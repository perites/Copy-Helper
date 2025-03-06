import json
import functools

from flask import g, request

from . import tools

import google.auth.transport.requests
import google.auth.transport.requests
import google.oauth2.credentials


def credentials_from_user_token(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        request_data = request.json

        user_token = request_data.get('user_token')
        if not user_token:
            return {'message': 'No user token was found in request json'}, 400

        maybe_credentials = tools.get_credentials(user_token)

        if not maybe_credentials:
            return {'message': 'No credentials was found for given user token'}, 401

        user_credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(
            json.loads(maybe_credentials))

        if not user_credentials.valid:
            if user_credentials.expired and user_credentials.refresh_token:
                user_credentials.refresh(google.auth.transport.requests.Request())
            else:
                return {
                    'message': 'Credentials not valid and can`t can not be refreshed because refresh_token is missing'}, 401

        g.user_credentials = user_credentials
        result = func(*args, **kwargs)
        return result

    return wrapped_func


def catch_errors(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result

        except Exception as e:
            status_code = e.status_code if hasattr(e, 'status_code') else 500
            return {'message': f'Error occurred during processing {func.__name__}',
                    'error_details': f'{type(e)} : {str(e)}'}, status_code

    return wrapped_func
