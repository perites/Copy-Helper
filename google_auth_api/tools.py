import redis
import requests

from . import config


def get_user_info(creds):
    url = "https://www.googleapis.com/oauth2/v2/userinfo"

    headers = {"Authorization": f"Bearer {creds.token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        return user_info
    else:
        raise Exception(
            f'Error while receiving user data. Response from google : {response.json()} status code : {response.status_code}')


redis_db = redis.Redis(host=config.DATABASE_CREDENTIALS['host'],
                       password=config.DATABASE_CREDENTIALS['password'], port=config.DATABASE_CREDENTIALS['port'],
                       ssl=True)


def get_credentials(user_token):
    return redis_db.get(user_token).decode('utf-8')


def save_credentials(user_token, user_credentials):
    redis_db.set(user_token, user_credentials)
    return True
