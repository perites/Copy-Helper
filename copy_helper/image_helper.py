from . import settings
import re
import requests
import os

import logging
from PIL import Image


class ImageHelper:
    @classmethod
    def save_image(cls, image_file_name, image_url, date):
        try:
            save_image_path = f'{settings.GeneralSettings.save_image_path}/{date}'

            if not os.path.exists(save_image_path):
                os.makedirs(save_image_path)

            temp_full_image_path = f'{save_image_path}/{image_file_name}'

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
            logging.exception(f'Error while saving image {image_file_name}')

    @classmethod
    def add_image_block(cls, copy, lift_file_content, image_block):
        logging.info(f'Adding image block to copy {str(copy)}')

        lift_file_content = lift_file_content.replace('<br><br>',
                                                      f'<!-- image-block-start -->{image_block}<!-- image-block-end -->',
                                                      1)
        return lift_file_content

    @classmethod
    def process_images(cls, copy, image_block, lift_file_content, date):
        src_part_pattern = r'src="[^"]*'

        src_list = re.findall(src_part_pattern, lift_file_content)
        if len(src_list) == 0:
            if copy.img_code:
                logging.info('Copy has img code and doesnt contain images')
                lift_file_content = cls.add_image_block(copy, lift_file_content, image_block)
                return lift_file_content
            else:
                logging.debug('No images no image code, doing nothing')
                return

        if settings.GeneralSettings.save_image_path:
            logging.info(f'Found {len(src_list)} images, saving...')
            for index, src_part in enumerate(src_list):
                img_url = src_part.split('"')[1]

                cls.save_image(f'{str(copy)}-image-{index + 1}', img_url, date)

        return lift_file_content
