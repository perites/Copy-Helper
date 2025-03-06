# TODO add proper logging to google auth api

import logging
import os
import sys
from flask import Flask

import copy_helper_api
import google_auth_api

logging.basicConfig(
    format='%(asctime)s [LOGGER:%(name)s] [%(levelname)s] : %(message)s',
    datefmt='%d-%m %H:%M:%S',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main-log.log', mode='a', encoding='utf-8', )
    ]
)

logging.getLogger('googleapiclient').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

app = Flask(__name__)
app_secret_key = os.getenv("SERVER_SECRET_KEY")
if not app_secret_key:
    raise ValueError('No server secret key provided')
app.secret_key = app_secret_key

app.register_blueprint(google_auth_api.google_auth_blueprint)
app.register_blueprint(copy_helper_api.copy_helper_blueprint)

if __name__ == "__main__":
    app.run(debug=True)
