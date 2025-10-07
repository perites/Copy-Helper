import logging
import os
import platform
import traceback
from datetime import datetime

import questionary
from prompt_toolkit.styles import Style

from .files_helper import LocalFilesHelper

logger = logging.getLogger(__name__)


class CliUI:
    def __init__(self, core):
        self.autocomplete_style = Style.from_dict({
            "completion-menu.completion": "bg:#444444 ansiwhite",
            "scrollbar.background": "bg:black",
            "scrollbar.button": "bg:black",
            "prompt": "bold ansiwhite",
        })
        self.core = core
        self.settings = LocalFilesHelper.sh.settings
        self.domains = LocalFilesHelper.dh.domains_dicts

        self.core.set_secrets(
            self.settings['Secrets']['OAUTH_CLIENT'],
            self.settings['Secrets']['MONDAY_TOKEN'],
            self.settings['Secrets'].get('CREDENTIALS'),
            LocalFilesHelper.sh.update_credentials
        )

    def start(self):
        self.clear_console()
        questionary.print('Welcome to copy-helper')
        while True:
            try:
                self.main_cycle()
            except Exception as e:
                logger.critical(f'Unexpected Error: {e}')
                logger.debug(traceback.format_exc())
                retry = questionary.autocomplete(
                    'Press Enter to return to main page, or type "exit" to quit:',
                    choices=['exit'], ignore_case=True,
                    match_middle=True, style=self.autocomplete_style).ask().strip().lower()
                if retry == 'exit':
                    self.core.exit()

    def main_cycle(self):

        menu_options = {
            'make-domain': self.make_one_domain,
            'make-all': self.make_all,
            'md': self.make_one_domain,
            'ma': self.make_all,
            'add-domain': self.add_domain,
            # 'edit-domain':cls.edit_domain,
            'clear-cache': self.clear_cache,
            'clear': self.clear_console,
            'restart': self.core.restart_script,
            'exit': self.core.exit
        }

        menu_options_to_show = menu_options.copy()
        del menu_options_to_show['md']
        del menu_options_to_show['ma']

        questionary.print(f'Available options: {", ".join(menu_options_to_show)}')

        option = questionary.autocomplete(
            "Select an option:",
            choices=list(menu_options.keys()),
            validate=lambda val: val in menu_options,
            ignore_case=True,
            match_middle=True, style=self.autocomplete_style

        ).ask()

        option_fun = menu_options.get(option)

        if option_fun:
            option_fun()

    def make_one_domain(self):
        domain_name, broadcast_date, str_copies = self.make_domain_gather_info()
        copies_results = self.make_domain(domain_name, broadcast_date, str_copies)

        questionary.print('======================')
        questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
        for results in copies_results:
            questionary.print(results)
        questionary.print('======================')
        questionary.print('')

    def make_domain(self, domain_name, broadcast_date, str_copies):
        domain_dict = self.domains[domain_name]

        domain_bc_name = domain_dict['broadcast']['name']
        date = broadcast_date.replace('/', '.')

        copies_results = []
        try:

            if not str_copies:
                str_copies = self.core.get_domain_copies(domain_dict, broadcast_date)

            if not str_copies:
                return []

            manual_lifts_htmls = LocalFilesHelper.dh.get_lifts_htmls(str_copies, domain_bc_name, date)

            copies = self.core.make_domain(domain_dict, str_copies, manual_lifts_htmls)
            max_len_str_copy = self.calc_max_len_str_copy(copies)
            for copy in copies:
                try:
                    LocalFilesHelper.save_copy(copy, domain_bc_name, date)
                    copies_results.append(self.get_copy_results(copy, max_len_str_copy))
                except Exception as e:
                    logger.error(f'Error while saving copy {copy.str_rep}. Details: {e}')
                    logger.debug(traceback.format_exc())

            return copies_results

        except Exception as e:
            logger.error(f'Error while making domain {domain_name}. Details: {e}')
            logger.debug(traceback.format_exc())
            return []

    def make_domain_gather_info(self):
        questionary.print(f'Domains : {", ".join(sorted(self.domains))}')

        choices = {**self.domains, 'back': ''}
        domain_name = questionary.autocomplete("Choose domain:",
                                               choices=list(choices.keys()),
                                               validate=lambda val: val in choices,
                                               ignore_case=True,
                                               match_middle=False,
                                               style=self.autocomplete_style).ask()

        if domain_name == 'back':
            return

        broadcast_date = questionary.text("Enter broadcast date:",
                                          default=f"{datetime.today().month}/{datetime.today().day}").ask().strip()
        if broadcast_date == 'back':
            return

        str_copies = questionary.text("Enter copies (press enter to fetch form broadcast):").ask().strip()
        if str_copies == 'back':
            return

        str_copies = str_copies.split(' ') if str_copies else None

        return domain_name, broadcast_date, str_copies

    def make_all(self):
        broadcast_date = questionary.text("Enter broadcast date:",
                                          default=f"{datetime.today().month}/{datetime.today().day}").ask().strip()
        if broadcast_date == 'back':
            return

        questionary.print(f'Staring making all domains : {", ".join(sorted(self.domains))}')

        domains_results = []
        for domain_name in sorted(self.domains):
            questionary.print(f'Making domain: {domain_name}')

            copies_results = self.make_domain(domain_name, broadcast_date, None)
            domains_results.append({'name': domain_name, 'results': copies_results})

            questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
            questionary.print('')

        questionary.print('======================')
        questionary.print('Finished making all domains')
        for domain_results in domains_results:
            questionary.print(f'Results for domain: {domain_results['name']}')
            for results in domain_results['results']:
                questionary.print(results)
            questionary.print('')
        questionary.print('======================')

    @staticmethod
    def calc_max_len_str_copy(copies):
        max_len_str_copy = 0
        for copy in copies:
            if len(copy.str_rep) > max_len_str_copy:
                max_len_str_copy = len(copy.str_rep)

        return max_len_str_copy

    @staticmethod
    def get_copy_results(copy, max_len_str_copy):
        warning_message = 'Warning!:' if not copy.results()['link'] else ''
        str_rep_padding = copy.str_rep + (' ' * (max_len_str_copy - len(copy.str_rep)))

        copy_results = " | ".join(
            [f'{name} : {'+' if raw_result else '-'}' for name, raw_result in copy.results().items()])

        results = f'{warning_message}{str_rep_padding} : {copy_results} | img {len(copy.lift_images)}'

        return results

    def add_domain(self):
        new_domain_name = questionary.text("Enter new domain name:").ask().strip()
        if new_domain_name == 'back':
            return

        questionary.print(
            f'Choose domain to copy from : {", ".join(sorted(self.domains))} or press Enter to copy from Default')
        choices = {**self.domains, 'back': '', '': ''}
        template_domain_name = questionary.autocomplete("Template domain:",
                                                        choices=list(choices.keys()),
                                                        ignore_case=True,
                                                        match_middle=False,
                                                        style=self.autocomplete_style).ask()

        if template_domain_name == 'back':
            return

        LocalFilesHelper.dh.create_new_domain(new_domain_name, template_domain_name)

    def clear_cache(self):
        option = questionary.text("Specify offer to clear cache:").ask().strip()
        if option == 'back':
            return
        self.core.clear_cache(option)

    @staticmethod
    def clear_console():
        current_os = platform.system()
        if current_os == "Windows":
            os.system('cls')
        else:
            print("\033[H\033[J\033[3J", end="", flush=True)
