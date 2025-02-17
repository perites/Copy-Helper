import logging
import time

import requests

from . import google_services
from . import tools
from . import exceptions

offers_info_endpoint = 'https://prior-shea-inri-a582c73b.koyeb.app/monday/product/'
path_to_offers_info_cache = 'SystemData/offers_info_cache.json'

monday_id_to_names = {'status7': 'status',
                      '_____': 'google_drive_folder_id',
                      '_____8': 'volume_green',
                      'text0': 'img_it',
                      'text21__1': 'rt_tm'}


class Offer:

    @classmethod
    def get_offer_info(cls, offer_name):
        logging.info(f'Searching info for offer {offer_name}')

        offers_info_cache = tools.FileHelper.read_json_data(path_to_offers_info_cache)
        offer_info_cache = offers_info_cache.get(offer_name)
        if offer_info_cache and (offer_info_cache['time_set'] + 60 * 60 * 6) > time.time():
            logging.debug(f'Found in cache')
            offer_info = offer_info_cache
        else:
            logging.debug(f'Not found in cache, making request')
            offer_info = cls.set_offer_cache(offer_name)

        if offer_info['status'] not in ['Live', 'Restricted']:
            raise exceptions.OfferNotLive(offer_name)

        return offer_info

    @classmethod
    def set_offer_cache(cls, offer_name):
        offer_info_request = requests.get(offers_info_endpoint + offer_name)

        if not offer_info_request.content:
            raise exceptions.OfferWasNotFoundError(offer_name)

        offer_info = offer_info_request.json()

        offer_info = cls.process_raw_offer_info(offer_info, offer_name)

        offers_info_cache = tools.FileHelper.read_json_data(path_to_offers_info_cache)
        offers_info_cache[offer_name] = offer_info

        tools.FileHelper.write_json_data(path_to_offers_info_cache, offers_info_cache)

        return offer_info

    @classmethod
    def process_raw_offer_info(cls, raw_offer_info, offer_name):
        processed_offer_info = {'offer_name': offer_name}

        for column in raw_offer_info['column_values']:
            if column['id'] in monday_id_to_names.keys():
                processed_offer_info[monday_id_to_names[column["id"]]] = column['text']

        google_drive_folder_id = cls.google_drive_folder_id_from_url(offer_name,
                                                                     processed_offer_info['google_drive_folder_id'])

        processed_offer_info['google_drive_folder_id'] = google_drive_folder_id

        processed_offer_info['time_set'] = time.time()

        return processed_offer_info

    @staticmethod
    def google_drive_folder_id_from_url(offer_name, google_drive_url):

        if google_drive_url:
            google_drive_folder_id = google_drive_url.split('/folders/')[1]
        else:
            google_drive_folder_id = google_services.GoogleDrive.get_offer_folder_id(offer_name)

        return google_drive_folder_id

    @staticmethod
    def get_lift_files(offer_name, google_drive_folder_id, lift_number):

        logging.info(f'Searching for lift files for offer {offer_name} and lift {lift_number}')

        lift_folder = google_services.GoogleDrive.get_folder_by_name(f"Lift {lift_number}",
                                                                     google_drive_folder_id)

        logging.debug(f"Searching for files in lift folder '{lift_folder['name']}'...")

        query = f'mimeType!="application/vnd.google-apps.folder" and trashed=false and "{lift_folder['id']}" in parents'
        fields = 'files(id, name, mimeType)'
        lift_folder_files = google_services.GoogleDrive.execute_query(query, fields)

        copy_file = None
        mjml_found = False

        sl_file = None

        for file in lift_folder_files:
            if not mjml_found:
                if (file['name'].lower().endswith('.html')) and ('mjml' in file['name'].lower()) and (
                        'SL' not in file['name']):
                    copy_file = file
                    mjml_found = True
                    logging.debug(f"Found copy file (mjml): {copy_file['name']}")

                elif (not copy_file) and (file['name'].lower().endswith('.html')) and ('SL' not in file['name']):
                    copy_file = file

            if not sl_file:
                if 'sl' in file['name'].lower():
                    sl_file = file
                    logging.debug(f"Found SL file: {sl_file['name']}")

            if mjml_found and sl_file:
                break

        return copy_file, sl_file
