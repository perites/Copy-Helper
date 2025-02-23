import hashlib
import logging
import os
import platform
import subprocess
import uuid

from . import tools

GENERAL_SETTINGS_PATH = 'Settings/General-Settings.json'


class GeneralSettings:
    broadcast_id: str
    parent_folder_id: str
    result_directory: str
    domains_short_names: dict
    machine_id: str
    priority_products_table_id: str
    default_style_settings: dict
    anti_spam_replacements: dict
    save_image_path: str
    logging_level: str

    @classmethod
    def set_settings(cls):
        if not os.path.exists(GENERAL_SETTINGS_PATH):
            logging.info('Setting Folder was not found, creating new')
            cls.create_settings()

        logging.info('Parsing settings')
        settings_dict = tools.read_json_file(GENERAL_SETTINGS_PATH)

        cls.broadcast_id = settings_dict["YourTeamBroadcastSheetID"]
        cls.parent_folder_id = settings_dict["FolderWithPartners"]
        cls.result_directory = settings_dict["DirectoryToStoreResults"]
        cls.domains_short_names = settings_dict["DomainsShortNames"]
        cls.priority_products_table_id = settings_dict['PriorityProductsTableId']
        cls.default_style_settings = settings_dict['DefaultStyles']
        cls.anti_spam_replacements = settings_dict['AntiSpamReplacements']
        cls.machine_id = cls.get_unique_machine_id()
        cls.save_image_path = settings_dict['AutoImagesSavePath']
        cls.logging_level = settings_dict['InformationLevel']

    @classmethod
    def create_settings(cls):
        settings_folder_path = os.path.dirname(GENERAL_SETTINGS_PATH)
        os.makedirs(settings_folder_path)

        tools.write_json_file(GENERAL_SETTINGS_PATH, {
            "YourTeamBroadcastSheetID": "",
            "FolderWithPartners": "1-WFEkKNjVjaJDNt2XKBeJhpIQUviBVim",
            "PriorityProductsTableId": "1e40khWM1dKTje_vZi4K4fL-RA8-D6jhp2wmZSXurQH0",
            "DirectoryToStoreResults": "",
            "InformationLevel": "All",
            "AutoImagesSavePath": "",
            "DomainsShortNames": {
                "DOMAIN_ABR": "DomainNameAsInBroadcast"
            },
            "DefaultStyles": {
                "FontSize": "21px",
                "FontFamily": "Roboto",
                "LinksColor": "#2402fb",
                "SidePadding": "30px",
                "UpperDownPadding": "10px",
                "AddAfterPriorityBlock": "<br><br>",
                "PriorityFooterUrlTemplate": "<b><a target=\"_blank\" href=\"PRIORITY_FOOTER_URL\" style=\"text-decoration: underline; color: #ffffff;\">PRIORITY_FOOTER_TEXT_URL</a></b>",
                "ImageBlock": "<table align=\"center\"><tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr>\n<tr>\n  <td class=\"img-bg-block\" align=\"center\">\n    <a href=\"urlhere\" target=\"_blank\">\n      <img alt=\"ALT_TEXT\" height=\"auto\" src=\"IMAGE_URL\" style=\"border:0;display:block;outline:none;text-decoration:none;height:auto;width:100%;max-width: 550px;font-size:13px;\" width=\"280\" />\n        </a>\n  </td>\n</tr>\n<tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr></table>"
            },
            "AntiSpamReplacements": {
                "A": "А",
                "E": "Е",
                "I": "І",
                "O": "О",
                "P": "Р",
                "T": "Т",
                "H": "Н",
                "K": "К",
                "X": "Х",
                "C": "С",
                "B": "В",
                "M": "М",
                "e": "е",
                "y": "у",
                "i": "і",
                "o": "о",
                "a": "а",
                "x": "х",
                "c": "с",
                "%": "％",
                "$": "＄"
            }
        })

        cls.create_new_domain()

    @classmethod
    def create_new_domain(cls, domain_name='DomainNameAsInBroadcast'):
        if not domain_name:
            logging.warning('DomainName cant be empty')
            return

        settings_folder_path = os.path.dirname(GENERAL_SETTINGS_PATH)
        domain_folder_path = settings_folder_path + f'/Domains/{domain_name}/'
        os.makedirs(domain_folder_path, exist_ok=True)
        tools.write_json_file(domain_folder_path + f'settings.json', {
            "Name": f"{domain_name}",
            "PageInBroadcast": "",
            "AntiSpam": False,
            "TrackingLinkInfo": {
                "Type": "",
                "Start": "",
                "End": ""
            },
            "CustomPriorityUnsubLinkInfo": {
                "Type": "",
                "Start": "",
                "End": ""
            },
            "StylesSettings": {

            }
        })

        with open(domain_folder_path + 'template.html', 'w', encoding='utf-8') as file:
            file.write(
                'put html template design here <br> put <<<-COPY_HERE->>> where copy need to be <br> put <<<-PRIORITY_FOOTER_HERE->>> where priority footer will be')

        logging.info(f'Created new domain {domain_name}')

    @staticmethod
    def get_unique_machine_id():
        os_name = platform.system()

        try:
            if os_name == "Windows":
                machine_id = subprocess.check_output(
                    'reg query HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid',
                    shell=True
                ).decode().strip().split()[-1]

            elif os_name == "Linux":
                with open("/etc/machine-id", "r") as f:
                    machine_id = f.read().strip()

            elif os_name == "Darwin":  # macOS
                machine_id = subprocess.check_output(
                    "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
                    shell=True
                ).decode().strip().split('"')[-2]

            else:
                machine_id = os.popen("uuidgen").read().strip()

        except Exception as e:
            logging.warning(f'Could not get secure machine id')
            machine_id = uuid.getnode()

        hashed = hashlib.sha256(machine_id.encode()).hexdigest()
        short_id = str(int(hashed[:16], 16))[:13]

        return short_id
