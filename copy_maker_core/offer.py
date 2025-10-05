import json
import logging
import os
import time

import requests

from . import google_services

MAX_CACHE_DURATION_SECONDS = 60 * 60 * 6
PATH_TO_OFFERS_CACHE_FILE = 'copy_maker_core/offers_info_cache.json'
if not os.path.exists(PATH_TO_OFFERS_CACHE_FILE):
    open('copy_maker_core/offers_info_cache.json', 'w').write('{}')

logger = logging.getLogger(__name__)


class OffersCache:
    @classmethod
    def get_offer(cls, offer_name):
        raise NotImplemented

    @classmethod
    def update_offer(cls, offer_name, new_data):
        raise NotImplemented


class OffersCacheJSON(OffersCache):
    offers_cache = {}

    @classmethod
    def _get_offers_cache(cls):
        if not cls.offers_cache:
            cls.offers_cache = cls._read_cache_file()
        return cls.offers_cache

    @classmethod
    def get_offer(cls, offer_name):
        return cls._get_offers_cache().get(offer_name)

    @classmethod
    def update_offer(cls, offer_name, new_data):
        cls.offers_cache[offer_name] = new_data
        cls._update_cache_file()

    @staticmethod
    def _read_cache_file():
        logger.debug(f'Reading json file {PATH_TO_OFFERS_CACHE_FILE}')
        with open(PATH_TO_OFFERS_CACHE_FILE, 'r', encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def _update_cache_file(cls):
        logger.debug(f'Updating {PATH_TO_OFFERS_CACHE_FILE}')
        with open(PATH_TO_OFFERS_CACHE_FILE, 'w') as file:
            json.dump(cls.offers_cache, file, indent=4)


class Offer:
    cache = OffersCacheJSON()

    def __init__(self, name):
        self.name = name
        self.monday_fields = {}
        self.priority_info = {}

    def find_offer_data(self, monday_info, priority_table_info):
        if not self.find_cached_data():
            self.get_fresh_data(monday_info)

        self.priority_info = self.get_priority_footer_values(priority_table_info["tableID"],
                                                             priority_table_info["pages"],
                                                             priority_table_info["text_column"],
                                                             priority_table_info["link_column"],
                                                             priority_table_info["id_column"]
                                                             )

    def find_cached_data(self):
        offer_cache = self.cache.get_offer(self.name)
        if offer_cache and (offer_cache['creation_timestamp'] + MAX_CACHE_DURATION_SECONDS > time.time()):
            logger.debug(f'Found valid cache for {self.name}')
            self.monday_fields = offer_cache['monday_fields']
            return True

        logger.debug(f'Offer {self.name} was not found in cache')
        return False

    def get_fresh_data(self, monday_info):
        logger.debug(f'Getting fresh data for offer {self.name}')
        raw_monday_columns = self._get_raw_monday_colums(monday_info['mondayId'], monday_info['monday_token'])
        monday_fields = self._process_raw_monday_colums(raw_monday_columns, monday_info['partners_folder_id'])
        self.monday_fields = monday_fields

        self.cache.update_offer(self.name, {'monday_fields': monday_fields})

    def _get_raw_monday_colums(self, board_id, monday_token):
        logger.info(f'Getting raw fields for {self.name} from monday')

        WRONG_OFFERS = {
            "AHMS": 8753642885,
            "AHTT": 8753520275,
            "CONO": 7101745053,
            "AHTG": 8721191855,
            "BIGG": 7654340357
        }

        item_id = WRONG_OFFERS.get(self.name)

        if item_id:
            query = '''
                    query ($value: ID!) {
                      items(ids: [$value]) {
                        id
                        name
                        column_values {
                          id
                          value
                          type
                          text
                          column {
                            title
                          }
                        }
                      }
                    }
                    '''

            variables = {
                "value": item_id,
            }
        else:
            query = """
                query ($boardId: ID!, $value: CompareValue!) {
                  boards(ids: [$boardId]) {
                    items_page(query_params: {rules: [{column_id: "name", compare_value: $value, operator: contains_text}]}) {
                      items {
                        id
                        name
                        column_values {
                          id
                          text
                          column {
                            title
                          }
                        }
                      }
                    }
                  }
                }
                """

            variables = {
                "boardId": board_id,
                "value": self.name,
            }

        headers = {
            "Authorization": f"Bearer {monday_token}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            'https://api.monday.com/v2',
            json={"query": query, "variables": variables},
            headers=headers
        )

        raw_response_dict = response.json()
        raw_columns = raw_response_dict['data']['items'][0]['column_values'] if item_id else \
            raw_response_dict['data']['boards'][0]['items_page']['items'][0]['column_values']

        return raw_columns

    def _process_raw_monday_colums(self, raw_monday_columns, partners_folder_id):
        logger.debug(f'Processing raw monday fields for {self.name}')
        if not raw_monday_columns:
            raise OfferNotFound(self.name)

        monday_fields = {column['column']['title']: column['text'] for column in raw_monday_columns}
        monday_fields['name'] = self.name
        monday_fields['is_priority'] = True
        monday_fields['creation_timestamp'] = time.time()

        monday_fields['copy_location_folder_id'] = self.find_valid_offer_folder_id(monday_fields.get('Copy Location'),
                                                                                   partners_folder_id)

        return monday_fields

    def find_valid_offer_folder_id(self, untrusted_offer_folder_url, partners_folder_id):
        if not untrusted_offer_folder_url:
            logger.warning(f'Google drive offer folder url was not found in Monday, starting manual search')
            return self.find_offer_folder_id_manually(partners_folder_id)

        untrusted_google_drive_folder_id = untrusted_offer_folder_url.split('/folders/')[1]
        if google_services.GoogleDrive.get_folder_by_name('Lift', untrusted_google_drive_folder_id, False):
            return untrusted_google_drive_folder_id

        logger.debug(
            f'Something wrong with Copy Location url of offer {self.name}, no lift folder was found in given folder')

        maybe_google_drive_folder_id = google_services.GoogleDrive.get_folder_by_name('HTML+SL',
                                                                                      untrusted_google_drive_folder_id,
                                                                                      strict=False)
        if maybe_google_drive_folder_id:
            return maybe_google_drive_folder_id['id']

        logger.warning(f'Google drive offer folder url was incorrect in Monday, starting manual search')
        return self.find_offer_folder_id_manually(partners_folder_id)

    def find_offer_folder_id_manually(self, partners_folder_id):
        offer_general_folder = self.get_offer_general_folder(partners_folder_id)

        offer_folder = google_services.GoogleDrive.get_folder_by_name('HTML+SL', offer_general_folder['id'],
                                                                      strict=False)
        offer_folder_id = offer_folder.get('id')
        if not offer_folder_id:
            logger.error(
                f'Folder "HTML+SL" was not found for offer {self.name}. Folder id where searching: {offer_general_folder}')
            raise OfferNotFound(self.name)

        return offer_folder_id

    def get_offer_general_folder(self, partners_folder_id):
        for partner_folder in google_services.GoogleDrive.get_folders_of_folder(partners_folder_id):

            partner_folder_id = partner_folder['id']
            offer_general_folder = google_services.GoogleDrive.get_folder_by_name(self.name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        logger.error(f'No Partners with offer {self.name} was found in GoogleDrive')
        raise OfferNotFound(self.name)

    def get_priority_footer_values(self, tableID, pages, text_column, link_column, id_column):
        if not self.monday_fields['is_priority']:
            return {
                'is_priority': False,
                'unsub_text': '',
                'unsub_link': '',
                'unsub_id': ''
            }

        logger.debug(f'Searching for footer for offer {self.name}')

        priority_product_index, priority_product_page = None, None

        for page in pages:
            index = google_services.GoogleSheets.get_table_index_of_value(tableID, self.name,
                                                                          f'{page}!A:A', is_row=False,
                                                                          strict=False)

            if index:
                priority_product_index, priority_product_page = index, page
                break

        if not priority_product_index:
            self.monday_fields['is_priority'] = False
            self.cache.update_offer(self.name, self.monday_fields)
            return {
                'is_priority': False,
                'unsub_text': '',
                'unsub_link': '',
                'unsub_id': ''
            }

        priority_product_index += 1

        text_value = google_services.GoogleSheets.get_data_from_range(
            tableID, f'{priority_product_page}!{text_column}{priority_product_index}')[0][0]

        if text_value:
            logger.info(f'Priority footer was found for {self.name}')
        else:
            logger.debug(f'Priority footer not found for {self.name}')

        unsub_url = google_services.GoogleSheets.get_data_from_range(
            tableID, f'{priority_product_page}!{link_column}{priority_product_index}')

        if not unsub_url:
            logger.warning('Unsub url not found')
        else:
            unsub_url = unsub_url[0][0]

        unsub_id = None
        if id_column:
            unsub_id = google_services.GoogleSheets.get_data_from_range(
                tableID, f'{priority_product_page}!{id_column}{priority_product_index}')

            if not unsub_id:
                logger.warning('Unsub ID not found')
            else:
                unsub_id = unsub_id[0][0]

        return {
            'is_priority': True,
            'unsub_text': text_value,
            'unsub_link': unsub_url,
            'unsub_id': unsub_id
        }


class OfferNotFound(Exception):
    def __init__(self, offer_name):
        message = f'Could not find data about {offer_name}'
        super().__init__(offer_name, message)


class StatusNotAllowed(Exception):
    def __init__(self, offer_name, offer_status):
        message = f'{offer_name} have status {offer_status}. Not allowed to send on this domain'
        super().__init__(offer_name, message)
