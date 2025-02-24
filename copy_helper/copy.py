import dataclasses
from . import offer

import re

import logging
from . import google_services


@dataclasses.dataclass
class Copy:
    offer: offer.Offer
    lift_number: str
    img_code: str

    @classmethod
    def create(cls, str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            logging.debug(f'Failed to find offer name, lift_number and img_code in {str_copy}')
            return None
        try:
            offer_obj = offer.Offer.find(match.group(1))
        except Exception:
            logging.exception(f'Error while creating offer {match.group(1)}')
            return None

        return cls(offer_obj, match.group(2), match.group(3))

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
            logging.exception(f'Error while receiving copy files (lift or sl) for offer {self.name}')
            return '', ''

    def __str__(self):
        return self.offer.name + self.lift_number + self.img_code
