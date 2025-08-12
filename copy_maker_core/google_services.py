import json
import logging
from io import BytesIO

from docx import Document
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import secrets

logger = logging.getLogger(__name__)


class ServicesHelper:

    @staticmethod
    def get_credentials():
        creds = None

        scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets.readonly']

        if secrets.CREDENTIALS:
            creds = Credentials.from_authorized_user_info(secrets.CREDENTIALS, scopes)

        if creds:
            if creds.valid:
                return creds

            elif creds.expired and creds.refresh_token:
                creds.refresh(Request())

                secrets.update_credentials(json.loads(creds.to_json()))
                return creds

        flow = InstalledAppFlow.from_client_config(secrets.OAUTH_CLIENT, scopes)
        creds = flow.run_local_server(port=0)

        secrets.update_credentials(json.loads(creds.to_json()))

        return creds


class GoogleDrive:
    drive_service = build('drive', 'v3', credentials=ServicesHelper.get_credentials(), cache_discovery=False)

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
                logger.warning(f'Unknown mime_type {mime_type}, returning None')
                return

        if not content:
            logger.warning(f'Could not get file content for file {file['name']} ')
            return ''

        return content

    @staticmethod
    def extract_text_from_docx(binary_data):
        doc_file = BytesIO(binary_data)
        doc = Document(doc_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text


class GoogleSheets:
    sheet_service = build('sheets', 'v4', credentials=ServicesHelper.get_credentials(), cache_discovery=False)
    cache = {}

    @classmethod
    def get_new_data_from_range(cls, spreadsheet_id, range):
        sheet = cls.sheet_service.spreadsheets()

        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get('values', [])

        return values

    @classmethod
    def get_data_from_range(cls, spreadsheet_id, range, use_cache=False):
        request = (spreadsheet_id, range)

        values = cls.cache.get(request)
        if values and use_cache:
            return values

        values = cls.get_new_data_from_range(*request)

        cls.cache[request] = values

        return values

    @classmethod
    def get_table_index_of_value(cls, spreadsheet_id, value, range, is_row=True, strict=True):
        all_values = cls.get_data_from_range(spreadsheet_id, range, use_cache=True)

        if is_row:
            all_values = all_values[0] if is_row else all_values
            if strict:
                index = all_values.index(value)
                return index
            else:
                for index, data in enumerate(all_values):
                    data = data.strip() if data else None
                    if value in data:
                        return index

        else:
            for index, table_row in enumerate(all_values):

                data = table_row[0].strip() if table_row else None

                if strict:
                    if data == value:
                        return index
                elif data:
                    if value in data:
                        return index
