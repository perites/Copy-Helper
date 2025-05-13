import datetime
import logging
import traceback

import logger
from core import core


class CliUI:
    @classmethod
    def start(cls):
        cls.clear_console()
        logging.info('Welcome to copy-helper')
        logging.info('Loading...')
        while True:
            try:
                cls.main_cycle()
                raise Exception
            except Exception as e:
                logging.critical(f'Unexpected Error: {e}')
                logging.debug(traceback.format_exc())
                logging.info('Press Enter to return to main page, or type "exit" to quit: ')
                retry = cls.cinput().strip().lower()
                if retry == 'exit':
                    return

    @staticmethod
    def cinput():
        prefix = f'{datetime.datetime.now():{logger.datefmt}} [INPUT] > '
        return input(prefix).strip()

    @staticmethod
    def clear_console():
        print("\033[H\033[J\033[3J", end="")

    @classmethod
    def get_str_copies(cls):
        logging.info('Copies were not found, you can enter them manually (separated by space)')
        str_copies = cls.cinput().split(' ')
        return str_copies

    @classmethod
    def main_cycle(cls):
        logging.info('Type what you want to do:')
        logging.info('make-domain (md) | clear-cache | add-domain | clear | restart | exit')
        action = cls.cinput()
        match action:
            case 'exit':
                core.exit()

            case 'restart':
                core.restart_script()

            case 'clear':
                cls.clear_console()

            case 'add-domain':
                logging.info('Enter new domain name')
                domain_name = cls.cinput()
                core.create_new_domain(domain_name)

            case 'clear-cache':
                logging.info('Specify offer to clear cache')
                option = cls.cinput()
                core.clear_cache(option)

            case 'make-domain' | 'md':
                logging.info('To make domain, enter <domain-name> <date>')
                logging.info(f'Added domains : {', '.join(sorted(core.domains.keys()))}')

                user_input = cls.cinput().strip().split(' ')
                domain_name, broadcast_date, *str_copies = user_input

                core.make_domain(domain_name, broadcast_date, cls.get_str_copies, str_copies)
