import json
import urllib.parse

import google.auth.transport.requests
import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
from flask import redirect, url_for, request, Blueprint, g

from basic_api_tools.basic_decorators import catch_errors, credentials_required
from . import config

google_auth_blueprint = Blueprint('google_auth_blueprint', __name__)

SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/spreadsheets.readonly']


@google_auth_blueprint.route('/login', methods=['GET'])
@catch_errors
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
@catch_errors
def callback():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        config.CLIENT_SECRETS_FILE_PATH, scopes=SCOPES,
        redirect_uri=url_for('.callback', _external=True)
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    credentials_json = credentials.to_json()
    try:
        state_param = request.args.get('state', '{}')

        custom_data = json.loads(urllib.parse.unquote(state_param))

        custom_callback = custom_data.get('custom_callback')
        if not custom_callback:
            return {'message': 'Successful login to copy helper google service',
                    'credentials': credentials_json}, 200

        try:
            json_data = json.dumps({
                'credentials': credentials_json
            })
            redirect_url = custom_callback + f'?data={urllib.parse.quote(json_data)}'
            return redirect(redirect_url)

        except Exception as e:
            return {
                'message': 'Successful login to google service, but could not redirect to specified callback url.',
                'error_details': f'{type(e)} : {str(e)}',
                'user_token': credentials_json}, 500

    except Exception as e:
        return {
            'message': 'Successful login to copy helper google service, but could not proceed.',
            'error_details': f'{type(e)} : {str(e)}',
            'credentials': credentials_json
        }, 500


@google_auth_blueprint.route('/credentials/refresh', methods=['POST'])
@catch_errors
@credentials_required
def refresh():
    credentials = g.credentials

    if credentials.refresh_token:
        credentials.refresh(google.auth.transport.requests.Request())
    else:
        return {
            'message': 'Refresh Token missing'}, 400

    return {'credentials': json.loads(credentials.to_json())}, 200
