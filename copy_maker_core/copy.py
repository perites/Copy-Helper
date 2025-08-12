import logging
import re

import secrets
from . import google_services
from .crypto_all_products_types import crypto_all_products_types
from .offer import Offer, StatusNotAllowed
from .styles_helper import StylesHelper

logger = logging.getLogger(__name__)


class Copy:
    def __init__(self, offer_name, lift_number, img_code):
        self.offer = Offer(offer_name)
        self.lift_number = lift_number
        self.img_code = img_code
        self.str_rep = offer_name + lift_number + img_code

        self.tracking_link = ''
        self.lift_html = ''
        self.html_found = False
        self.lift_sls = ''
        self.lift_images = []

    @classmethod
    def match_str_copy(cls, str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            raise WrongPatterForCopy(str_copy)

        return cls(match.group(1), match.group(2), match.group(3))

    def result(self):
        return {
            'str_rep': self.str_rep,
            'html_r': self.html_found,
            'sl_r': bool(self.lift_sls),
            'pfooter_r': bool(self.offer.priority_info['unsub_text']),
            'link_r': bool('UNKNOWN_TYPE' not in self.tracking_link)
        }

    def find(self, products_info):
        monday_info = {'mondayId': products_info['mondayId'], 'monday_token': secrets.MONDAY_TOKEN,
                       'partners_folder_id': products_info['partnersFolderId']}

        self.offer.find_offer_data(monday_info, products_info['priority'])

        if self.offer.monday_fields['Status'] not in products_info['allowedStatuses']:
            raise StatusNotAllowed(self.offer.name, self.offer.monday_fields['Status'])

        self.make_tracking_link(products_info['trackingLink'])
        self.make_custom_unsub_link(products_info['priority']['unsubLinkTemplate'])
        self.get_files_content()
        self.lift_html = self.lift_html.replace('urlhere', self.tracking_link)

    def change_html(self, domain_styles):
        styles_helper = StylesHelper(self.lift_html, self.lift_sls, domain_styles)

        self.lift_images = styles_helper.process_images(self.img_code, self.str_rep)

        styles_helper.antispam_copy()
        styles_helper.apply_styles()
        styles_helper.add_template(self.offer.priority_info)

        self.lift_html = styles_helper.lift_html
        self.lift_sls = styles_helper.lift_sls

    def get_files_content(self):
        logger.info(f'Searching copy files for offer {self.offer.name} lift {self.lift_number}')

        lift_file, sl_file = self.get_copy_files()

        if lift_file:
            lift_file_content = google_services.GoogleDrive.get_file_content(lift_file)
            self.html_found = True
        else:
            logger.warning(f'Lift file for {self.offer.name} lift {self.lift_number} was not found')
            lift_file_content = ''

        if sl_file:
            sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
        else:
            logger.warning(f'Sl file for {self.offer.name} lift {self.lift_number} was not found')
            sl_file_content = ''

        self.lift_html = lift_file_content
        self.lift_sls = sl_file_content

    def get_copy_files(self):
        lift_folder = google_services.GoogleDrive.get_folder_by_name(f'Lift {self.lift_number}',
                                                                     self.offer.monday_fields[
                                                                         'copy_location_folder_id'])

        if not lift_folder:
            raise LiftFolderNotFound(self.lift_number, self.offer.name)

        lift_folder_files = google_services.GoogleDrive.get_files_from_folder(lift_folder['id'])

        lift_file = None
        mjml_found = False

        sl_file = None

        for file in lift_folder_files:
            if not mjml_found:
                if (file['name'].lower().endswith('.html')) and ('mjml' in file['name'].lower()) and (
                        'SL' not in file['name']):
                    lift_file = file
                    mjml_found = True
                    logger.debug(f"Found copy file (mjml): {lift_file['name']}")

                elif (not lift_file) and (file['name'].lower().endswith('.html')) and ('SL' not in file['name']):
                    lift_file = file

            if not sl_file:
                if 'sl' in file['name'].lower():
                    sl_file = file
                    logger.debug(f"Found SL file: {sl_file['name']}")

            if mjml_found and sl_file:
                break

        return lift_file, sl_file

    def make_tracking_link(self, tracking_link_info):
        tracking_id = self.offer.monday_fields.get(tracking_link_info['type'])
        if not tracking_id:
            logger.warning('Unknown Tracking Type. Ensure it is the same as in Monday.')
            tracking_id = 'UNKNOWN_TYPE'

        match tracking_link_info['endType']:
            case 'IMG-IT':
                link_end = self.offer.monday_fields['IMG-IT'] + '_' + self.lift_number + self.img_code
            case 'IMG-IT-NUM':
                link_end = self.offer.monday_fields['IMG-IT'][3:] + '_' + self.lift_number + self.img_code
            case _:
                link_end = self.str_rep

        link_body = tracking_link_info['template']
        tracking_link = link_body.replace('[TRACKING_ID]', tracking_id)

        send_type = self.get_send_type()
        tracking_link = tracking_link.replace('[SEND_TYPE]', send_type)

        tracking_link = tracking_link.replace('[END]', link_end)

        self.tracking_link = tracking_link

    def get_send_type(self):
        if not self.offer.name.startswith('CO'):
            logger.debug('Using regular send type')
            return 'B'

        crypto_product_types = crypto_all_products_types.get(self.offer.name)

        if not crypto_product_types:
            logger.warning(f'{self.offer.name} does not have according type, using regular type "B"')
            return 'B'

        return str(crypto_product_types.get(int(self.lift_number), 'DeadEmail'))

    def make_custom_unsub_link(self, unsub_link_template):
        if not self.offer.priority_info['unsub_id']:
            return

        custom_unsub_link = unsub_link_template.replace('[UNSUB_ID]', self.offer.priority_info['unsub_id'])
        self.offer.priority_info['unsub_link'] = custom_unsub_link


class WrongPatterForCopy(Exception):
    def __init__(self, str_copy):
        message = f'Failed to find offer name, lift number and image code in {str_copy}'
        super().__init__(message)


class LiftFolderNotFound(Exception):
    def __init__(self, lift_number, offer_name):
        message = f'Lift {lift_number} for offer {offer_name} not found. Please check if lift exists on google drive'
        super().__init__(message)
