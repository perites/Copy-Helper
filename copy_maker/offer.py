import json
import logging
import time

import requests

from . import google_services

MAX_CACHE_DURATION_SECONDS = 60 * 60 * 6
PATH_TO_FILE_OFFERS_CACHE = 'copy_maker/offers_info_cache.json'

logger = logging.getLogger(__name__)


class OffersCache:

    @classmethod
    def get_cache(cls):
        logger.debug('Getting all offers info cache')
        offers_info_cache = cls.read_json_file(PATH_TO_FILE_OFFERS_CACHE)

        return offers_info_cache

    @classmethod
    def set_cache(cls, new_offers_info_cache):
        logger.debug('Setting new offers info cache')
        cls.write_json_file(PATH_TO_FILE_OFFERS_CACHE, new_offers_info_cache)

    @classmethod
    def set_offer_cache(cls, offer_info):

        offers_info_cache = cls.get_cache()
        offers_info_cache[offer_info['name']] = offer_info

        cls.set_cache(offers_info_cache)

        return offer_info

    @classmethod
    def clear_cache(cls, option):
        match option:
            case 'all':
                cls.set_cache({})
                logger.info('All cache successfully cleared')
            case _:
                all_cache = cls.get_cache()
                if not all_cache.get(option):
                    logger.warning(f'Can`t clear cache of {option} as it is NOT found in cache')
                    return

                del all_cache[option]
                cls.set_cache(all_cache)
                logger.info(f'Cache for offer {option} cleared')

    @staticmethod
    def read_json_file(path):
        logger.debug(f'Reading json file {path}')
        with open(path, 'r', encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def write_json_file(path, data):
        logger.debug(f'Writing to {path}')
        with open(path, 'w') as file:
            json.dump(data, file, indent=4)


# class OffersCache:
#     DATABASE_CREDENTIALS = json.load(open('../SystemData/secrets.json'))['DATABASE_CREDENTIALS']
#     redis_db = redis.Redis(host=DATABASE_CREDENTIALS['host'],
#                            password=DATABASE_CREDENTIALS['password'], port=DATABASE_CREDENTIALS['port'],
#                            ssl=True)
#
#     @classmethod
#     def get_cached_offer(cls, offer_name):
#         logger.debug('Getting offer cache')
#         cached_offer_info = cls.redis_db.get(offer_name)
#         if cached_offer_info:
#             cached_offer_info = json.loads(cached_offer_info.decode('utf-8'))
#         return cached_offer_info
#
#     @classmethod
#     def set_offer_cache(cls, offer_info):
#         cls.redis_db.set(offer_info['name'], json.dumps(offer_info), ex=MAX_CACHE_DURATION_SECONDS)
#         return offer_info
#
#     @classmethod
#     def clear_offer_cache(cls, offer_name):
#         cls.redis_db.delete(offer_name)


class Offer:
    def __init__(self, offer_name, board_id=None, partners_folder_id=None, monday_token=None):
        self.name = offer_name
        self.fields = self.find_offer_info(board_id, partners_folder_id, monday_token)

    def find_offer_info(self, board_id, partners_folder_id, monday_token):
        # offer_cached_info = OffersCache.get_cached_offer(self.name)
        # if offer_cached_info:

        offer_cached_info = OffersCache.get_cache().get(self.name)
        if offer_cached_info and (offer_cached_info['creation_timestamp'] + MAX_CACHE_DURATION_SECONDS > time.time()):
            logger.debug(f'Found valid cache for {self.name}')
            return offer_cached_info

        if not board_id or not partners_folder_id or not monday_token:
            logger.error('Offer was not found in cache and no board id or partners_folder_id was provided')
            raise OfferNotFound(self.name)

        logger.debug(f'Offer {self.name} was not found in cache')
        logger.debug(f'Getting new info to cache for offer {self.name}')
        raw_offer_monday_fields = self._get_raw_offer_info(board_id, monday_token)
        offer_info = self._process_raw_offer_info(raw_offer_monday_fields, partners_folder_id)

        OffersCache.set_offer_cache(offer_info)

        return offer_info

    def _get_raw_offer_info(self, board_id, monday_token):
        logger.info(f'Getting raw info for {self.name} from backend')

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

        raw_offer_monday_fields = {column['column']['title']: column['text'] for column in raw_columns}
        raw_offer_monday_fields['name'] = self.name
        raw_offer_monday_fields['is_priority'] = True
        raw_offer_monday_fields['creation_timestamp'] = time.time()
        return raw_offer_monday_fields

    def _process_raw_offer_info(self, raw_offer_info, partners_folder_id):
        if not raw_offer_info:
            raise OfferNotFound(self.name)

        logger.debug(f'Processing raw offer {self.name} info')

        offer_info = self.validate_offer_google_drive_url(raw_offer_info, partners_folder_id)

        return offer_info

    def validate_offer_google_drive_url(self, offer_monday_fields, partners_folder_id):
        offer_name = offer_monday_fields['name']
        google_drive_offer_folder_url = offer_monday_fields.get('Copy Location')
        if not google_drive_offer_folder_url:
            logger.warning(f'Google drive offer folder url was not found in Monday, starting manual search')
            google_drive_folder_id = self.find_offer_folder_manually(partners_folder_id)

        else:
            raw_google_drive_folder_id = google_drive_offer_folder_url.split('/folders/')[1]

            if not google_services.GoogleDrive.get_folder_by_name('Lift', raw_google_drive_folder_id, False):
                logger.warning(
                    f'Something wrong with Copy Location url of offer {offer_name}, no lift folder was found in given folder')

                maybe_google_drive_folder_id = google_services.GoogleDrive.get_folder_by_name('HTML+SL',
                                                                                              raw_google_drive_folder_id,
                                                                                              strict=False)
                if maybe_google_drive_folder_id:
                    google_drive_folder_id = maybe_google_drive_folder_id['id']
                else:
                    logger.warning(f'Google drive offer folder url was incorrect in Monday, starting manual search')
                    google_drive_folder_id = self.find_offer_folder_manually(partners_folder_id)
            else:
                google_drive_folder_id = raw_google_drive_folder_id
        offer_monday_fields['Copy Location'] = 'https://drive.google.com/drive/folders/' + google_drive_folder_id
        return offer_monday_fields

    def find_offer_folder_manually(self, partners_folder_id):
        offer_general_folder = self.get_offer_general_folder(partners_folder_id)

        offer_folder_id = google_services.GoogleDrive.get_folder_by_name('HTML+SL', offer_general_folder['id'],
                                                                         strict=False)
        if offer_folder_id:
            offer_folder_id = offer_folder_id['id']
        else:
            logger.warning(
                f'Folder "HTML+SL" was not found for offer {self.name}. Folder id where searching: {offer_general_folder}')

        return offer_folder_id

    def get_offer_general_folder(self, partners_folder_id):
        for partner_folder in google_services.GoogleDrive.get_folders_of_folder(partners_folder_id):

            partner_folder_id = partner_folder['id']
            offer_general_folder = google_services.GoogleDrive.get_folder_by_name(self.name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        logger.warning(f'No Partners with offer {self.name} was found in GoogleDrive')

    def get_priority_footer_values(self, tableID, pages, text_column, link_column, id_column):

        if not self.fields['is_priority']:
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
            self.update_offer_cache('is_priority', False)
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

    def update_offer_cache(self, key, new_value):
        # offer_info = OffersCache.get_cached_offer(self.name)
        offer_info = OffersCache.get_cache().get(self.name)
        offer_info[key] = new_value

        OffersCache.set_offer_cache(offer_info)

    @staticmethod
    def get_copy_files(lift_folder):
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

    def get_copy_files_content(self, lift_number):
        logger.info(f'Searching copy files for offer {self.name} and lift {lift_number}')

        lift_folder = google_services.GoogleDrive.get_folder_by_name(f'Lift {lift_number}',
                                                                     self.fields['Copy Location'].split('/folders/')[1])

        if not lift_folder:
            logger.warning(
                f'Could not find folder Lift {lift_number} in offer {self.name}. Please check if folder exist on google drive')
            lift_file, sl_file = None, None
        else:
            lift_file, sl_file = self.get_copy_files(lift_folder)

        lift_file_content, sl_file_content = None, None
        if lift_file:
            lift_file_content = google_services.GoogleDrive.get_file_content(lift_file)
        else:
            logger.warning(f'Lift file for {self.name} was not found')

        if sl_file:
            sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
        else:
            logger.warning(f'Sl file for {self.name} was not found')

        return lift_file_content, sl_file_content


class OfferException(Exception):
    def __init__(self, offer_name, message):
        self.offer_name = offer_name
        super().__init__(message)


class OfferNotFound(OfferException):
    def __init__(self, offer_name):
        message = f'Could not find info about {offer_name}'
        super().__init__(offer_name, message)


class OfferFolderIdNotFound(OfferException):
    def __init__(self, offer_name):
        message = f'Offer {offer_name} folder id with lifts was not found'
        super().__init__(offer_name, message)


class StatusNotAllowed(OfferException):
    def __init__(self, offer_name, offer_status):
        message = f'{offer_name} have status {offer_status}. Not allowed to send'
        super().__init__(offer_name, message)
