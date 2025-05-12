import datetime
import json
import logging
import os
import shutil
import sys
import time
import traceback

import requests
from PIL import Image

import logger

if not os.path.exists('GeneralSettings.json'):
    open('GeneralSettings.json', 'w').write(json.dumps(
        {
            "ResultsDirectory": "",
            "ResultsDirectoryType": "",
            "ImagesDirectory": "",
            "SaveImages": False
        }
    ))
    logging.error('Fill general settings!')
    exit()

if not os.path.exists('custom_sls.json'):
    open('custom_sls.json', 'w').write('{}')
    logging.debug('Custom sls file created')

SETTINGS = json.load(open('GeneralSettings.json'))
CUSTOM_SLS = json.load(open('custom_sls.json'))
os.makedirs('Domains', exist_ok=True)
os.makedirs('Images', exist_ok=True)


def cinput():
    prefix = f'{datetime.datetime.now():{logger.datefmt}} [INPUT] > '
    return input(prefix).strip()


def clear_console():
    print("\033[H\033[J\033[3J", end="")


def restart_script():
    logging.info("Restarting...")
    time.sleep(1)
    os.execl(sys.executable, sys.executable, *sys.argv)


def get_copy_result(copy, max_len_str_copy):
    html_r = '+' if copy.html_found else '-'
    sl_r = '+' if copy.lift_sls else '-'
    pfooter_r = '+' if copy.priority_info['unsub_text'] else '-'
    link_r = '+' if 'UNKNOWN_TYPE' not in copy.tracking_link else '-'
    result = f'{copy.str_rep + (' ' * (max_len_str_copy - len(copy.str_rep)))} : html {html_r} | sl {sl_r} | pfooter {pfooter_r} | link {link_r} | img {len(copy.lift_images)}'

    return result


def get_domain_result_path(domain_name, date):
    match SETTINGS['ResultsDirectoryType']:
        case 'Domain-Date':
            path_to_domain_results = SETTINGS['ResultsDirectory'] + f'{domain_name}/{date}/'

        case 'Date-Domain':
            path_to_domain_results = SETTINGS['ResultsDirectory'] + f'{date}/{domain_name}/'

        case _:
            logging.warning('Unknown type of result directory type, using default')
            path_to_domain_results = SETTINGS['ResultsDirectory'] + f'{date}/{domain_name}/'

    os.makedirs(path_to_domain_results, exist_ok=True)
    return path_to_domain_results


def save_lift_file(copy, path_to_domain_results):
    file_name = copy.str_rep + ('-Priority' if copy.priority_info['is_priority'] else '')
    path = path_to_domain_results + f'{file_name}.html'
    with open(path, 'w', encoding='utf-8') as file:
        file.write(copy.lift_html)
        logging.debug(f'Successfully saved lift file for {copy.str_rep}')


def save_sl_file(copy, domain_name, date, path_to_domain_results):
    path_to_sls_file = path_to_domain_results + f'SLs-{domain_name}-{date}.txt'

    if os.path.exists(path_to_sls_file):
        with open(path_to_sls_file, 'r', encoding='utf-8') as file:
            sls_file_content = file.read()
            if copy.str_rep in sls_file_content:
                logging.info(f'Did not add sls for {copy.str_rep} in SLs.txt file as already has them')
                return

    if copy.priority_info['is_priority']:
        unsub_url_str = f'Unsub link:\n{copy.priority_info['unsub_link']}\n\n'
        suffix = '-Priority'

    else:
        unsub_url_str, suffix = '', ''

    if copy.custom_sls:
        custom_sls_block = '''Custom SLs:\n'''
        for lift_custom_sls, custom_sls in copy.custom_sls.items():
            custom_sls_block += f'''
{lift_custom_sls} 
SL : {custom_sls['SL']}
SN : {custom_sls['SN']}

'''
        custom_sls_block += '\n'
    else:
        custom_sls_block = ''

    copy_sls = (
            copy.str_rep + suffix + '\n\n' +

            f'Tracking link:\n{copy.tracking_link}\n\n' +
            unsub_url_str +
            custom_sls_block +

            'Sls:\n' +

            (copy.lift_sls if copy.lift_sls else '') +

            "\n----------------------------------------\n\n\n\n")

    with open(path_to_sls_file, 'a', encoding='utf-8') as file:
        file.write(copy_sls)
        logging.info(f'Successfully add sls for {copy.str_rep} in SLs.txt')


def save_image(image_file_name, image_url, date):
    try:
        save_image_path = SETTINGS['ImagesDirectory'] + f'{date}/'

        if not os.path.exists(save_image_path):
            os.makedirs(save_image_path)

        temp_full_image_path = 'Images/' + image_file_name

        with os.scandir(save_image_path) as entries:
            for entry in entries:
                if entry.is_file() and image_file_name in entry.name:
                    logging.debug(f'Not saving {image_file_name} - image already saved')
                    return

        with os.scandir('Images/') as entries:
            for entry in entries:
                if entry.is_file() and image_file_name in entry.name:
                    logging.debug(f'Image {image_file_name} already downloaded, copying')
                    shutil.copy(entry.path, save_image_path + entry.name)
                    return

        logging.debug(f'Saving {image_file_name} to {temp_full_image_path}')
        with open(temp_full_image_path, 'wb') as file:
            response = requests.get(image_url, stream=True)
            if not response.ok:
                logging.warning(
                    f'Error while saving image {image_file_name}. Request status code {response.status_code}')

                return

            for chunk in response.iter_content(512):
                file.write(chunk)

        img = Image.open(temp_full_image_path)
        ext = img.format.lower()
        img.close()

        new_full_image_path = temp_full_image_path + f'.{ext}'

        os.rename(temp_full_image_path, new_full_image_path)

        shutil.copy(new_full_image_path, save_image_path + image_file_name + f'.{ext}')

    except Exception as e:
        logging.error(f'Error while saving image {image_file_name}. Details : {e}')
        logging.debug(traceback.format_exc())


def find_custom_image(image_file_name, date):
    save_image_path = SETTINGS['ImagesDirectory'] + f'{date}/'
    if not os.path.exists(save_image_path):
        os.makedirs(save_image_path)

    with os.scandir(save_image_path) as entries:
        for entry in entries:
            if entry.is_file() and image_file_name in entry.name:
                logging.debug(f'Not saving custom image {image_file_name} - image already saved')
                return

    with os.scandir('Images/') as entries:
        for entry in entries:
            if entry.is_file() and image_file_name in entry.name:
                logging.info(f'Found custom image {image_file_name}, copying')
                shutil.copy(entry.path, save_image_path + entry.name)
                return


def main_cycle():
    logging.info('Type what you want to do:')
    logging.info('make-domain (md) | clear-cache | add-domain | clear | restart | exit')
    action = cinput()
    match action:
        case 'exit':
            exit()

        case 'restart':
            restart_script()

        case 'clear':
            clear_console()

        case 'add-domain':
            logging.info('Enter new domain name')
            domain_name = cinput()
            if not domain_name:
                logging.warning('Domain Name cant be empty')
                return
            logging.info('Creating new Domain')
            domain_folder_path = 'Domains/' + f'{domain_name}/'
            try:
                os.makedirs(domain_folder_path)
            except FileExistsError:
                logging.warning('Domain must have unique name')
                return

            shutil.copy('Domains/DefaultDomain/settings.json', domain_folder_path)
            shutil.copy('Domains/DefaultDomain/template.html', domain_folder_path)

        case 'clear-cache':
            logging.info('Specify offer to clear cache')
            option = cinput()
            copy_helper.offer.OffersCache.clear_cache(option)

        case 'make-domain' | 'md':
            logging.info('To make domain, enter <domain-name> <date>')
            logging.info(f'Added domains : {', '.join(sorted(DOMAINS.keys()))}')

            user_input = cinput().strip().split(' ')

            domain_name, broadcast_date = user_input[0], user_input[1]

            domain = DOMAINS.get(domain_name)
            if not domain:
                return

            if len(user_input) == 2:
                str_copies = domain.get_copies_from_broadcast(broadcast_date)
                if not str_copies:
                    logging.info('Copies were not found, you can enter them manually (separated by space)')
                    str_copies = cinput().split(' ')

            elif len(user_input) > 2:
                str_copies = user_input[2:]

            else:
                logging.warning('Wrong input')
                return

            path_to_domain_results = get_domain_result_path(domain.broadcast['name'], broadcast_date.replace('/', '.'))

            copies = []
            max_len_str_copy = 0
            for str_copy in str_copies:
                if str_copy:
                    if (len_str_copy := len(str_copy)) > max_len_str_copy:
                        max_len_str_copy = len_str_copy
                    copies.append(domain.create_copy(str_copy.strip()))

            copies_results = []

            logging.info(f'Processing copies : {", ".join([copy.str_rep for copy in copies])}')
            for copy in copies:
                try:
                    copy = domain.find_copy(copy)
                    if not copy.lift_html:
                        logging.info(f'Html was not found for {copy.str_rep}, trying to read from local file')
                        file_name = copy.str_rep + ('-Priority' if copy.priority_info['is_priority'] else '')
                        path = path_to_domain_results + f'{file_name}.html'
                        if os.path.exists(path):
                            copy.lift_html = open(path, 'r', encoding='utf-8').read()

                    copy = domain.make_tracking_link(copy)
                    copy = domain.make_unsub_link(copy)
                    copy = domain.process_images(copy)

                    styles_helper = copy_helper.styles_helper.StylesHelper(domain.styles)
                    copy = styles_helper.apply_styles(copy)
                    copy = styles_helper.add_template(copy)

                    copy.lift_html = copy.lift_html.replace('urlhere', copy.tracking_link)

                    copies_results.append(get_copy_result(copy, max_len_str_copy))

                    save_lift_file(copy, path_to_domain_results)

                    if custom_sls := (CUSTOM_SLS.get(copy.offer_name)):
                        copy.custom_sls = custom_sls
                    save_sl_file(copy, domain.broadcast['name'], broadcast_date.replace('/', '.'),
                                 path_to_domain_results)

                    if copy.img_code:
                        find_custom_image(f'{copy.offer_name}_{copy.img_code}', broadcast_date.replace('/', '.'))

                    if SETTINGS['SaveImages']:
                        for index, image_url in enumerate(copy.lift_images):
                            save_image(f'{copy.offer_name}{copy.lift_number}-image-{index + 1}', image_url,
                                       broadcast_date.replace('/', '.'))

                except Exception as e:
                    logging.error(f'Error while making copy {copy.str_rep}. Details : {e}')
                    logging.debug(traceback.format_exc())

            logging.info('======================')

            logging.info(f'Finished making domain {domain_name} for date {broadcast_date}')
            for results in copies_results:
                logging.info(results)

            logging.info('======================')


if __name__ == "__main__":
    logging.root = logger.logger
    import copy_helper

    clear_console()
    logging.info('Welcome to copy-helper')
    logging.info('Loading...')

    domains_folder = 'Domains/'
    DOMAINS = {}
    for name in os.listdir(domains_folder):
        if name == 'DefaultDomain':
            continue

        full_path = os.path.join(domains_folder, name)
        if os.path.isdir(full_path):
            domain_dict = json.load(open(full_path + '/settings.json'))
            domain_dict['styles']['template'] = open(full_path + '/template.html').read()
            domain = copy_helper.domain.Domain(domain_dict)

            DOMAINS[name] = domain

    while True:
        try:
            main_cycle()
        except Exception as e:
            logging.critical(f'Got Unexpected Error! Details : {e}')
            logging.debug(traceback.format_exc())
            logging.info('Returning to main page')
