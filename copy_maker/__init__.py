import logging
import os

import default_config


def check_files():
    if not os.path.exists('copy_maker/offers_info_cache.json'):
        open('copy_maker/offers_info_cache.json', 'w').write('{}')

    if not os.path.exists('copy_maker/secrets.json'):
        open('copy_maker/secrets.json', 'w').write(default_config.default_secret_file)
        logging.warning('Fill secrets file!')
        exit()


def import_modules():
    from . import domain
    from . import offer
    from . import styles_helper


check_files()
import_modules()
