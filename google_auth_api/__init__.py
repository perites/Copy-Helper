import hashlib
import json
import os
import urllib.parse

import google.auth.transport.requests
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
from flask import redirect, url_for, request, Blueprint, g

from . import config
from . import tools
from .decorators import catch_errors, credentials_from_user_token

google_auth_blueprint = Blueprint('google_auth_blueprint', __name__)

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets.readonly']

if not os.getenv('USER_TOKEN_SECRET_KEY'):
    raise ValueError('No user token secret key provided')


@google_auth_blueprint.route('/login', methods=['GET'])
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        config.CLIENT_SECRETS_FILE_PATH, scopes=SCOPES,
        redirect_uri=url_for('.callback', _external=True)
    )
    custom_callback = request.args.get('callback', '')

    custom_data = {'custom_callback': custom_callback}

    state_param = urllib.parse.quote(json.dumps(custom_data))

    auth_url, state = flow.authorization_url(prompt="consent", state=state_param)
    return redirect(auth_url)


@google_auth_blueprint.route('/callback')
def callback():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        config.CLIENT_SECRETS_FILE_PATH, scopes=SCOPES,
        redirect_uri=url_for('.callback', _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    user_credentials = flow.credentials
    try:
        user_info = tools.get_user_info(user_credentials)

        user_google_id = user_info['id']
        user_token_raw = user_google_id + os.getenv('USER_TOKEN_SECRET_KEY')
        user_token_bytes = user_token_raw.encode('utf-8')
        user_token = hashlib.sha256(user_token_bytes).hexdigest()

        tools.save_credentials(user_token, user_credentials.to_json())

        state_param = request.args.get('state', '{}')

        custom_data = json.loads(urllib.parse.unquote(state_param))

        custom_callback = custom_data.get('custom_callback', '')
        if not custom_callback:
            return {'message': 'Successful login to google service', 'user_token': user_token}, 201

        try:
            json_data = json.dumps({
                'user_token': user_token
            })
            redirect_url = custom_callback + f'?data={urllib.parse.quote(json_data)}'
            return redirect(redirect_url)

        except Exception as e:
            return {
                'message': 'Successful login to google service, but could not redirect to specified callback url.',
                'error_details': str(e),
                'user_token': user_token}, 500

    except Exception as e:
        return {
            'message': 'Successful login to google service, but could not process them. Returning raw credentials',
            'error_details': f'{type(e)} : {str(e)}',
            'credentials': user_credentials.to_json()}, 500


@google_auth_blueprint.route('/credentials', methods=['GET'])
# @catch_errors
@credentials_from_user_token
def credentials():
    return {'credentials': json.loads(g.user_credentials.to_json())}, 200
