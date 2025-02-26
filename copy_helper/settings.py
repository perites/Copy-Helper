import hashlib
import logging
import os
import platform
import subprocess
import uuid

from . import paths
from . import tools


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
    result_directory_type: str

    @classmethod
    def set_settings(cls):

        logging.debug('Parsing settings')
        settings_dict = tools.read_json_file(paths.PATH_TO_FILE_GENERAL_SETTINGS)

        cls.broadcast_id = settings_dict["YourTeamBroadcastSheetID"]
        cls.parent_folder_id = settings_dict["FolderWithPartners"]
        cls.result_directory = settings_dict["DirectoryToStoreResults"]
        cls.result_directory_type = settings_dict['ResultDirectoryType']
        cls.domains_short_names = settings_dict["DomainsShortNames"]
        cls.priority_products_table_id = settings_dict['PriorityProductsTableId']
        cls.default_style_settings = settings_dict['DefaultStyles']
        cls.anti_spam_replacements = settings_dict['AntiSpamReplacements']
        cls.machine_id = cls.get_unique_machine_id()
        cls.save_image_path = settings_dict['AutoImagesSavePath']
        cls.logging_level = settings_dict['InformationLevel']

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

        except Exception:
            logging.warning(f'Could not get secure machine id')
            machine_id = uuid.getnode()

        hashed = hashlib.sha256(machine_id.encode()).hexdigest()
        short_id = str(int(hashed[:16], 16))[:13]

        return short_id


GeneralSettings.set_settings()
