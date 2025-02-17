import json
import logging

import os

from io import BytesIO
from docx import Document

import re


class FileHelper:
    @staticmethod
    def read_json_data(path_to_json_file):
        logging.debug(f'Trying to read {path_to_json_file} json file')
        try:
            with open(path_to_json_file, 'r', encoding="utf-8") as file:
                data = file.read()
                if not data:
                    raise FileNotFoundError

                data = json.loads(data)

                return data
        except FileNotFoundError:
            logging.debug(f'FileNotFoundError was raised for {path_to_json_file} returning empty dict')
            return {}

    @staticmethod
    def read_file(path):
        try:
            with open(path, 'r', encoding="utf-8") as file:
                data = file.read()

                return data
        except FileNotFoundError:
            logging.error(f"Could not fing file {path}")

    @staticmethod
    def write_json_data(path_to_json_file, data):
        logging.debug(f'Dumping data and write to {path_to_json_file}')
        json_data = json.dumps(data)
        with open(path_to_json_file, 'w', encoding="utf-8") as file:
            file.write(json_data)

    @staticmethod
    def write_to_file(path, data, mode='w'):
        logging.debug(f"Writing to {path}")

        dir_path = os.path.dirname(path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(path, mode, encoding='utf-8') as file:
            file.write(data)

    @staticmethod
    def extract_text_from_docx(binary_data):
        doc_file = BytesIO(binary_data)
        doc = Document(doc_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text


class RegExHelper:
    @staticmethod
    def regex_replace(str_pattern, source, new):
        name_to_reqex = {'FontFamily': r'font-family\s*:\s*([^;]+);?',
                         'FontSize': r'font-size\s*:\s*(16|18)?px;',
                         'Color': r'color\s*:\s*([^;]+);?'}

        str_pattern = name_to_reqex.get(str_pattern) if name_to_reqex.get(str_pattern) else str_pattern

        pattern = re.compile(str_pattern, re.IGNORECASE)
        if not pattern.search(source):
            return source, False

        content = pattern.sub(lambda match: new, source)

        return content, True

    @staticmethod
    def match_str_copy(str_copy):
        pattern = r'^([A-Za-z]+)(\d+)(.*)$'
        match = re.match(pattern, str_copy)
        if match:
            offer_name = match.group(1)
            lift_number = match.group(2)
            img_code = match.group(3)

            return offer_name, lift_number, img_code

        logging.debug(f'Failed to match str_copy {str_copy}')


def clear_cache(option):
    if option == 'all':
        FileHelper.write_json_data('SystemData/offers_info_cache.json', {})
        return

    all_cache = FileHelper.read_json_data('SystemData/offers_info_cache.json')
    if not all_cache.get(option):
        return
    del all_cache[option]
    FileHelper.write_json_data('SystemData/offers_info_cache.json', all_cache)
