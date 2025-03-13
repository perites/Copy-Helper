import dataclasses
import logging

from . import exceptions
from . import google_services
from .decorators import google_sheets_required


@dataclasses.dataclass
class DomainSettings:
    page: str
    tracking_link_info: dict
    priority_unsub_link_info: dict
    styles_settings: dict
    antispam: bool
    template: str

    @classmethod
    def create_from_dict(cls, domain_info):
        return cls(
            page=domain_info['pageInBroadcast'],
            tracking_link_info=domain_info['trackingLinkInfo'],
            priority_unsub_link_info=domain_info['customPriorityUnsubLinkInfo'],
            styles_settings=domain_info['stylesSettings'],
            antispam=domain_info['antiSpam'],
            template=domain_info['template']

        )


# class DomainGoogleSheetsHelper:
#     @classmethod
#     def get_copies(cls, name, broadcast_id, page, date):
#
#         domain_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, name, f'{page}!1:1')
#
#         if not domain_index:
#             logging.warning(f'Could not find domain {name} in Broadcast')
#             return
#
#         date_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, broadcast_date, f'{page}!A:A',
#                                                                            False)
#         if not date_index:
#             logging.warning(f'Could not find date {broadcast_date} in Broadcast')
#             return
#
#         date_row = date_index + 1
#         copies_range = f'{page}!{date_row}:{date_row}'
#         copies_for_date = google_services.GoogleSheets.get_data_from_range(broadcast_id, copies_range)
#         copies_for_domain = copies_for_date[0][domain_index]
#         if not copies_for_domain:
#             logging.warning(f'Could not find copies in range {copies_range} in Broadcast')
#             return
#
#         return copies_for_domain.strip().split(' ')


class Domain:
    def __init__(self, domain_info):
        self.name = domain_info['name']
        self.settings = DomainSettings.create_from_dict(domain_info)

    # def get_file_data(self, file_name):
    #     path_to_domain_settings_directory = paths.PATH_TO_FOLDER_DOMAINS_SETTINGS + self.name
    #     match file_name:
    #         case 'settings':
    #             return tools.read_json_file(f'{path_to_domain_settings_directory}/settings.json')
    #
    #         case 'template':
    #             with open(f'{path_to_domain_settings_directory}/template.html', 'r', encoding='utf-8') as file:
    #                 return file.read()

    @classmethod
    @google_sheets_required
    def get_copies(cls, name, broadcast_id, broadcast_page, date):

        domain_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, name,
                                                                             f'{broadcast_page}!1:1')

        if not domain_index:
            raise exceptions.DomainNotFound(name)

        date_index = google_services.GoogleSheets.get_table_index_of_value(broadcast_id, date, f'{broadcast_page}!A:A',
                                                                           False)
        if not date_index:
            raise exceptions.DateNotFound(date)

        date_row = date_index + 1
        copies_range = f'{broadcast_page}!{date_row}:{date_row}'
        copies_for_date = google_services.GoogleSheets.get_data_from_range(broadcast_id, copies_range)
        copies_for_domain = copies_for_date[0][domain_index]
        if not copies_for_domain:
            raise exceptions.CopyNotFound(copies_range)

        return copies_for_domain.strip().split(' ')

    def add_template(self, html_copy, priority_block, add_after_priority_block):
        template = self.settings.template

        if not template:
            return html_copy + "<br><br><br><br><br>" + priority_block

        template = template.replace('<<<-COPY_HERE->>>', html_copy)

        template = template.replace('<<<-PRIORITY_FOOTER_HERE->>>',
                                    priority_block + (add_after_priority_block if priority_block else ""))

        return template

    def make_tracking_link(self, offer, str_copy, lift_number, img_code):
        logging.debug(f'Making tracking link for domain {self.name} copy {str_copy}')
        tracking_link_info = self.settings.tracking_link_info

        match tracking_link_info['type']:
            case "RT TM":
                tracking_link = tracking_link_info['start'] + offer.tracking_id('rt_tm') + \
                                tracking_link_info[
                                    'end'] + str_copy

            case 'VolumeGreen':
                tracking_link = tracking_link_info['start'] + offer.tracking_id('volume_green') + \
                                tracking_link_info[
                                    'end'] + f'{offer.tracking_id("img_it")}_{lift_number}{img_code}'

            case 'CM TM':
                tracking_link = tracking_link_info['start'] + offer.tracking_id('cm_tm') + \
                                tracking_link_info[
                                    'end'] + f'{offer.tracking_id("cm_tm")}_{lift_number}{img_code}'
            case _:
                logging.warning(f"Got unsupported link type {tracking_link_info['type']}")
                tracking_link = tracking_link_info['Start'] + "UNSUPPORTED_TYPE" + tracking_link_info[
                    'End'] + "UNSUPPORTED_TYPE"

        return tracking_link
