import logging
import os
from io import BytesIO

from docx import Document
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from . import paths


class ServicesHelper:
    @classmethod
    def get_service(cls, service_name):
        match service_name:
            case "drive":
                version = "v3"

            case "sheets":
                version = "v4"

            case _:
                return

        service = build(service_name, version, credentials=cls.get_credentials(), cache_discovery=False)
        return service

    @staticmethod
    def get_credentials():
        creds = None

        scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets.readonly']

        path_to_credentials = paths.PATH_TO_FOLDER_SYSTEM_DATA + 'services_token.json'

        if os.path.exists(path_to_credentials):
            creds = Credentials.from_authorized_user_file(path_to_credentials, scopes)

        if creds:
            if creds.valid:
                return creds

            elif creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(path_to_credentials, 'w', encoding='utf-8') as file:
                    file.write(creds.to_json())
                return creds

        flow = InstalledAppFlow.from_client_secrets_file(paths.PATH_TO_FILE_OAUTH, scopes)
        creds = flow.run_local_server(port=0)

        with open(path_to_credentials, 'w', encoding='utf-8') as file:
            file.write(creds.to_json())

        return creds


class GoogleDrive:
    drive_service = ServicesHelper.get_service('drive')

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
    def get_files_from_folder(cls, folder_id):
        query = f'mimeType!="application/vnd.google-apps.folder" and trashed=false and "{folder_id}" in parents'
        fields = 'files(id, name, mimeType)'
        lift_folder_files = cls.execute_query(query, fields)

        return lift_folder_files

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

                content = cls.extract_text_from_docx(request.execute())

            case _:
                logging.warning(f'Unknown mime_type {mime_type}, returning None')
                return

        if not content:
            logging.warning(f'Could not get file content for file {file['name']} ')
            return ''

        return content

    @staticmethod
    def extract_text_from_docx(binary_data):
        doc_file = BytesIO(binary_data)
        doc = Document(doc_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text


class GoogleSheets:
    sheet_service = ServicesHelper.get_service('sheets')
    cache = {}

    @classmethod
    def get_new_data_from_range(cls, spreadsheet_id, range):
        sheet = cls.sheet_service.spreadsheets()

        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get('values', [])

        return values

    @classmethod
    def get_data_from_range(cls, spreadsheet_id, range):
        request = (spreadsheet_id, range)

        # values = cls.cache.get(request)
        # if values:
        #     return values

        values = cls.get_new_data_from_range(*request)

        cls.cache[request] = values

        return values

    @classmethod
    def get_table_index_of_value(cls, spreadsheet_id, value, range, is_row=True, strict=True):
        all_values = cls.get_data_from_range(spreadsheet_id, range)

        if is_row:
            all_values = all_values[0] if is_row else all_values
            value_index = all_values.index(value)
            # TODO add strict=False support
            return value_index

        else:
            for index, table_row in enumerate(all_values):

                data = table_row[0].strip() if table_row else None

                if strict:
                    if data == value:
                        return index
                elif data:
                    if value in data:
                        return index
