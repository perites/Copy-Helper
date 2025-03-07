import dataclasses
import logging
import re
import traceback

from flask import g

from copy_helper_api import google_services, image_helper, styles_helper, domain, offer


@dataclasses.dataclass
class Copy:
    lift_file_content: str = ''
    sls: str = ''
    tracking_link: str = 'LINK_NOT_MAID'
    priority_info: dict[str:str] = dataclasses.field(
        default_factory=lambda: {'text': '', 'url': '', 'html_block': ''}
    )
    images: list[str] = dataclasses.field(
        default_factory=lambda: []
    )


@dataclasses.dataclass
class Results:
    str_copy: str
    is_raw_lift_file_found: bool = True
    is_raw_sl_file_found: bool = False
    is_priority_footer_found: bool = False
    is_antispammed: bool = False

    def __str__(self):
        return (f'{self.str_copy} results: copy file {self.to_str(self.is_raw_sl_file_found)} | '
                f'sl file {self.to_str(self.is_raw_sl_file_found)} | '
                f'pfooter {self.to_str(self.is_priority_footer_found)} | '
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
    def __init__(self, domain_info, str_copy):
        self.domain = domain.Domain(domain_info)

        default_style_settings = g.user_settings.default_style_settings
        user_domain_styles_settings = self.domain.settings.styles_settings
        self.styles_helper = styles_helper.StylesHelper({**default_style_settings, **user_domain_styles_settings})

        self.str_copy = str_copy.replace('/', '-')
        offer_name, self.lift_number, self.img_code = self.get_info_from_str_copy(self.str_copy)
        self.offer = offer.Offer.find(offer_name)

        self.copy = Copy()
        self.results = Results(self.str_copy)

    @CopyMakerHelpers.catch_errors
    def get_copy_files_content(self):
        """Saving Lift and SL files from GoogleDrive"""

        logging.info(f'Searching copy files for offer {self.offer.name} and lift {self.lift_number}')

        # lift_folder = google_services.GoogleDrive.get_folder_by_name(f'Lift {self.lift_number}',
        #                                                              self.offer.google_drive_folder_id)

        lift_folder = offer.OfferGoogleDriveHelper.get_lift_folder(self.offer.google_drive_folder_id,
                                                                   self.lift_number)

        if not lift_folder:
            logging.warning(
                f'Could not find folder Lift {self.lift_number} in offer {self.offer.name}. Please check if folder exist on google drive')
            lift_file, sl_file = None, None
        else:
            lift_file, sl_file = offer.OfferGoogleDriveHelper.get_copy_files(lift_folder['id'])

        if lift_file:
            self.copy.lift_file_content = google_services.GoogleDrive.get_file_content(lift_file)
        else:
            logging.warning(f'Lift file for {self.offer.name} was not found')

        if sl_file:
            sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)

            self.copy.sls = sl_file_content.split('\n')
        else:
            logging.warning(f'Sl file for {self.offer.name} was not found')

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

        self.copy.lift_file_content, self.copy.images = image_helper.ImageHelper.process_images(
            self.copy.lift_file_content,
            self.str_copy,
            self.styles_helper.image_block,
            self.img_code)

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

        self.get_copy_files_content()

        self.make_tracking_link()

        self.get_priority_info()

        if not self.copy.lift_file_content:
            return "sdmth"

        self.antispam_content()

        self.process_images()
        self.apply_styles()
        self.add_template()
        self.add_link_to_html()

        return self.results


class CopyMakerException(Exception):
    pass


class WrongPatterForCopy(CopyMakerException):
    def __init__(self, str_copy):
        message = f'Failed to find offer name, lift number and image code in {str_copy}'
        super().__init__(message)
