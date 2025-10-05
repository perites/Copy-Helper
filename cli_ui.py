import logging
import os
import platform
import traceback
from datetime import datetime

import questionary
from prompt_toolkit.styles import Style

from core import core
from local_files_helper import LocalFilesHelper

logger = logging.getLogger(__name__)


class CliUI:

    def __init__(self):
        self.autocomplete_style = Style.from_dict({
            "completion-menu.completion": "bg:#444444 ansiwhite",
            "scrollbar.background": "bg:black",
            "scrollbar.button": "bg:black",
            "prompt": "bold ansiwhite",
        })

        self.settings = LocalFilesHelper.sh.settings
        self.domains = LocalFilesHelper.dh.domains_dicts

        core.set_secrets(
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
                    core.exit()

    def main_cycle(self):

        menu_options = {
            'make-domain': self.make_domain,
            'md': self.make_domain,
            'add-domain': self.add_domain,
            # 'edit-domain':cls.edit_domain,
            'clear-cache': self.clear_cache,
            'clear': self.clear_console,
            'restart': core.restart_script,
            'exit': core.exit
        }

        menu_options_to_show = menu_options.copy()
        del menu_options_to_show['md']
        questionary.print(f'Avalible options: {", ".join(menu_options_to_show)}')

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

    def make_domain(self):
        domain_name, broadcast_date, str_copies = self.make_domain_gather_info()
        domain_dict = self.domains[domain_name]

        domain_bc_name = domain_dict['broadcast']['name']
        date = broadcast_date.replace('/', '.')

        copies_results = []
        try:
            manual_lifts_htmls = LocalFilesHelper.dh.get_lifts_htmls(str_copies, domain_bc_name, date)

            copies = core.make_domain(domain_dict, broadcast_date, str_copies, manual_lifts_htmls)
            max_len_str_copy = self.calc_max_len_str_copy(copies)
            for copy in copies:
                LocalFilesHelper.save_copy(copy, domain_bc_name, date)
                copies_results.append(self.get_copy_results(copy, max_len_str_copy))

        except Exception as e:
            logger.error(f'Error while making domain {domain_name}. Details: {e}')
            logger.debug(traceback.format_exc())
            return

        questionary.print('======================')
        questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
        for results in copies_results:
            questionary.print(results)
        questionary.print('======================')

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

        results = f'{warning_message}{str_rep_padding} : {copy_results} img {len(copy.lift_images)}'

        return results

    def add_domain(self):
        new_domain_name = questionary.text("Enter new domain name:").ask().strip()
        if new_domain_name == 'back':
            return

        questionary.print(f'Choose domain to copy from : {", ".join(sorted(self.domains))}')
        choices = {**core.domains, 'back': '', '': ''}
        template_domain_name = questionary.autocomplete("Template domain:",
                                                        choices=list(choices.keys()),
                                                        validate=lambda val: val in choices,
                                                        ignore_case=True,
                                                        match_middle=False,
                                                        style=self.autocomplete_style).ask()

        if template_domain_name == 'back':
            return

        LocalFilesHelper.dh.create_new_domain(new_domain_name, template_domain_name)

    @classmethod
    def clear_cache(cls):
        option = questionary.text("Specify offer to clear cache:").ask().strip()
        if option == 'back':
            return
        core.clear_cache(option)

    @staticmethod
    def clear_console():
        current_os = platform.system()
        if current_os == "Windows":
            os.system('cls')
        else:
            print("\033[H\033[J\033[3J", end="", flush=True)

    # @classmethod
    # def edit_domain(cls):
    #     def dict_to_tree_string(d, indent=0):
    #         tree_strings = []
    #         for key, value in d.items():
    #             tree_strings.append("  " * indent + str(key))
    #             if isinstance(value, dict):
    #                 tree_strings.extend(dict_to_tree_string(value, indent + 1))
    #             else:
    #                 tree_strings.append("  " * (indent + 1) + str(value))
    #         return tree_strings

    #     questionary.print(f'Domains : {", ".join(sorted(core.domains))}')

    #     choices = {**core.domains, 'back': ''}
    #     domain_name = questionary.autocomplete("Choose domain:",
    #         choices=choices,
    #         validate=lambda val: val in choices,
    #         ignore_case=True,
    #         match_middle=False,
    #         style=cls.autocomplete_style).ask()

    #     if domain_name=='back':
    #         return

    #     options = dict_to_tree_string(json.load(open(f'Domains/{domain_name}/local_files_helper.json')))

    #     selected = questionary.select(
    #         "Select an item from the tree:",
    #         choices=options
    #     ).ask()

    #     print(f"You selected: {selected}")

    # @classmethod
    # def edit_domain(cls):
    #     questionary.print(f'Domains : {", ".join(sorted(core.domains))}')

    #     choices = {**core.domains, 'back': ''}
    #     domain_name = questionary.autocomplete("Choose domain:",
    #         choices=choices,
    #         validate=lambda val: val in choices,
    #         ignore_case=True,
    #         match_middle=False,
    #         style=cls.autocomplete_style).ask()

    #     if domain_name=='back':
    #         return

    #     dict_obj = json.load(open(f'Domains/{domain_name}/local_files_helper.json'))

    #     new_domain = cls.edit_dict(dict_obj)

    #     print(new_domain)

    # @classmethod
    # def edit_dict(cls, dict_obj):

    #      #list(fil(dict_obj.keys()))
    #     choices = []
    #     for k, v in dict_obj.items():
    #         if isinstance(v, dict):
    #             choices.append(k)
    #         else:
    #             choices.append(f'{k} : {v}')

    #     answer = questionary.select("Select a key to edit", choices=choices).ask()
    #     key = answer.split(' : ')[0]

    #     # key = questionary.select("Select a key to edit", choices=dict_obj).ask()
    #     value = dict_obj[key]
    #     if isinstance(value, dict):
    #         # Recursive editing
    #         dict_obj[key] = cls.edit_dict(dict_obj[key])
    #     else:
    #         questionary.print(f"Enter new value for {key}, currently: {value}")
    #         new_val = questionary.text('New value:').ask().strip()
    #         dict_obj[key] = new_val

    #     return dict_obj
