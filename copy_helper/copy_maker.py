import logging
import os
import re

from . import google_services
from . import offer
from . import settings


class Copy:
    lift_file_content: str = ''
    sl_file_content: str = ''
    tracking_link: str = 'LINK_NOT_MAID'
    priority_info: dict[str:str] = {'text': None, 'url': None, }


class CopyMaker:
    def __init__(self, domain, str_copy, date):
        self.domain = domain
        self.str_copy = str_copy
        try:
            self.offer, self.lift_number, self.img_code = self.get_info_from_str_copy(str_copy)
        except Exception:
            logging.exception(f'Error while extracting info from {str_copy}')
            return

        self.date = date

        self.path_to_domain_results = self.set_result_directory()
        self.copy = Copy()

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

    @staticmethod
    def get_info_from_str_copy(str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            raise Exception(f'Failed to find offer name, lift number and image code in {str_copy}')

        return offer.Offer.find(match.group(1)), match.group(2), match.group(3)

    def get_copy_files_content(self):
        try:
            logging.info(f'Searching copy files for offer {self.offer.name} and lift {self.lift_number}')

            lift_folder = google_services.GoogleDrive.get_folder_by_name(f'Lift {self.lift_number}',
                                                                         self.offer.google_drive_folder_id)
            if not lift_folder:
                logging.warning(
                    f'Could not find folder Lift {self.lift_number} in offer {self.offer.name}. Please check if folder exist on google drive')
                return '', ''

            lift_file, sl_file = self.offer.get_copy_files(lift_folder)

            if lift_file:
                lift_file_content = google_services.GoogleDrive.get_file_content(lift_file)
            else:
                logging.warning(f'Lift file for {self.offer.name} was not found')
                lift_file_content = ''

            if sl_file:
                sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
            else:
                logging.warning(f'Sl file for {self.offer.name} was not found')
                sl_file_content = ''

            return lift_file_content, sl_file_content

        except Exception:
            logging.exception(f'Error while receiving copy files (lift or sl) for offer {self.offer.name}')
            return '', ''

    def get_copy_files(self):
        self.copy.lift_file_content, self.copy.sl_file_content = self.get_copy_files_content()

    def set_content_from_local(self):
        domain_lift_file_path = f'{self.path_to_domain_results + self.str_copy}.html'
        logging.info(f'Trying to read {domain_lift_file_path}')
        try:
            with open(domain_lift_file_path, 'r', encoding='utf-8') as file:
                self.copy.lift_file_content = file.read()

        except FileNotFoundError:
            logging.warning('Copy file not found')
            self.copy.lift_file_content = ''

    def save_copy_files(self):
        self.save_lift_file()
        self.save_sl_file()

    def save_lift_file(self):
        try:
            file_name = self.str_copy + ('-Priority' if self.offer.is_priority else '')
            path = self.path_to_domain_results + f'{file_name}.html'
            with open(path, 'w', encoding='utf-8') as file:
                file.write(self.copy.lift_file_content)
                logging.info(f'Successfully saved lift file for {self.str_copy}')

        except Exception:
            logging.exception(f'Error while saving lift file for {self.str_copy}')

    def save_sl_file(self):
        try:
            path_to_sls_file = self.path_to_domain_results + f'SLs-{self.domain.name}-{self.date}.txt'

            try:
                with open(path_to_sls_file, 'r', encoding='utf-8') as file:
                    sls_file_content = file.read()

                    if self.str_copy in sls_file_content:
                        logging.info(f'Did not add sls for {self.str_copy} in SLs.txt file as it already have them')
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

        except Exception:
            logging.exception(f'Error while adding sls for {self.str_copy} in SLs.txt')

    def make_copy(self, set_content_from_local=False):
        if not set_content_from_local:
            self.get_copy_files()
        else:
            self.set_content_from_local()

        self.save_copy_files()
