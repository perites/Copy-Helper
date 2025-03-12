import dataclasses
import json
import logging
import os
import time

import redis
import requests
from flask import g

from copy_helper_api import google_services

MAX_CACHE_DURATION_SECONDS = 60 * 60 * 6

ALLOWED_STATUSES = ['Live', 'Restricted']


class OffersCache:
    DATABASE_CREDENTIALS = json.loads(os.getenv('DATABASE_CREDENTIALS'))
    redis_db = redis.Redis(host=DATABASE_CREDENTIALS['host'],
                           password=DATABASE_CREDENTIALS['password'], port=DATABASE_CREDENTIALS['port'],
                           ssl=True)

    @classmethod
    def get_cached_offer(cls, offer_name):
        logging.debug('Getting all offers info cache')
        cached_offer_info = cls.redis_db.get(offer_name)
        if cached_offer_info:
            cached_offer_info = json.loads(cached_offer_info.decode('utf-8'))
        return cached_offer_info

    @classmethod
    def set_offer_cache(cls, offer_info):
        cls.redis_db.set(offer_info['name'], json.dumps(offer_info))

        return offer_info

    # @classmethod
    # def clear_cache(cls, option):
    #     match option:
    #         case 'all':
    #             cls.set_cache({})
    #             logging.info('All cache successfully cleared')
    #         case _:
    #             all_cache = cls.get_cache()
    #             if not all_cache.get(option):
    #                 logging.warning(f'Can`t clear cache of {option} as it is NOT found in cache')
    #                 return
    #
    #             del all_cache[option]
    #             cls.set_cache(all_cache)
    #             logging.info(f'Cache for offer {option} cleared')


class OfferGoogleDriveHelper:

    @staticmethod
    def get_copy_files(lift_folder_id):
        lift_folder_files = google_services.GoogleDrive.get_files_from_folder(lift_folder_id)

        lift_file = None
        mjml_found = False

        sl_file = None

        for file in lift_folder_files:
            if not mjml_found:
                if (file['name'].lower().endswith('.html')) and ('mjml' in file['name'].lower()) and (
                        'SL' not in file['name']):
                    lift_file = file
                    mjml_found = True
                    logging.debug(f"Found copy file (mjml): {lift_file['name']}")

                elif (not lift_file) and (file['name'].lower().endswith('.html')) and ('SL' not in file['name']):
                    lift_file = file

            if not sl_file:
                if 'sl' in file['name'].lower():
                    sl_file = file
                    logging.debug(f"Found SL file: {sl_file['name']}")

            if mjml_found and sl_file:
                break

        return lift_file, sl_file

    @staticmethod
    def get_lift_folder(google_drive_folder_id, lift_number):
        folder_info = google_services.GoogleDrive.get_folder_by_name(f'Lift {lift_number}', google_drive_folder_id,
                                                                     strict=True)

        return folder_info

    @staticmethod
    def get_offer_general_folder(offer_name):
        for partner_folder in google_services.GoogleDrive.get_folders_of_folder(
                g.user_settings.parent_folder_id):

            partner_folder_id = partner_folder['id']
            offer_general_folder = google_services.GoogleDrive.get_folder_by_name(offer_name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        logging.warning(f'No Partners with offer {offer_name} was found in GoogleDrive')

    @staticmethod
    def get_offer_folder_id(offer_name, offer_general_folder):
        offer_folder_id = google_services.GoogleDrive.get_folder_by_name('HTML+SL', offer_general_folder, strict=False)
        if not offer_folder_id:
            logging.debug(
                f'Folder "HTML+SL" was not found for offer {offer_name}. Folder id where searching: {offer_general_folder}')
            return

        return offer_folder_id['id']


class OfferGoogleSheetHelper:
    @staticmethod
    def get_priority_offer_coordinates(offer_name, pages_to_search):
        for page in pages_to_search:
            priority_product_index = google_services.GoogleSheets.get_table_index_of_value(
                g.user_settings.priority_products_table_id, offer_name, f'{page}!A:A', is_row=False)

            if priority_product_index:
                return priority_product_index, page

        return False, False


class OfferInfoFinder:
    def __init__(self, offer_name):
        self.name = offer_name

    def find_offer_info(self):
        offer_cached_info = OffersCache.get_cached_offer(self.name)

        if not offer_cached_info:
            logging.debug(f'Offer {self.name} was not found in cache')
            offer_info = self._get_new_offer_info()
            OffersCache.set_offer_cache(offer_info)

        elif offer_cached_info['creation_timestamp'] + MAX_CACHE_DURATION_SECONDS < time.time():
            logging.debug(f'Cache for offer {self.name} expired')
            offer_info = self._get_new_offer_info()
            OffersCache.set_offer_cache(offer_info)

        else:
            logging.debug(f'Found valid cache for {self.name}')
            offer_info = offer_cached_info

        return offer_info

    def complain(self, text):
        logging.warning(f'Something wrong with offer {self.name}. Details : {text}')
        with open('wrong_offers.txt', 'a', encoding='utf-8') as file:
            file.write(text + '\n')

    def _get_new_offer_info(self):
        logging.debug(f'Getting new info to cache for offer {self.name}')
        raw_offer_info = self._get_raw_offer_info()
        offer_info = self._process_raw_offer_info(raw_offer_info)

        return offer_info

    def _get_raw_offer_info(self):
        logging.info(f'Getting raw info for {self.name} from backend')

        offers_info_endpoint = 'https://prior-shea-inri-a582c73b.koyeb.app/monday/product/'
        offer_info_request = requests.get(
            offers_info_endpoint + self.name + f'?requester=copy-helper')

        if not offer_info_request.content:
            logging.debug(f'Offer {self.name} was not found at backend')
            raise OfferNotFound(self.name)

        raw_offer_info = offer_info_request.json()

        return raw_offer_info

    def _process_raw_offer_info(self, raw_offer_info):
        if not raw_offer_info:
            raise OfferNotFound(self.name)

        logging.debug(f'Processing raw offer {self.name} info')

        processed_offer_info = {'name': self.name, 'raw_column_values': raw_offer_info['column_values'],
                                'creation_timestamp': time.time(),
                                'is_priority': True}  # at first treat all offers as priority

        for column in raw_offer_info['column_values']:
            if column['id'] == 'status7':
                processed_offer_info['status'] = column['text']

            elif column['id'] == '_____':
                raw_google_drive_folder_url = column['text']
                google_drive_folder_id = self._find_offer_google_drive_folder_id(raw_google_drive_folder_url)
                if not google_drive_folder_id:
                    raise OfferFolderIdNotFound(self.name)

                processed_offer_info['google_drive_folder_id'] = google_drive_folder_id

        return processed_offer_info

    def _find_offer_google_drive_folder_id(self, raw_google_drive_offer_folder_url):
        if raw_google_drive_offer_folder_url:
            logging.debug('Checking if folder in Monday actually for HTML+SL folder')

            raw_google_drive_folder_id = raw_google_drive_offer_folder_url.split('/folders/')[1]
            maybe_google_drive_folder_id = OfferGoogleDriveHelper.get_offer_folder_id(self.name,
                                                                                      raw_google_drive_folder_id)

            if maybe_google_drive_folder_id:
                self.complain(f'{self.name} - wrong link for google drive in Monday')
                return maybe_google_drive_folder_id

            return raw_google_drive_folder_id

        else:
            logging.warning(f'Google drive offer folder url was not found in Monday, starting manual search')
            self.complain(f'{self.name} - link for google drive missing in Monday')

            offer_general_folder = OfferGoogleDriveHelper.get_offer_general_folder(self.name)
            google_drive_folder_id = OfferGoogleDriveHelper.get_offer_folder_id(self.name, offer_general_folder)

        if not google_drive_folder_id:
            logging.warning(f'Google drive folder id was not found for offer {self.name}')

        return google_drive_folder_id


@dataclasses.dataclass
class Offer:
    name: str
    status: str
    google_drive_folder_id: str
    is_priority: bool
    _raw_column_values: dict
    _raw_offer_info: dict

    @classmethod
    def find(cls, offer_name):
        offer_info = OfferInfoFinder(offer_name).find_offer_info()
        if not offer_info:
            raise OfferNotFound(offer_name)

        if offer_info['status'] not in ALLOWED_STATUSES:
            raise StatusNotAllowed(offer_name, offer_info['status'])

        return cls(
            name=offer_info['name'],
            status=offer_info['status'],
            google_drive_folder_id=offer_info['google_drive_folder_id'],
            is_priority=offer_info['is_priority'],

            _raw_column_values=offer_info['raw_column_values'],
            _raw_offer_info=offer_info
        )

    def get_priority_footer_values(self, priority_unsub_link_info):
        logging.debug(f'Searching for footer for offer {self.name}')

        priority_product_index, page = OfferGoogleSheetHelper.get_priority_offer_coordinates(self.name,
                                                                                             ['Other PP', 'FIT'])

        if not priority_product_index:
            self.is_priority = False
            self.update_priority(False)
            return '', ''

        priority_products_table_id = g.user_settings.priority_products_table_id

        priority_product_index += 1

        text_value = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                      f'{page}!C{priority_product_index}')[0][0]

        unsub_url = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                     f'{page}!F{priority_product_index}')
        if not unsub_url:
            logging.warning('Unsub url not found')
            unsub_url = 'UNSUB_URL_NOT_FOUND'
        else:
            unsub_url = unsub_url[0][0]

        if unsub_link_type := priority_unsub_link_info.get('Type'):
            match unsub_link_type:
                case 'VolumeGreen':
                    id = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                          f'{page}!E{priority_product_index}')
                    if id:
                        unsub_url = priority_unsub_link_info['Start'] + id[0][0] + priority_unsub_link_info['End']
                    else:
                        logging.warning('VolumeGreen was not found in priority table, using default link')

        return text_value, unsub_url

    def update_offer_cache(self, key, new_value):
        offer_info = self._raw_offer_info
        offer_info[key] = new_value

        OffersCache.set_offer_cache(offer_info)

    def update_priority(self, new_value):
        self.update_offer_cache('is_priority', new_value)

    def tracking_id(self, tracking_id_name):
        tracking_id_to_monday_id = {
            'volume_green': '_____8',
            'img_it': 'text0',
            'rt_tm': 'text21__1',
            'cm_tm': 'dup__of_rt_tm_mkn9g0sh'
        }
        monday_id = tracking_id_to_monday_id.get(tracking_id_name)
        if not monday_id:
            logging.warning(f'{tracking_id_name} was not found for {self.name}')
            return f'{tracking_id_name}_NOT_FOUND'

        for column in self._raw_column_values:
            if column['id'] == monday_id:
                return column['text']


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
