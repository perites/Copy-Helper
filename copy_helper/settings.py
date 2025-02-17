import logging

from . import exceptions
from . import tools


class GeneralSettings:
    broadcast_id: str
    parent_folder_id: str
    result_directory: str
    domains_short_names: dict
    clear_old_copies: bool

    @classmethod
    def set_settings(cls):
        logging.info('Setting up setting')
        general_setting_path = 'Settings/General-Setting.json'

        settings_dict = cls.parse_general_setting_file(general_setting_path)
        cls.validate_settings_dict(settings_dict)

        cls.broadcast_id = settings_dict.get("Broadcast")
        cls.parent_folder_id = settings_dict.get("FolderWithPartners")
        cls.result_directory = settings_dict.get("DirectoryToStoreResults")
        cls.domains_short_names = settings_dict.get("DomainsShortNames")
        cls.clear_old_copies = True if settings_dict.get('ClearOldCopies') == 'yes' else False

    @staticmethod
    def parse_general_setting_file(general_setting_path):
        settings_dict = tools.FileHelper.read_json_data(general_setting_path)
        if not settings_dict:
            raise exceptions.SettingsError(
                f'General-Setting file missing or can`t be parsed. Searching at {general_setting_path}')

        return settings_dict

    @staticmethod
    def validate_settings_dict(settings_dict):
        for setting_name in ['Broadcast', 'FolderWithPartners', 'DirectoryToStoreResults']:
            if not settings_dict.get(setting_name):
                raise exceptions.SettingsError(f'Missing setting {setting_name}')


class DomainSettings:
    pass
