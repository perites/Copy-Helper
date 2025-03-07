import dataclasses
import logging

from flask import g


@dataclasses.dataclass
class UserSettings:
    broadcast_id: str
    parent_folder_id: str
    priority_products_table_id: str
    default_style_settings: dict
    anti_spam_replacements: dict

    @classmethod
    def set_settings(cls, user_settings_dict):
        logging.debug('Parsing settings')
        g.user_settings = cls(
            broadcast_id=user_settings_dict["YourTeamBroadcastSheetID"],
            parent_folder_id=user_settings_dict["FolderWithPartners"],
            priority_products_table_id=user_settings_dict['PriorityProductsTableId'],
            default_style_settings=user_settings_dict['DefaultStyles'],
            anti_spam_replacements=user_settings_dict['AntiSpamReplacements'],
        )
