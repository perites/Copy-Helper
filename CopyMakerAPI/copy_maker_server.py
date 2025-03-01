from flask import Flask, redirect, url_for, request
import server_secrets
import functools
import copy_helper
import logging
import traceback

app = Flask(__name__)

app.secret_key = server_secrets.app_secret_key


def validate_credentials(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        # key = request.headers['Authorization'].split(' ')[1]

        # validate = reques . get ( /valdate )

        # credentials = json.loads(get_credentials(key))
        # credentials = Credentials.from_authorized_user_info(credentials)
        #
        # if not credentials.valid:
        #
        #     if credentials.expired and credentials.refresh_token:
        #         credentials.refresh(Request())
        #         update_credentials(key, credentials)
        #     else:
        #         return redirect(url_for('login'))

        result = func(*args, **kwargs)
        return result

    return wrapped_func


@app.route("/copy/make")
@validate_credentials
def make_copy():
    request_data = request.json

    domain_name = request_data['DomainName']

    date = request_data['Date']

    str_copy = request_data['Copy']

    try:
        copy_maker = copy_helper.copy_maker.CopyMaker(domain_name, str_copy, date)
        results = copy_maker.make_copy(set_content_from_local=True)
        logging.info(str(results))
    except copy_helper.copy_maker.CopyMakerException as e:
        logging.error(
            f'Error while making copy {str_copy} for domain {domain_name} for date {date}. Details : {e}')

    except copy_helper.offer.OfferException as e:
        logging.error(f'Error with offer {e.offer_name}. Details : {e}')

    except Exception as e:
        logging.error(f'Unknown error while making copy {str_copy}. Details : {e}')
        logging.debug(traceback.format_exc())

    return 'f'


if __name__ == "__main__":
    app.run(debug=True)
