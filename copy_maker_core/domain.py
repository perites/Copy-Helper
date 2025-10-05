import logging
import traceback

from openpyxl.utils import get_column_letter

from . import google_services
from .copy import Copy

logger = logging.getLogger(__name__)


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
            logger.warning(f'Could not find domain {self.broadcast['name']} in Broadcast')
            return

        date_index = google_services.GoogleSheets.get_table_index_of_value(self.broadcast['id'], date,
                                                                           f'{self.broadcast['page']}!A:A', False)

        if not date_index:
            logger.warning(f'Could not find date {date} in Broadcast')
            return

        date_row = date_index + 1
        copies_range = f'{self.broadcast['page']}!{get_column_letter(domain_index + 1)}{date_row}'
        copies_for_domain = google_services.GoogleSheets.get_data_from_range(self.broadcast['id'], copies_range)
        if not copies_for_domain:
            logger.info(f'Could not find copies in range {copies_range} in Broadcast')
            return

        copies_str = copies_for_domain[0][0].strip().split(' ')
        copies_str = list(map(lambda copy: copy.replace('(P)', ''), copies_str))
        copies_str = list(map(lambda copy: copy.replace('(L)', ''), copies_str))

        return copies_str

    def make_copy(self, str_copy, manual_lift_html):
        try:
            copy = Copy.match_str_copy(str_copy)
            copy.find(self.products, manual_lift_html)
            copy.change_html(self.styles)
            return copy

        except Exception as e:
            logger.error(f'Error while making copy {str_copy}. Details : {e}')
            logger.debug(traceback.format_exc())


class DomainException(Exception):
    pass


class StatusNotAllowed(DomainException):
    def __init__(self, offer_name, offer_status):
        message = f'{offer_name} have status {offer_status}. Not allowed to send'
        super().__init__(offer_name, message)
