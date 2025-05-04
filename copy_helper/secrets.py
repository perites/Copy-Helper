import json
import logging


def update_credentials(new_info):
    secrets = read_json_file(PATH_TO_SECRETS_FILE)
    secrets['CREDENTIALS'] = new_info
    write_json_file(PATH_TO_SECRETS_FILE, secrets)


def read_json_file(path):
    logging.debug(f'Reading json file {path}')
    with open(path, 'r', encoding="utf-8") as file:
        return json.load(file)


def write_json_file(path, data):
    logging.debug(f'Writing to {path}')
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)


PATH_TO_SECRETS_FILE = 'copy_helper/secrets.json'
secrets = read_json_file(PATH_TO_SECRETS_FILE)

OAUTH_CLIENT = secrets['OAUTH_CLIENT']
MONDAY_TOKEN = secrets['MONDAY_TOKEN']

CREDENTIALS = secrets.get('CREDENTIALS')
