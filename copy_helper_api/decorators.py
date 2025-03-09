import functools

from flask import g

from basic_api_tools import basic_exceptions
from . import google_services


def google_sheets_required(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        if not g.get('credentials'):
            raise basic_exceptions.CredentialsMissing

        google_services.GoogleSheets.initialize(g.credentials)
        result = func(*args, **kwargs)
        return result

    return wrapped_func
