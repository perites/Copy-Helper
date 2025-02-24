import dataclasses
import logging
import time

import requests

from . import google_services
from . import settings
from . import tools
from . import paths

PATH_TO_OFFERS_INFO_CACHE = paths.PATH_TO_JSON_FILE_OFFERS_CACHE.full_path()

MAX_CACHE_DURATION_SECONDS = 60 * 60 * 6

ALLOWED_STATUSES = ['Live', 'Restricted']


class OfferGoogleDriveHelper(google_services.GoogleDrive):

    @classmethod
    def get_copy_files(cls, lift_folder):

        lift_folder_files = cls.get_files_from_folder(lift_folder['id'])

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

    @classmethod
    def _get_offer_general_folder(cls, name):
        for partner_folder in cls.get_folders_of_folder(settings.GeneralSettings.parent_folder_id):
            partner_folder_id = partner_folder['id']
            offer_general_folder = cls.get_folder_by_name(name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        logging.warning(f'No Partners with offer {name} was found in GoogleDrive')

    @classmethod
    def _get_offer_folder_id(cls, name=None, offer_general_folder=None):
        offer_general_folder = cls._get_offer_general_folder(name) if not offer_general_folder else offer_general_folder
        if not offer_general_folder:
            return

        offer_folder_id = cls.get_folder_by_name('HTML+SL', offer_general_folder, strict=False)
        if not offer_folder_id:
            logging.debug(
                f'Folder "HTML+SL" was not found for offer {name}. Folder id where searching: {offer_general_folder}')
            return

        return offer_folder_id['id']

   
class OfferCacheHelper:

    @staticmethod
    def _get_cache():
        logging.debug('Getting all offers info cache')
        offers_info_cache = tools.read_json_file(PATH_TO_OFFERS_INFO_CACHE)
        # try:
        #     offers_info_cache = tools.read_json_file(PATH_TO_OFFERS_INFO_CACHE)
        # except FileNotFoundError:
        #     return {}

        return offers_info_cache

    @staticmethod
    def _set_cache(new_offers_info_cache):
        logging.debug('Setting new offers info cache')
        tools.write_json_file(PATH_TO_OFFERS_INFO_CACHE, new_offers_info_cache)

    @classmethod
    def _set_offer_cache(cls, offer_info):

        offers_info_cache = cls._get_cache()
        offers_info_cache[offer_info['name']] = offer_info

        cls._set_cache(offers_info_cache)

        return offer_info

    @classmethod
    def clear_cache(cls, option):
        match option:
            case 'all':
                cls._set_cache({})
                logging.info('All cache successfully cleared')
            case _:
                all_cache = cls._get_cache()
                if not all_cache.get(option):
                    logging.warning(f'Can`t clear cache of {option} as it is NOT found in cache')
                    return

                del all_cache[option]
                cls._set_cache(all_cache)
                logging.info(f'Cache for offer {option} cleared')


@dataclasses.dataclass
class Offer(OfferCacheHelper, OfferGoogleDriveHelper):
    name: str
    status: str
    google_drive_folder_id: str
    _raw_column_values: dict
    is_priority: bool

    @classmethod
    def find(cls, offer_name):
        try:
            offer_info = cls._find_offer_info(offer_name)
            if not offer_info:
                return
            if offer_info['status'] not in ALLOWED_STATUSES:
                logging.warning(f'{offer_info['name']} have status {offer_info['status']}. Not allowed to send')
                return

            return cls(
                name=offer_info['name'],
                status=offer_info['status'],
                google_drive_folder_id=offer_info['google_drive_folder_id'],
                _raw_column_values=offer_info['raw_column_values'],
                is_priority=offer_info['is_priority']
            )

        except Exception:
            logging.exception(f'Error while finding {offer_name}')
            return

    @classmethod
    def complain_about_offer(cls, text):
        logging.warning(f'Something wrong with offer. Details : {text}')
        with open('SystemData/wrong_monday_offers.txt', 'a', encoding='utf-8') as file:
            file.write(text + '\n')

    @classmethod
    def _find_offer_info(cls, offer_name):
        offers_info_cache = cls._get_cache()
        offer_cached_info = offers_info_cache.get(offer_name)

        if not offer_cached_info:
            logging.debug(f'Offer {offer_name} was not found in cache')
            offer_info = cls._get_new_offer_info(offer_name)
            cls._set_offer_cache(offer_info)

        elif offer_cached_info['creation_timestamp'] + MAX_CACHE_DURATION_SECONDS < time.time():
            logging.debug(f'Cache for offer {offer_name} expired')
            offer_info = cls._get_new_offer_info(offer_name)
            cls._set_offer_cache(offer_info)

        else:
            logging.debug(f'Found valid cache for {offer_name}')
            offer_info = offer_cached_info

        return offer_info

    @classmethod
    def _get_new_offer_info(cls, offer_name):
        logging.debug(f'Getting new info to cache for offer {offer_name}')
        raw_offer_info = cls._get_raw_offer_info(offer_name)
        offer_info = cls._process_raw_offer_info(raw_offer_info, offer_name)

        return offer_info

    @classmethod
    def _get_raw_offer_info(cls, offer_name):
        logging.info(f'Getting raw info for {offer_name} from backend')

        offers_info_endpoint = 'https://prior-shea-inri-a582c73b.koyeb.app/monday/product/'
        offer_info_request = requests.get(
            offers_info_endpoint + offer_name + f'?requester=copy-helper-{settings.GeneralSettings.machine_id}')

        if not offer_info_request.content:
            logging.warning(f'Offer {offer_name} was not found at backend')
            return None

        raw_offer_info = offer_info_request.json()

        return raw_offer_info

    @classmethod
    def _process_raw_offer_info(cls, raw_offer_info, offer_name):
        if not raw_offer_info:
            return

        logging.debug('Processing raw offer info')

        processed_offer_info = {'name': offer_name, 'raw_column_values': raw_offer_info['column_values']}
        for column in raw_offer_info['column_values']:
            if column['id'] == 'status7':
                processed_offer_info['status'] = column['text']

            elif column['id'] == '_____':
                raw_google_drive_folder_url = column['text']
                google_drive_folder_id = cls._get_google_drive_offer_folder_id(raw_google_drive_folder_url, offer_name)
                if not google_drive_folder_id:
                    return

                processed_offer_info['google_drive_folder_id'] = google_drive_folder_id

        processed_offer_info['creation_timestamp'] = time.time()
        processed_offer_info['is_priority'] = True  # at first treat all offers as priority

        return processed_offer_info

    @classmethod
    def _get_google_drive_offer_folder_id(cls, raw_google_drive_offer_folder_url, offer_name):
        if raw_google_drive_offer_folder_url:
            logging.debug('Checking in folder in Monday actually for HTML+SL folder')

            raw_google_drive_folder_id = raw_google_drive_offer_folder_url.split('/folders/')[1]
            maybe_google_drive_folder_id = cls._get_offer_folder_id(offer_general_folder=raw_google_drive_folder_id)

            if not maybe_google_drive_folder_id:
                return raw_google_drive_folder_id

            cls.complain_about_offer(f'{offer_name} - wrong link for google drive in Monday')

            return maybe_google_drive_folder_id

        else:
            logging.warning(f'Google drive offer folder url was not found in Monday, starting manual search')
            cls.complain_about_offer(f'{offer_name} - link for google drive missing in Monday')
            google_drive_folder_id = cls._get_offer_folder_id(offer_name)

        if not google_drive_folder_id:
            logging.warning(f'Google drive folder id was not found for offer {offer_name}')

        return google_drive_folder_id

    def update_offer_cache(self, key, new_value):
        offer_info = self._find_offer_info(self.name)
        offer_info[key] = new_value

        self._set_offer_cache(offer_info)

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
            return f'{tracking_id_name}_NOT_FOUND'

        for column in self._raw_column_values:
            if column['id'] == monday_id:
                return column['text']
