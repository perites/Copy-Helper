import logging

from . import tools
import platform
import subprocess
import hashlib
import os
import uuid


class GeneralSettings:
    broadcast_id: str
    parent_folder_id: str
    result_directory: str
    domains_short_names: dict
    machine_id: str
    priority_products_table_id: str

    @classmethod
    def set_settings(cls):
        logging.info('Parsing settings')
        general_setting_path = 'Settings/General-Settings.json'

        settings_dict = tools.read_json_file(general_setting_path)

        cls.broadcast_id = settings_dict["YourTeamBroadcastSheetID"]
        cls.parent_folder_id = settings_dict["FolderWithPartners"]
        cls.result_directory = settings_dict["DirectoryToStoreResults"]
        cls.domains_short_names = settings_dict["DomainsShortNames"]
        cls.priority_products_table_id = settings_dict['PriorityProductsTableId']

        cls.machine_id = cls.get_unique_machine_id()

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
