from . import domain

import logging
from . import paths
import re
from . import offer
from . import google_services


class Copy:
    lift_file_content: str = ''
    sl_file_content: str = ''


class CopyMaker:
    def __init__(self, domain, str_copy, bc_date):
        self.domain = domain
        self.str_copy = str_copy
        try:
            self.offer, self.lift_number, self.img_code = self.get_info_from_str_copy(str_copy)
        except Exception:
            logging.exception(f'Error while extracting info from {str_copy}')
            return

        self.date = bc_date.replace('/', '.')

        self.copy = Copy()

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

            lift_folder = self.offer.get_folder_by_name(f'Lift {self.lift_number}', self.offer.google_drive_folder_id)
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
