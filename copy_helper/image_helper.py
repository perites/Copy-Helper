from . import settings
import re
import requests
import os

import logging


class ImageHelper:
    @classmethod
    def save_image(cls, image_file_name, image_url):
        save_image_path = settings.GeneralSettings.save_image_path
        full_image_path = f'{save_image_path}/{image_file_name}'

        if not os.path.exists(full_image_path):
            logging.debug(f'Saving {image_file_name} to {save_image_path}')
            response = requests.get(image_url)
            with open(full_image_path, 'wb') as file:
                file.write(response.content)

        else:
            logging.debug(f'Not saving {image_file_name} - image already saved')

    @classmethod
    def add_image_block(cls, copy, lift_file_content, image_block):
        logging.info(f'Adding image block to copy {str(copy)}')

        lift_file_content = lift_file_content.replace('<br><br>',
                                                      f'<!-- image-block-start -->{image_block}<!-- image-block-end -->',
                                                      1)
        return lift_file_content

    @classmethod
    def process_images(cls, copy, image_block, lift_file_content):
        src_part_pattern = r'src="[^"]*'

        src_list = re.findall(src_part_pattern, lift_file_content)
        if len(src_list) == 0 and copy.img_code:
            logging.info('Copy has img code and doesnt contain images')
            lift_file_content = cls.add_image_block(copy, lift_file_content, image_block)
            return lift_file_content

        if settings.GeneralSettings.save_image_path:
            logging.info(f'Found {len(src_list)} images, saving...')
            for index, src_part in enumerate(src_list):
                img_url = src_part.split('"')[1]
                file_extension = img_url.split('.')[::-1][0]
                image_file_name = f'{str(copy)}-image-{index + 1}.{file_extension}'

                cls.save_image(image_file_name, img_url)

        return lift_file_content
