import logging
import os
import sys
import traceback

from . import copy
from . import domain as dmn
from . import google_services
from . import offer
from . import secrets

logger = logging.getLogger(__name__)


class Core:
    @staticmethod
    def set_secrets(oauth_client, monday_token, credentials, callable_update_credentials):
        secrets.Secrets.oauth_client = oauth_client
        secrets.Secrets.monday_token = monday_token
        secrets.Secrets.credentials = credentials
        secrets.Secrets.callable_update_credentials = callable_update_credentials

        google_services.ServicesHelper.build_services()

    @staticmethod
    def exit():
        exit()

    @staticmethod
    def restart_script():
        logger.debug('Restarting')
        os.execl(sys.executable, sys.executable, *sys.argv)

    @staticmethod
    def clear_cache(offer_name):
        offer.OffersCacheJSON.update_offer(offer_name, {})

    @staticmethod
    def make_domain(domain_dict, str_copies, manual_lift_html):
        try:
            domain = dmn.Domain(domain_dict)
        except Exception as e:
            logger.error(f'Error parsing domain dict')
            logger.debug(traceback.format_exc())
            return

        made_copies = []
        for str_copy in str_copies:
            copy = domain.make_copy(str_copy, manual_lift_html.get(str_copy))
            if copy:
                made_copies.append(copy)

        return made_copies

    @staticmethod
    def get_domain_copies(domain_dict, broadcast_date):
        try:
            domain = dmn.Domain(domain_dict)
        except Exception as e:
            logger.error(f'Error parsing domain dict')
            logger.debug(traceback.format_exc())
            return []

        str_copies = domain.get_copies_from_broadcast(broadcast_date)
        if str_copies:
            logger.info(f'Found copies: {", ".join(str_copies)}')
        else:
            logger.warning(f'No copies found')

        return str_copies
