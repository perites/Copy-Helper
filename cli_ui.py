import logging
import os
import platform
import traceback
from datetime import datetime

import questionary
from prompt_toolkit.styles import Style

from core import core

logger = logging.getLogger(__name__)


class CliUI:
    autocomplete_style = Style.from_dict({
        "completion-menu.completion": "bg:#444444 ansiwhite",
        "scrollbar.background": "bg:black",
        "scrollbar.button": "bg:black",
        "prompt": "bold ansiwhite",
    })

    @classmethod
    def start(cls):
        cls.clear_console()
        questionary.print('Welcome to copy-helper')
        while True:
            try:
                cls.main_cycle()
            except Exception as e:
                logger.critical(f'Unexpected Error: {e}')
                logger.debug(traceback.format_exc())
                retry = questionary.autocomplete(
                    'Press Enter to return to main page, or type "exit" to quit:',
                    choices=['exit'], ignore_case=True,
                    match_middle=True, style=cls.autocomplete_style).ask().strip().lower()
                if retry == 'exit':
                    core.exit()

    @classmethod
    def main_cycle(cls):

        menu_options = {
            'make-domain': cls.make_domain,
            'make-all': cls.make_all,
            'md': cls.make_domain,
            'ma': cls.make_all,
            'add-domain': cls.add_domain,
            # 'edit-domain':cls.edit_domain,
            'clear-cache': cls.clear_cache,
            'clear': cls.clear_console,
            'restart': core.restart_script,
            'exit': core.exit
        }

        menu_options_to_show = menu_options.copy()
        del menu_options_to_show['md']
        del menu_options_to_show['ma']
        questionary.print(f'Avalible options: {", ".join(menu_options_to_show)}')

        option = questionary.autocomplete(
            "Select an option:",
            choices=menu_options,
            validate=lambda val: val in menu_options,
            ignore_case=True,
            match_middle=True, style=cls.autocomplete_style

        ).ask()

        option_fun = menu_options.get(option)

        if option_fun:
            option_fun()

    @classmethod
    def make_all(cls):
        broadcast_date = questionary.text("Enter broadcast date:",
                                          default=f"{datetime.today().month}/{datetime.today().day}").ask().strip()
        if broadcast_date == 'back':
            return

        questionary.print(f'Staring making all domains : {", ".join(sorted(core.domains))}')

        domains_results = []
        for domain_name in sorted(core.domains):
            questionary.print(f'Making domain: {domain_name}')
            try:
                domain_results = core.make_domain(domain_name, broadcast_date, cls.get_str_copies, str_copies=None)
            except Exception as e:
                logger.error(f'Error while making domain {domain_name}. Details: {e}')
                logger.debug(traceback.format_exc())
                continue

            domains_results.append({'name': domain_name, 'results': domain_results})
            questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')

        questionary.print('======================')
        questionary.print('Finished making all domains')
        for domain_results in domains_results:
            questionary.print(f'Results for domain: {domain_results['name']}')
            for results in domain_results['results']:
                questionary.print(results)
            questionary.print('\n')

        questionary.print('======================')

    @classmethod
    def make_domain(cls):
        questionary.print(f'Domains : {", ".join(sorted(core.domains))}')

        choices = {**core.domains, 'back': ''}
        domain_name = questionary.autocomplete("Choose domain:",
                                               choices=choices,
                                               validate=lambda val: val in choices,
                                               ignore_case=True,
                                               match_middle=False,
                                               style=cls.autocomplete_style).ask()

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
        try:
            domain_results = core.make_domain(domain_name, broadcast_date, cls.get_str_copies, str_copies)
        except Exception as e:
            logger.error(f'Error while making domain {domain_name}. Details: {e}')
            logger.debug(traceback.format_exc())
            return

        questionary.print('======================')
        questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
        for results in domain_results:
            questionary.print(results)
        questionary.print('======================')

        # questionary.print(next(make_domain_results))
        # while True:
        #     try:

        #         sys.stdout.write(f'\033[2K\rStatus: {next(make_domain_results)}')
        #         sys.stdout.flush()
        #         time.sleep(2)

        #     except StopIteration as e:

        #         sys.stdout.write('\033[2K\rStatus: Done\n')
        #         sys.stdout.flush()
        #         questionary.print('======================')
        #         questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
        #         for results in e.value:
        #             questionary.print(results)
        #         questionary.print('======================')

        #         break

    @classmethod
    def get_str_copies(cls):
        str_copies = questionary.text(
            'Copies were not found, you can enter them manually (separated by space):').ask().strip().split(' ')

        return str_copies

    @classmethod
    def add_domain(cls):
        domain_name = questionary.text("Enter new domain name:").ask().strip()
        if domain_name == 'back':
            return
        core.create_new_domain(domain_name)

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

    #     options = dict_to_tree_string(json.load(open(f'Domains/{domain_name}/settings.json')))

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

    #     dict_obj = json.load(open(f'Domains/{domain_name}/settings.json'))

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
