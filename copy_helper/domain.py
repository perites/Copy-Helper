import dataclasses
import logging
import re

from . import google_services
from . import secrets
from .offer import Offer


@dataclasses.dataclass
class Copy:
    offer_name: str
    lift_number: str
    img_code: str
    str_rep: str

    tracking_link = ''

    offer_monday_fields = {}
    priority_info = {}
    lift_html = ''
    html_found = False
    lift_sls = ''
    lift_images = []


class Domain:
    def __init__(self, settings_dict):
        self.broadcast = settings_dict['broadcast']
        self.products = settings_dict['products']
        self.styles = settings_dict['styles']

    def get_copies_from_broadcast(self, date):

        domain_index = google_services.GoogleSheets.get_table_index_of_value(self.broadcast['id'],
                                                                             self.broadcast['name'],
                                                                             f'{self.broadcast['page']}!1:1')

        if not domain_index:
            logging.warning(f'Could not find domain {self.broadcast['name']} in Broadcast')
            return

        date_index = google_services.GoogleSheets.get_table_index_of_value(self.broadcast['id'], date,
                                                                           f'{self.broadcast['page']}!A:A', False)

        if not domain_index:
            logging.warning(f'Could not find date {date} in Broadcast')
            return

        date_row = date_index + 1
        copies_range = f'{self.broadcast['page']}!{date_row}:{date_row}'
        copies_for_date = google_services.GoogleSheets.get_data_from_range(self.broadcast['id'], copies_range)
        copies_for_domain = copies_for_date[0][domain_index]
        if not copies_for_domain:
            logging.warning(f'Could not find copies in range {copies_range} in Broadcast')
            return

        return copies_for_domain.strip().split(' ')

    @staticmethod
    def create_copy(str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if not match:
            raise WrongPatterForCopy(str_copy)

        return Copy(match.group(1), match.group(2), match.group(3), str_copy)

    def find_copy(self, copy):
        offer = Offer(copy.offer_name, self.products['mondayId'], self.products['partnersFolderId'],
                      secrets.MONDAY_TOKEN)

        if offer.fields['Status'] not in self.products['allowedStatuses']:
            raise StatusNotAllowed(copy.offer_name, offer.fields['Status'])

        offer_priority_info = offer.get_priority_footer_values(self.products['priority']['tableID'],
                                                               self.products['priority']['pages'],
                                                               self.products['priority']['textColumn'],
                                                               self.products['priority']['linkColumn'],
                                                               self.products['priority']['idColumn'])

        lift_html, lift_sls = offer.get_copy_files_content(copy.lift_number)

        copy.offer_monday_fields = offer.fields
        copy.priority_info = offer_priority_info
        copy.lift_html = lift_html
        if copy.lift_html:
            copy.html_found = True
        copy.lift_sls = lift_sls

        return copy

    def make_tracking_link(self, copy):
        tracking_id = copy.offer_monday_fields.get(self.products['trackingLink']['type'])
        if not tracking_id:
            logging.warning('Unknown Tracking Type. Ensure it is same as in Monday.')
            tracking_id = 'UNKNOWN_TYPE'

        match self.products['trackingLink']['endType']:
            case 'IMG-IT':
                link_end = copy.offer_monday_fields['IMG-IT'] + copy.lift_number + copy.img_code
            case 'IMG-IT-NUM':
                link_end = copy.offer_monday_fields['IMG-IT'][3:] + copy.lift_number + copy.img_code
            case _:
                link_end = copy.str_rep

        link_body = self.products['trackingLink']['template']
        tracking_link = link_body.replace('[TRACKING_ID]', tracking_id)
        tracking_link = tracking_link.replace('[END]', link_end)

        copy.tracking_link = tracking_link

        return copy

    def make_unsub_link(self, copy):
        if not copy.priority_info['unsub_id']:
            return copy

        link_template = self.products['priority']['unsubLinkTemplate']
        unsub_link = link_template.replace('[UNSUB_ID]', copy.priority_info['unsub_id'])
        copy.priority_info['unsub_link'] = unsub_link

        return copy

    def process_images(self, copy):
        src_part_pattern = r'src="[^"]*'
        images_urls = []
        src_list = re.findall(src_part_pattern, copy.lift_html)
        if len(src_list) == 0:
            if copy.img_code:
                logging.info('Copy has img code and doesnt contain images')
                logging.debug(f'Adding image block to copy {copy.str_rep}')
                copy.lift_html = copy.lift_html.replace('<br><br>',
                                                        f'<!-- image-block-start -->{self.styles['imageBlock']}<!-- image-block-end -->',
                                                        1)

                return copy

            else:
                logging.debug('No images no image code, doing nothing')
                return copy

        logging.info(f'Found {len(src_list)} images')
        for index, src_part in enumerate(src_list):
            img_url = src_part.split('"')[1]
            if img_url not in images_urls:
                images_urls.append(img_url)

        copy.lift_images = images_urls
        return copy


class DomainException(Exception):
    pass


class StatusNotAllowed(DomainException):
    def __init__(self, offer_name, offer_status):
        message = f'{offer_name} have status {offer_status}. Not allowed to send'
        super().__init__(offer_name, message)


class WrongPatterForCopy(DomainException):
    def __init__(self, str_copy):
        message = f'Failed to find offer name, lift number and image code in {str_copy}'
        super().__init__(message)
