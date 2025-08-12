import json
import logging
import os

import default_config

logger = logging.getLogger(__name__)


def update_credentials(new_info):
    secrets = read_json_file(PATH_TO_SECRETS_FILE)
    secrets['CREDENTIALS'] = new_info
    write_json_file(PATH_TO_SECRETS_FILE, secrets)


def read_json_file(path):
    logger.debug(f'Reading json file {path}')
    with open(path, 'r', encoding="utf-8") as file:
        return json.load(file)


def write_json_file(path, data):
    logger.debug(f'Writing to {path}')
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)


PATH_TO_SECRETS_FILE = 'secrets.json'

if not os.path.exists('PATH_TO_SECRETS_FILE'):
    open('secrets.json', 'w').write(default_config.default_secret_file)
    logging.warning('Fill secrets file!')
    exit()

secrets = read_json_file(PATH_TO_SECRETS_FILE)

OAUTH_CLIENT = secrets['OAUTH_CLIENT']
MONDAY_TOKEN = secrets['MONDAY_TOKEN']

CREDENTIALS = secrets.get('CREDENTIALS')
