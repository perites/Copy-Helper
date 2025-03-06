import logging
from io import BytesIO

from docx import Document

from googleapiclient.discovery import build
from . import exceptions


def get_service(service_name, credentials):
    match service_name:
        case "drive":
            version = "v3"

        case "sheets":
            version = "v4"

        case _:
            return

    service = build(service_name, version, credentials=credentials, cache_discovery=False)
    return service


class GoogleDrive:
    def __init__(self, credentials):
        self.drive_service = get_service('drive', credentials)

    def execute_query(self, query, fields='files(id, name)'):
        result = self.drive_service.files().list(q=query, fields=fields,
                                                 includeItemsFromAllDrives=True,
                                                 supportsAllDrives=True).execute()
        result = result.get('files', [])

        return result

    def get_folder_by_name(self, folder_name, parent_folder_id, strict=True):
        name_part = "name=" if strict else "name contains "

        query = f"{name_part}'{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_folder_id}' in parents"
        folders = self.execute_query(query)
        return folders[0] if folders else None

    def get_folders_of_folder(self, parent_folder_id):
        query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_folder_id}' in parents"
        folders = self.execute_query(query)
        return folders

    def get_files_from_folder(self, folder_id):
        query = f'mimeType!="application/vnd.google-apps.folder" and trashed=false and "{folder_id}" in parents'
        fields = 'files(id, name, mimeType)'
        lift_folder_files = self.execute_query(query, fields)

        return lift_folder_files

    def get_file_content(self, file):
        file_id = file['id']
        mime_type = file['mimeType']
        match mime_type:
            case 'text/html':
                request = self.drive_service.files().get_media(fileId=file_id)
                content = request.execute().decode('utf-8')

            case 'application/vnd.google-apps.document':
                request = self.drive_service.files().export_media(fileId=file_id,
                                                                  mimeType='text/plain')

                content = request.execute().decode('utf-8')

            case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                request = self.drive_service.files().get_media(fileId=file_id)

                content = self.extract_text_from_docx(request.execute())

            case _:
                raise exceptions.UnsupportedFileType(mime_type)

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

    def __init__(self, credentials):
        self.sheet_service = get_service('sheets', credentials)
        # cache = {}

    def get_new_data_from_range(self, spreadsheet_id, range):
        sheet = self.sheet_service.spreadsheets()

        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        values = result.get('values', [])

        return values

    def get_data_from_range(self, spreadsheet_id, range):
        request = (spreadsheet_id, range)

        # values = cls.cache.get(request)
        # if values:
        #     return values

        values = self.get_new_data_from_range(*request)

        # cls.cache[request] = values

        return values

    def get_table_index_of_value(self, spreadsheet_id, value, range, is_row=True):
        all_values = self.get_data_from_range(spreadsheet_id, range)

        if is_row:
            all_values = all_values[0] if is_row else all_values
            value_index = all_values.index(value)

            return value_index

        else:
            for index, table_row in enumerate(all_values):

                data = table_row[0] if table_row else None
                if data == value:
                    return index
