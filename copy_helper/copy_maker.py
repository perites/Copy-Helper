import dataclasses
import logging
import os
import re
import traceback

from . import google_services
from . import image_helper
from . import offer
from . import settings
from . import styles_helper


@dataclasses.dataclass
class Copy:
    lift_file_content: str = ''
    sl_file_content: str = ''
    tracking_link: str = 'LINK_NOT_MAID'
    priority_info: dict[str:str] = dataclasses.field(
        default_factory=lambda: {'text': '', 'url': '', 'html_block': ''}
    )


@dataclasses.dataclass
class Results:
    str_copy: str
    is_raw_lift_file_found: bool = True
    is_raw_sl_file_found: bool = False
    is_priority_footer_found: bool = False
    images_saved: int = 0
    is_image_block_added: bool = False
    is_antispammed: bool = False

    def __str__(self):
        return (f'{self.str_copy} results: copy file {self.to_str(self.is_raw_sl_file_found)} | '
                f'sl file {self.to_str(self.is_raw_sl_file_found)} | '
                f'pfooter {self.to_str(self.is_priority_footer_found)} | '
                f'images saved {self.images_saved} | '
                f'img block created {self.to_str(self.is_image_block_added)} | '
                f'antispammed {self.to_str(self.is_antispammed)}')

    def to_str(self, value):
        return '+' if value else '-'


class CopyMakerHelpers:

    @staticmethod
    def catch_errors(func):
        def inner(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                return result
            except Exception as e:
                logging.error(f'Error while {func.__doc__}. Details : {e}')
                logging.debug(traceback.format_exc())

        return inner

    @staticmethod
    def get_info_from_str_copy(str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            raise WrongPatterForCopy(str_copy)

        return match.group(1), match.group(2), match.group(3)


class CopyMaker(CopyMakerHelpers):
    def __init__(self, domain, str_copy, date):
        self.domain = domain
        self.date = date
        self.path_to_domain_results = self.set_result_directory()

        default_style_settings = settings.GeneralSettings.default_style_settings
        user_domain_styles_settings = self.domain.settings.styles_settings
        self.styles_helper = styles_helper.StylesHelper({**default_style_settings, **user_domain_styles_settings})

        self.str_copy = str_copy.replace('/', '-')
        offer_name, self.lift_number, self.img_code = self.get_info_from_str_copy(self.str_copy)
        self.offer = offer.Offer.find(offer_name)

        self.copy = Copy()
        self.results = Results(self.str_copy)

    def set_result_directory(self):
        match settings.GeneralSettings.result_directory_type:
            case 'Domain-Date':
                path_to_domain_results = settings.GeneralSettings.result_directory + f'{self.domain.name}/{self.date}/'

            case 'Date-Domain':
                path_to_domain_results = settings.GeneralSettings.result_directory + f'{self.date}/{self.domain.name}/'

            case _:
                logging.warning('Unknown type of ResultDirectoryType, setting default')
                path_to_domain_results = settings.GeneralSettings.result_directory + f'{self.date}/{self.domain.name}/'

        os.makedirs(path_to_domain_results, exist_ok=True)
        return path_to_domain_results

    @CopyMakerHelpers.catch_errors
    def get_copy_files_content(self):
        """Saving Lift and SL files from GoogleDrive"""

        logging.info(f'Searching copy files for offer {self.offer.name} and lift {self.lift_number}')

        lift_folder = google_services.GoogleDrive.get_folder_by_name(f'Lift {self.lift_number}',
                                                                     self.offer.google_drive_folder_id)
        if not lift_folder:
            logging.warning(
                f'Could not find folder Lift {self.lift_number} in offer {self.offer.name}. Please check if folder exist on google drive')
            lift_file, sl_file = None, None
        else:
            lift_file, sl_file = offer.OfferGoogleDriveHelper.get_copy_files(lift_folder)

        if lift_file:
            self.copy.lift_file_content = google_services.GoogleDrive.get_file_content(lift_file)
        else:
            logging.warning(f'Lift file for {self.offer.name} was not found')

        if sl_file:
            self.copy.sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
        else:
            logging.warning(f'Sl file for {self.offer.name} was not found')

    @CopyMakerHelpers.catch_errors
    def set_content_from_local(self):
        """"Searching for copy file locally"""

        domain_lift_file_path = f'{self.path_to_domain_results + self.str_copy}.html'
        logging.info(f'Trying to read {domain_lift_file_path}')
        try:
            with open(domain_lift_file_path, 'r', encoding='utf-8') as file:
                self.copy.lift_file_content = file.read()

        except FileNotFoundError:
            logging.warning('Copy file not found')

    def save_copy_files(self):
        self.save_lift_file()
        self.save_sl_file()

    @CopyMakerHelpers.catch_errors
    def save_lift_file(self):
        """Saving Lift file locally"""

        file_name = self.str_copy + ('-Priority' if self.offer.is_priority else '')
        path = self.path_to_domain_results + f'{file_name}.html'
        with open(path, 'w', encoding='utf-8') as file:
            file.write(self.copy.lift_file_content)
            logging.info(f'Successfully saved lift file for {self.str_copy}')

    @CopyMakerHelpers.catch_errors
    def save_sl_file(self):
        """Saving Sl file to Sls.txt"""

        path_to_sls_file = self.path_to_domain_results + f'SLs-{self.domain.name}-{self.date}.txt'

        try:
            with open(path_to_sls_file, 'r', encoding='utf-8') as file:
                sls_file_content = file.read()

                if self.str_copy in sls_file_content:
                    logging.info(f'Did not add sls for {self.str_copy} in SLs.txt file as already has them')
                    return

        except FileNotFoundError:
            pass

        if self.offer.is_priority:
            unsub_url_str = f'Unsub link:\n{self.copy.priority_info['url']}\n\n'
        else:
            unsub_url_str = ''

        copy_sls = (
                self.str_copy + ('-Priority' if self.offer.is_priority else '') + '\n\n' +

                f'Tracking link:\n{self.copy.tracking_link}\n\n' + unsub_url_str +

                'Sls:\n' +

                self.copy.sl_file_content +

                "\n----------------------------------------\n\n\n\n")

        with open(path_to_sls_file, 'a', encoding='utf-8') as file:
            file.write(copy_sls)
            logging.info(f'Successfully add sls for {self.str_copy} in SLs.txt')

    @CopyMakerHelpers.catch_errors
    def get_priority_info(self):
        """Searching priority text and url in GoogleSheets"""
        if self.offer.is_priority:
            footer_text, url = self.offer.get_priority_footer_values(self.domain.settings.priority_unsub_link_info)
            if footer_text:
                logging.info(f'Priority footer was found for {self.offer.name}')
            else:
                logging.debug(f'Priority footer not found for {self.offer.name}')
                return

            html_block = self.styles_helper.make_priority_footer_html(footer_text, url)

            self.copy.priority_info = {'text': footer_text, 'url': url, 'html_block': html_block}

            if self.copy.priority_info['html_block']:
                self.results.is_priority_footer_found = True

    @CopyMakerHelpers.catch_errors
    def make_tracking_link(self):
        """Making tracking link"""

        tracking_link = self.domain.make_tracking_link(self.offer, self.str_copy, self.lift_number, self.img_code)
        self.copy.tracking_link = tracking_link

    @CopyMakerHelpers.catch_errors
    def antispam_content(self):
        """Antispamming lift, sl and priority footer"""
        if self.domain.settings.antispam:
            self.copy.lift_file_content = self.styles_helper.antispam_text(self.copy.lift_file_content)
            self.copy.sl_file_content = self.styles_helper.antispam_text(self.copy.sl_file_content)

            if self.copy.priority_info['html_block']:
                self.copy.priority_info['html_block'] = self.styles_helper.antispam_text(
                    self.copy.priority_info['html_block'])

            self.results.is_antispammed = True

    @CopyMakerHelpers.catch_errors
    def process_images(self):
        """Processing Images"""

        self.copy.lift_file_content, imgs_info = image_helper.ImageHelper.process_images(self.copy.lift_file_content,
                                                                                         self.str_copy,
                                                                                         self.styles_helper.image_block,
                                                                                         self.img_code, self.date)

        if imgs_info == -1:
            pass
        elif imgs_info == 0:
            self.results.is_image_block_added = True
        else:
            self.results.images_saved = imgs_info

    @CopyMakerHelpers.catch_errors
    def apply_styles(self):
        """Applying styles"""

        self.copy.lift_file_content = self.styles_helper.apply_styles(self.copy.lift_file_content)

    @CopyMakerHelpers.catch_errors
    def add_template(self):
        """Adding template"""
        self.copy.lift_file_content = self.domain.add_template(self.copy.lift_file_content,
                                                               self.copy.priority_info['html_block'],
                                                               self.styles_helper.add_after_priority_block)

    @CopyMakerHelpers.catch_errors
    def add_link_to_html(self):
        """Replacing urlhere with real tracking link"""
        self.copy.lift_file_content = self.copy.lift_file_content.replace('urlhere', self.copy.tracking_link)

    def make_copy(self, set_content_from_local=False):
        if not set_content_from_local:
            self.get_copy_files_content()
        else:
            self.set_content_from_local()

        if self.copy.lift_file_content:
            self.results.is_raw_lift_file_found = True
        if self.copy.sl_file_content:
            self.results.is_raw_sl_file_found = True

        self.make_tracking_link()

        self.get_priority_info()

        if not self.copy.lift_file_content:
            self.save_copy_files()
            return self.results

        self.antispam_content()

        self.process_images()
        self.apply_styles()
        self.add_template()
        self.add_link_to_html()

        self.save_copy_files()

        return self.results


class CopyMakerException(Exception):
    pass


class WrongPatterForCopy(CopyMakerException):
    def __init__(self, str_copy):
        message = f'Failed to find offer name, lift number and image code in {str_copy}'
        super().__init__(message)
