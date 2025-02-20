import dataclasses
import logging
import time

import requests

from . import google_services
from . import settings
from . import tools

PATH_TO_OFFERS_INFO_CACHE = 'SystemData/offers_info_cache.json'

MAX_CACHE_DURATION_SECONDS = 60 * 60 * 6

ALLOWED_STATUSES = ['Live', 'Restricted']


@dataclasses.dataclass
class OfferInfo:
    name: str
    status: str
    google_drive_folder_id: str
    _tracking_ids: dict

    def tracking_id(self, tracking_id_name):
        return self._tracking_ids.get(tracking_id_name) or f"{tracking_id_name}_NOT_FOUND"


class OfferGoogleDriveHelper(google_services.GoogleDrive):

    @classmethod
    def _get_copy_files(cls, name, google_drive_folder_id, lift_number):
        logging.info(f'Searching for lift files for offer {name} and lift {lift_number}')

        if not google_drive_folder_id:
            logging.warning('No Google Drive folder id was provided, lift files not received')
            return None, None

        lift_folder = cls.get_folder_by_name(f"Lift {lift_number}", google_drive_folder_id)
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
    def _get_offer_folder_id(cls, name):
        offer_general_folder = cls._get_offer_general_folder(name)
        if not offer_general_folder:
            return

        offer_folder_id = cls.get_folder_by_name('HTML+SL', offer_general_folder, strict=False)[0]
        if not offer_folder_id:
            logging.warning(
                f'Folder "HTML+SL" was not found for offer {name}. Folder id where searching: {offer_general_folder}')
        return offer_folder_id


class Offer(OfferGoogleDriveHelper):
    name: str

    def __init__(self, name):
        self.name = name
        self.info = self.get_offer_info()

    def get_offer_info(self):
        logging.info(f'Searching info for offer {self.name}')

        offer_info = self._find_cached_info()
        if not offer_info:
            raw_offer_info = self._get_raw_offer_info()
            offer_info = self._process_raw_offer_info(raw_offer_info)
            self._set_offer_cache(offer_info)

        if offer_info['status'] not in ALLOWED_STATUSES:
            raise OfferNotAllowedToSend(self.name)

        return OfferInfo(name=offer_info['name'],
                         status=offer_info['status'],
                         google_drive_folder_id=offer_info['google_drive_folder_id'],
                         _tracking_ids=offer_info['tracking_ids']
                         )

    def get_copy_files(self, lift_number):
        return self._get_copy_files(self.name, self.info.google_drive_folder_id, lift_number)

    @staticmethod
    def _get_cache():
        logging.debug('Getting offers info cache')
        try:
            offers_info_cache = tools.read_json_file(PATH_TO_OFFERS_INFO_CACHE)
        except FileNotFoundError:
            return {}

        return offers_info_cache

    @staticmethod
    def _set_cache(new_offers_info_cache):
        logging.debug('Setting new offers info cache')
        tools.write_json_file(PATH_TO_OFFERS_INFO_CACHE, new_offers_info_cache)

    def _find_cached_info(self):
        offers_info_cache = self._get_cache()
        offer_cached_info = offers_info_cache.get(self.name)
        if not offer_cached_info:
            logging.debug(f'Offer {self.name} was not found in cache')
            return
        elif offer_cached_info['creation_timestamp'] + MAX_CACHE_DURATION_SECONDS < time.time():
            logging.debug(f'Cache for offer {self.name} expired')
            return

        logging.debug(f'Found valid cache for {self.name}')
        return offer_cached_info

    def _set_offer_cache(self, offer_info, offers_info_cache=None):
        logging.debug(f'Caching info for offer {self.name}')

        offers_info_cache = offers_info_cache if offers_info_cache else self._get_cache()
        offers_info_cache[self.name] = offer_info

        self._set_cache(offers_info_cache)

    def _get_raw_offer_info(self):
        logging.debug(f'Getting info for name {self.name} from backend')

        offers_info_endpoint = 'https://prior-shea-inri-a582c73b.koyeb.app/monday/product/'
        offer_info_request = requests.get(
            offers_info_endpoint + self.name + f'?requester=copy-helper-{settings.GeneralSettings.machine_id}')

        if not offer_info_request.content:
            logging.warning(f'Offer {self.name} was not found at backend')
            return None

        raw_offer_info = offer_info_request.json()

        return raw_offer_info

    def _process_raw_offer_info(self, raw_offer_info):
        logging.debug('Processing raw offer info')

        monday_id_to_names = {'status7': 'status',
                              '_____8': 'volume_green',
                              'text0': 'img_it',
                              'text21__1': 'rt_tm'}

        tracking_ids = ['volume_green', 'img_it', 'rt_tm']

        processed_offer_info = {'name': self.name, 'tracking_ids': {}}

        for column in raw_offer_info['column_values']:
            if column['id'] in monday_id_to_names.keys():
                field_name = monday_id_to_names[column["id"]]
                if field_name in tracking_ids:
                    processed_offer_info["tracking_ids"][field_name] = column['text']
                else:
                    processed_offer_info[field_name] = column['text']
            elif column['id'] == '_____':
                google_drive_folder_url = column['text']
                google_drive_folder_id = self._get_google_drive_offer_folder_id(google_drive_folder_url)

                processed_offer_info['google_drive_folder_id'] = google_drive_folder_id

        processed_offer_info['creation_timestamp'] = time.time()

        return processed_offer_info

    def _get_google_drive_offer_folder_id(self, google_drive_offer_folder_url):
        if google_drive_offer_folder_url:
            google_drive_folder_id = google_drive_offer_folder_url.split('/folders/')[1]
        else:
            logging.info(f'Google drive offer folder url was not found in Monday, starting manual search')
            google_drive_folder_id = self._get_offer_folder_id(self.name)

        if not google_drive_folder_id:
            logging.warning(f'Google drive folder id was not found for offer {self.name}, returning None')

        return google_drive_folder_id

    @classmethod
    def clear_cache(cls, option):
        match option:
            case 'all':
                cls._set_cache({})

            case _:
                all_cache = cls._get_cache()
                if not all_cache.get(option):
                    return

                del all_cache[option]
                cls._set_cache(all_cache)


class OfferException(Exception):
    pass


class OfferNotAllowedToSend(OfferException):
    def __init__(self, offer_name):
        self.message = f'Offer {offer_name} status not in ALLOWED_STATUSES'
        super().__init__(self.message)
