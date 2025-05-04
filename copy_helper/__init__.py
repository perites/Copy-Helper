import json
import logging
import os

from . import domain
from . import offer
from . import styles_helper

if not os.path.exists('copy_helper/offers_info_cache.json'):
    open('copy_helper/offers_info_cache.json', 'w').write('{}')

if not os.path.exists('copy_helper/secrets.json'):
    open('copy_helper/secrets.json', 'w').write(json.dumps({
        "MONDAY_TOKEN": "",
        "OAUTH_CLIENT": ""
    }))

    logging.warning('Fill secrets file!')
    exit()
