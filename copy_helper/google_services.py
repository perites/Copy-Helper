import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from . import exceptions
from . import settings
from . import tools


class ServicesHelper:
    @classmethod
    def get_service(cls, service_name):
        match service_name:
            case "drive":
                scopes = ['https://www.googleapis.com/auth/drive']
                version = "v3"

            case "sheets":
                scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
                version = "v4"

            case _:
                logging.warning(f'No information was found for this service {service_name} returning None')
                return

        service = build(service_name, version, credentials=cls.get_credentials(scopes), cache_discovery=False)
        return service

    @staticmethod
    def get_credentials(scopes):
        creds = None
        path_to_credentials = 'SystemData/services_token.json'

        if os.path.exists(path_to_credentials):
            creds = Credentials.from_authorized_user_file(path_to_credentials, scopes)

        if creds:
            if creds.valid:
                return creds

            elif creds.expired and creds.refresh_token:
                creds.refresh(Request())
                tools.FileHelper.write_to_file(path_to_credentials, creds.to_json())
                return creds

        flow = InstalledAppFlow.from_client_secrets_file('SystemData/OAuth 2.0 Client ID.json', scopes)
        creds = flow.run_local_server(port=0)

        tools.FileHelper.write_to_file(path_to_credentials, creds.to_json())

        return creds


class GoogleDrive:
    drive_service = ServicesHelper.get_service('drive')

    @classmethod
    def get_offer_general_folder(cls, offer_name):
        for partner_folder in cls.get_folders_of_folder(settings.GeneralSettings.parent_folder_id):
            partner_folder_id = partner_folder['id']
            offer_general_folder = cls.get_folder_by_name(offer_name, partner_folder_id, False)
            if offer_general_folder:
                return offer_general_folder

        raise exceptions.NoPartnersWithOffer(offer_name)

    @classmethod
    def get_offer_folder_id(cls, offer_name):
        offer_general_folder = cls.get_offer_general_folder(offer_name)
        offer_folder_id = cls.get_offer_folder_id_from_general(offer_general_folder)
        return offer_folder_id

    @classmethod
    def get_offer_folder_id_from_general(cls, offer_general_folder):
        for general_folder in cls.get_folders_of_folder(offer_general_folder['id']):
            if general_folder['name'].strip().lower().startswith("html+sl"):
                offer_folder_id = general_folder['id']

                return offer_folder_id

        raise Exception(
            f"No 'HTML+SL' folder was found in General Offer Folder (name:{offer_general_folder['name']})")

    @classmethod
    def execute_query(cls, query, fields='files(id, name)'):
        result = cls.drive_service.files().list(q=query, fields=fields,
                                                includeItemsFromAllDrives=True,
                                                supportsAllDrives=True).execute()
        result = result.get('files', [])

        return result

    @classmethod
    def get_folder_by_name(cls, folder_name, parent_folder_id, strict=True):
        name_part = "name=" if strict else "name contains "

        query = f"{name_part}'{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_folder_id}' in parents"
        folders = cls.execute_query(query)
        return folders[0] if folders else None

    @classmethod
    def get_folders_of_folder(cls, parent_folder_id):
        query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_folder_id}' in parents"
        folders = cls.execute_query(query)
        return folders

    @classmethod
    def get_file_content(cls, file):
        file_id = file['id']
        mime_type = file['mimeType']
        match mime_type:
            case 'text/html':
                request = cls.drive_service.files().get_media(fileId=file_id)
                content = request.execute().decode('utf-8')

            case 'application/vnd.google-apps.document':
                request = cls.drive_service.files().export_media(fileId=file_id,
                                                                 mimeType='text/plain')

                content = request.execute().decode('utf-8')

            case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                request = cls.drive_service.files().get_media(fileId=file_id)

                content = tools.FileHelper.extract_text_from_docx(request.execute())

            case _:
                logging.warning(f'Unknown mime_type {mime_type}, returning None')
                return

        return content


class GoogleSheets:
    sheet_service = ServicesHelper.get_service('sheets')
    cache = {}

    @classmethod
    def get_new_data_from_range(cls, spreadsheet_id, range):
        sheet = cls.sheet_service.spreadsheets()

        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get('values', [])

        # print(values[0])

        return values

    @classmethod
    def get_data_from_range(cls, spreadsheet_id, range):
        request = (spreadsheet_id, range)

        values = cls.cache.get(request)
        if values:
            return values

        values = cls.get_new_data_from_range(*request)

        cls.cache[request] = values

        return values

    @classmethod
    def get_table_index_of_value(cls, spreadsheet_id, value, range, is_row=True):
        all_values = cls.get_data_from_range(spreadsheet_id, range)

        if is_row:
            all_values = all_values[0] if is_row else all_values
            value_index = all_values.index(value)

            return value_index

        else:
            for index, table_row in enumerate(all_values):

                data = table_row[0] if table_row else None
                if data == value:
                    return index
