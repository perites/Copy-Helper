import json
import logging
import os

from copy_maker_core.secrets import secrets
from . import default_config

logger = logging.getLogger(__name__)


class LocalFilesHelper:
    PATH_TO_SETTINGS = '../General-Settings.json'

    @classmethod
    def read_settings_file(cls):
        logger.debug(f'Reading json file {cls.PATH_TO_SETTINGS}')
        with open(cls.PATH_TO_SETTINGS, 'r', encoding="utf-8") as file:
            return json.load(file)

    @classmethod
    def write_settings_file(cls, data):
        logger.debug(f'Writing to {cls.PATH_TO_SETTINGS}')
        with open(cls.PATH_TO_SETTINGS, 'w') as file:
            json.dump(data, file, indent=4)

    @classmethod
    def check_paths(cls):
        if not os.path.exists(cls.PATH_TO_SETTINGS):
            open(cls.PATH_TO_SETTINGS, 'w').write(default_config.default_general_settings)
            logger.warning('Fill general local_files_helper!')
            exit()

        os.makedirs('Domains/DefaultDomain', exist_ok=True)
        if not os.path.exists('Domains/DefaultDomain/local_files_helper.json'):
            open('Domains/DefaultDomain/local_files_helper.json', 'w').write(default_config.default_domain_settings)
            logger.debug('DefaultDomain local_files_helper file created')

        if not os.path.exists('Domains/DefaultDomain/template.html'):
            open('Domains/DefaultDomain/template.html', 'w').write(default_config.default_domain_template)
            logger.debug('DefaultDomain template file created')

        os.makedirs('Images', exist_ok=True)

    @classmethod
    def update_credentials(cls, new_info):
        settings = cls.read_settings_file()
        settings['Secrets']['CREDENTIALS'] = new_info
        cls.write_settings_file(settings)


LocalFilesHelper.check_paths()
settings = LocalFilesHelper.read_settings_file()

# RESULT_DIRECTORY = local_files_helper['ResultsDirectory']
# RESULTS_DIRECTORY_TYPE = local_files_helper['ResultsDirectoryType']
# IMAGES_DIRECTORY = local_files_helper['ImagesDirectory']
# SAVE_IMAGES = local_files_helper['SaveImages']

secrets.oauth_client = settings['Secrets']['OAUTH_CLIENT']
secrets.monday_token = settings['Secrets']['MONDAY_TOKEN']
secrets.credentials = settings['Secrets'].get('CREDENTIALS')
secrets.callable_update_credentials = LocalFilesHelper.update_credentials
