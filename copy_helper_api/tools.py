import json
import logging


def read_json_file(path):
    logging.debug(f'Reading json file {path}')
    with open(path, 'r', encoding="utf-8") as file:
        return json.load(file)


def write_json_file(path, data):
    logging.debug(f'Writing to {path}')
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)
