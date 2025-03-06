import os

from . import config
from flask import request, Blueprint, g
from .decorators import catch_errors, credentials_required, required_structure
import logging
import traceback
from . import google_services_olapi
from . import exceptions
import google.oauth2.credentials
from . import offer as offer_module
from . import google_services
from . import copy_maker as copy_maker_module

copy_helper_blueprint = Blueprint('copy_helper_blueprint', __name__)


@copy_helper_blueprint.route("/copy/make", methods=['POST'])
# @catch_errors
@credentials_required
@required_structure(['copy', 'domainInfo'])
def make_copy():
    google_services.GoogleDrive.initialize(g.credentials)
    google_services.GoogleSheets.initialize(g.credentials)

    request_data = request.json

    domain_info = request_data['domainInfo']
    str_copy = request_data['copy']

    copy_maker = copy_maker_module.CopyMaker(domain_info, str_copy)
    results = copy_maker.make_copy()
    logging.info(str(results))

    return {
        'CopyHTML': copy_maker.copy.lift_file_content,
        'CopySls': copy_maker.copy.sls,
        'CopyImagesUrls': copy_maker.copy.images
    }

#
# @copy_helper_blueprint.route("/copy/files", methods=['GET'])  # {copy: BTUA7TS2 } credentials requared
# @catch_errors
# @credentials_required
# @required_structure(['offer_name', 'lift_number'])
# def get_copy_files():
#     request_data = request.json
#     offer_name = request_data['offer_name']
#     lift_number = request_data['lift_number']
#
#     output_type = request_data.get('output_type')
#     match output_type:
#         case 'content':
#             pass
#         case 'files_info':
#             pass
#         case _:
#             pass
#
#     offer = offer_module.Offer.find(offer_name)
#     lift_folder = offer.OfferGoogleDriveHelper.get_lift_folder_id(offer.google_drive_folder_id, lift_number)
#
#     lift_file, sl_file = offer.OfferGoogleDriveHelper.get_copy_files(lift_folder['id'])
#     # content_needed
#     # content_needed = request_data['content']
# #
#
# @copy_helper_blueprint.route('/file/content', methods=['GET'])
# @catch_errors
# @credentials_required
# # @required_structure([{'file': ['id', 'mimeType', 'name']}])
# @required_structure([{'file': [{"id": ['terst']}, 'mimeType', 'name']}])
# def file_content():
#     request_data = request.json
#     file = request_data['file']
#     google_drive_service = get_google_drive_service()
#
#     file_content = google_drive_service.get_file_content(file)
#     if not file_content:
#         return {'message': f'Could not get file content for file {file['name']} for unknown reason'}, 500
#
#     return {'file_content': file_content}, 200

# @google_services_blueprint.route('/google/drive/execute')
# @credentials_required
# def execute_drive_query():
#     drive = google_services.GoogleDrive(g.credentials)
#
#     request_data = request.json
#     query = request_data['query']
#     fields = request_data.get('fields')
#     result = drive.execute_query(query, fields)
#
#     return result
#
#
# @google_services_blueprint.route('/google/sheets/execute')
# @credentials_required
# def execute_sheets_query():
#     sheets = google_services.GoogleSheets(g.credentials)
#
#     request_data = request.json
#
#     spreadsheet_id = request_data['spreadsheet_id']
#     range = request_data['range']
#
#     result = sheets.get_data_from_range(spreadsheet_id, range)
#
#     return result

# creds = Credentials.from_authorized_user_info
# creds = Credentials.from_authorized_user_file("SystemData/services_token.json")  # Load your credentials
# user_info = get_user_info(creds)
#
# if user_info:
#     print("User ID:", user_info.get("id"))
#     print("Email:", user_info.get("email"))
#     print("Name:", user_info.get("name"))
#
#
# def credentials_required(func):
#     @functools.wraps(func)
#     def wrapped_func(*args, **kwargs):
#         cred_user_id = request.headers.get('Cred-User-ID')
#         if not cred_user_id:
#             return {'message': 'Header Cred-User-ID was not found in request'}, 401
#
#         cred_helper = credentials.CredentialsHelper(cred_user_id)
#         try:
#             cred_helper.get_credentials()
#             cred_helper.validate_credentials()
#
#         except Exception as e:
#             return {'message': f'Could not validate credentials. Details : {e}'}, 403
#
#         g.credentials = cred_helper.credentials
#         result = func(*args, **kwargs)
#         return result
#
#     return wrapped_func
#


# def only_from_allowed_sources(func):
#     @functools.wraps(func)
#     def wrapped_func(*args, **kwargs):
#         secret_key = request.headers.get('Secret-Key')
#         if secret_key and secret_key == os.getenv('COMMUNICATION_SECRET_KEY'):
#             result = func(*args, **kwargs)
#             return result
#
#         origin = request.headers.get('Origin')
#         if origin not in config.ALLOWED_ORIGINS:
#             return {'message': 'Request not from allowed origin'}, 403
#
#         result = func(*args, **kwargs)
#         return result
#
#     return wrapped_func


# def cred_user_id_required(func):
#     @functools.wraps(func)
#     def wrapped_func(*args, **kwargs):
#         cred_user_id = request.headers.get('Cred-User-ID')
#         if not cred_user_id:
#             return {'message': 'Header Cred-User-ID was not found in request'}, 401
#
#         g.cred_user_id = cred_user_id
#         return func(*args, **kwargs)
#
#     return wrapped_func

#
# @copy_maker_blueprint.route("/user")
# @only_from_allowed_sources
# @cred_user_id_required
# def user():
#     cred_user_id = g.cred_user_id
#     url = config.DATABASE_URL + 'v1/users/' + cred_user_id
#
#     headers = {
#         'Secret-Key': os.getenv('COMMUNICATION_SECRET_KEY')
#     }
#
#     return requests.get(url=url, headers=headers)
