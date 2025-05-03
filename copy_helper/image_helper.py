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
    def add_image_block(cls, lift_file_content, image_block):

        return lift_file_content

    @classmethod
    def process_images(cls, copy, image_block):
        src_part_pattern = r'src="[^"]*'
        images_urls = []
        src_list = re.findall(src_part_pattern, copy.lift_html)
        if len(src_list) == 0:
            if copy.img_code:
                logging.info('Copy has img code and doesnt contain images')
                logging.debug(f'Adding image block to copy {copy.str_rep}')
                copy.lift_html = copy.lift_html.replace('<br><br>',
                                                        f'<!-- image-block-start -->{image_block}<!-- image-block-end -->',
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

            # cls.save_image(f'{str_copy}-image-{index + 1}', img_url, date)

        copy.lift_images = images_urls
        return copy
