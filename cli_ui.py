import logging
import traceback

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
            'add-domain': cls.add_domain,
            'clear-cache': cls.clear_cache,
            'clear': cls.clear_console,
            'restart': core.restart_script,
            'exit': core.exit
        }

        questionary.print(f'Avalible options : {", ".join(menu_options.keys())}')
        option = questionary.autocomplete(
            "Select an option:",
            choices=list(menu_options.keys()),
            validate=lambda val: val in list(menu_options.keys()),
            ignore_case=True,
            match_middle=True, style=cls.autocomplete_style

        ).ask()

        option_fun = menu_options.get(option)

        if option_fun:
            option_fun()

    @classmethod
    def make_domain(cls):
        domain_name = questionary.select("Choose domain", choices=core.domains).ask()
        broadcast_date = questionary.text("Enter broadcast date:").ask().strip()

        str_copies = questionary.text("Enter copies (press enter to fetch form broadcast):").ask().strip()
        str_copies = str_copies.split(' ') if str_copies else None

        copies_results = core.make_domain(domain_name, broadcast_date, cls.get_str_copies, str_copies)

        questionary.print('======================')
        questionary.print(f'Finished making domain {domain_name} for date {broadcast_date}')
        for results in copies_results:
            questionary.print(results)
        questionary.print('======================')

    @classmethod
    def get_str_copies(cls):
        str_copies = questionary.text(
            'Copies were not found, you can enter them manually (separated by space):').ask().strip().split(' ')

        return str_copies

    @classmethod
    def add_domain(cls):
        domain_name = questionary.text("Enter new domain name:").ask().strip()
        core.create_new_domain(domain_name)

    @classmethod
    def clear_cache(cls):
        option = questionary.text("Specify offer to clear cache:").ask().strip()
        core.clear_cache(option)

    @staticmethod
    def clear_console():
        print("\033[H\033[J\033[3J", end="")

    # @classmethod
    # def edit_dict(cls, dict_obj):
    #
    #     keys = list(dict_obj.keys())
    #     key = questionary.select("Select a key to edit", choices=keys).ask()
    #
    #     value = dict_obj[key]
    #     if isinstance(value, dict):
    #         # Recursive editing
    #         dict_obj[key] = cls.edit_dict(dict_obj[key])
    #     else:
    #         new_val = questionary.text(f"Enter new value for {key} (currently: {value})").ask().strip()
    #         dict_obj[key] = new_val
    #
    #     return dict_obj
