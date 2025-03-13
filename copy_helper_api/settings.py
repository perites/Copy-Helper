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
            broadcast_id=user_settings_dict["yourTeamBroadcastSheetID"],
            parent_folder_id=user_settings_dict.get("FolderWithPartners") or '1-WFEkKNjVjaJDNt2XKBeJhpIQUviBVim',
            priority_products_table_id=user_settings_dict.get(
                'PriorityProductsTableId') or '1e40khWM1dKTje_vZi4K4fL-RA8-D6jhp2wmZSXurQH0',
            default_style_settings=user_settings_dict['defaultStyles'],
            anti_spam_replacements=user_settings_dict['antiSpamReplacements'],
        )
