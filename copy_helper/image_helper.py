import logging
import os
import re
import traceback

import requests
from PIL import Image

from . import settings


class ImageHelper:
    @classmethod
    def save_image(cls, image_file_name, image_url, date):
        try:
            save_image_path = settings.GeneralSettings.save_image_path + f'{date}/'

            if not os.path.exists(save_image_path):
                os.makedirs(save_image_path)

            temp_full_image_path = save_image_path + image_file_name

            with os.scandir(save_image_path) as entries:
                for entry in entries:
                    if entry.is_file() and image_file_name in entry.name:
                        logging.debug(f'Not saving {image_file_name} - image already saved')
                        return

            logging.debug(f'Saving {image_file_name} to {save_image_path}')

            with open(temp_full_image_path, 'wb') as file:
                response = requests.get(image_url, stream=True)
                if not response.ok:
                    logging.warning(
                        f'Error while saving image {image_file_name}. Request status code {response.status_code}')

                for chunk in response.iter_content(512):
                    file.write(chunk)

            img = Image.open(temp_full_image_path)
            ext = img.format.lower()
            img.close()

            new_full_image_path = temp_full_image_path + f'.{ext}'

            os.rename(temp_full_image_path, new_full_image_path)

        except Exception as e:
            logging.error(f'Error while saving image {image_file_name}. Details : {e}')
            logging.debug(traceback.format_exc())

    @classmethod
    def add_image_block(cls, lift_file_content, str_copy, image_block):
        logging.info(f'Adding image block to copy {str_copy}')

        lift_file_content = lift_file_content.replace('<br><br>',
                                                      f'<!-- image-block-start -->{image_block}<!-- image-block-end -->',
                                                      1)
        return lift_file_content

    @classmethod
    def process_images(cls, lift_file_content, str_copy, image_block, img_code, date):
        src_part_pattern = r'src="[^"]*'
        processed_urls = []
        src_list = re.findall(src_part_pattern, lift_file_content)
        if len(src_list) == 0:
            if img_code:
                logging.info('Copy has img code and doesnt contain images')
                lift_file_content = cls.add_image_block(lift_file_content, str_copy, image_block)
                return lift_file_content, 0
            else:
                logging.debug('No images no image code, doing nothing')
                return lift_file_content, -1

        if settings.GeneralSettings.save_image_path:
            logging.info(f'Found {len(src_list)} images, saving...')
            for index, src_part in enumerate(src_list):
                img_url = src_part.split('"')[1]
                if img_url in processed_urls:
                    continue

                cls.save_image(f'{str_copy}-image-{index + 1}', img_url, date)
                processed_urls.append(img_url)

        return lift_file_content, len(src_list)
