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
    def make_domain(domain_dict, broadcast_date, str_copies, manual_lift_html):
        try:
            domain = dmn.Domain(domain_dict)
        except Exception as e:
            logger.error(f'Error parsing domain dict')
            logger.debug(traceback.format_exc())
            return

        if not str_copies:
            domain.get_copies_from_broadcast(broadcast_date)

        logger.info(f'Processing copies: {", ".join(str_copies)}')

        made_copies = []
        for str_copy in str_copies:
            try:
                copy = domain.make_copy(str_copy, manual_lift_html[str_copy])
                made_copies.append(copy)
            except Exception as e:
                logger.error(f'Error while making copy {str_copy}. Details : {e}')
                logger.debug(traceback.format_exc())

        return made_copies
