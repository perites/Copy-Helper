import json
import logging
import os
import shutil
import sys
import traceback

import requests
from PIL import Image

import copy_maker_core
import default_config

logger = logging.getLogger(__name__)


class Core:
    def __init__(self):
        self.check_paths()

        self.settings = json.load(open('GeneralSettings.json'))
        self.domains = self.get_domains()

    @staticmethod
    def check_paths():
        if not os.path.exists('GeneralSettings.json'):
            open('GeneralSettings.json', 'w').write(default_config.default_general_settings)
            logger.error('Fill general settings!')
            exit()

        os.makedirs('Domains/DefaultDomain', exist_ok=True)
        if not os.path.exists('Domains/DefaultDomain/settings.json'):
            open('Domains/DefaultDomain/settings.json', 'w').write(default_config.default_domain_settings)
            logger.debug('DefaultDomain settings file created')

        if not os.path.exists('Domains/DefaultDomain/template.html'):
            open('Domains/DefaultDomain/template.html', 'w').write(default_config.default_domain_template)
            logger.debug('DefaultDomain template file created')

        os.makedirs('Images', exist_ok=True)

    @staticmethod
    def get_domains():
        domains_folder = 'Domains/'
        domains = {}
        for name in os.listdir(domains_folder):
            try:
                if name == 'DefaultDomain':
                    continue

                full_path = os.path.join(domains_folder, name)
                if os.path.isdir(full_path):
                    domain_dict = json.load(open(full_path + '/settings.json'))
                    domain_dict['styles']['template'] = open(full_path + '/template.html').read()
                    domain = copy_maker_core.domain.Domain(domain_dict)

                    domains[name] = domain
            except Exception as e:
                logger.error(f'Error parsing domain in folder "{name}"')
                logger.debug(traceback.format_exc())

        return domains

    @staticmethod
    def exit():
        exit()

    @staticmethod
    def restart_script():
        logger.debug('Restarting')
        os.execl(sys.executable, sys.executable, *sys.argv)

    @staticmethod
    def clear_cache(option):
        copy_maker_core.offer.OffersCache.clear_cache(option)

    @staticmethod
    def create_new_domain(domain_name):
        if not domain_name:
            logger.warning('Domain Name cant be empty')
            return

        logger.info('Creating new Domain')
        domain_folder_path = 'Domains/' + f'{domain_name}/'
        try:
            os.makedirs(domain_folder_path)
        except FileExistsError:
            logger.warning('Domain must have unique name')
            return

        shutil.copy('Domains/DefaultDomain/settings.json', domain_folder_path)
        shutil.copy('Domains/DefaultDomain/template.html', domain_folder_path)

    def make_domain(self, domain_name, broadcast_date, get_copies_manually_callback, str_copies=None):
        domain = self.get_domain(domain_name)
        copies, max_len_str_copy = self.get_copies(str_copies, domain, broadcast_date, get_copies_manually_callback)

        domain_bc_name = domain.broadcast['name']
        date = broadcast_date.replace('/', '.')
        path_to_domain_results = self.get_domain_result_path(domain_bc_name, date)

        copies_results = []

        message = f'Processing copies: {", ".join([copy.str_rep for copy in copies])}'
        logger.info(message)
        # yield message

        for copy in copies:
            try:
                # yield f'Making {copy.str_rep}'
                copy = self.make_copy(copy, domain, path_to_domain_results)
                # yield f'Saving {copy.str_rep}'
                self.save_copy(copy, domain_bc_name, date, path_to_domain_results)

                copies_results.append(self.get_copy_result(copy, max_len_str_copy))
                logger.debug(self.get_copy_result(copy, max_len_str_copy))

            except Exception as e:
                logger.error(f'Error while making copy {copy.str_rep}. Details : {e}')
                logger.debug(traceback.format_exc())

        return copies_results

    def get_domain(self, domain_name):
        domain = self.domains.get(domain_name)
        if not domain:
            raise Exception(f'No domain with given name {domain_name}')

        return domain

    def get_domain_result_path(self, domain_name, date):
        match self.settings['ResultsDirectoryType']:
            case 'Domain-Date':
                path_to_domain_results = self.settings['ResultsDirectory'] + f'{domain_name}/{date}/'

            case 'Date-Domain':
                path_to_domain_results = self.settings['ResultsDirectory'] + f'{date}/{domain_name}/'

            case _:
                logger.warning('Unknown type of result directory type, using default')
                path_to_domain_results = self.settings['ResultsDirectory'] + f'{date}/{domain_name}/'

        os.makedirs(path_to_domain_results, exist_ok=True)
        return path_to_domain_results

    @staticmethod
    def get_copies(str_copies, domain, broadcast_date, get_copies_manually_callback):
        if not str_copies:
            str_copies = domain.get_copies_from_broadcast(broadcast_date)
            if not str_copies:
                str_copies = get_copies_manually_callback()

        copies = []
        max_len_str_copy = 0
        for str_copy in str_copies:
            if str_copy:
                if (len_str_copy := len(str_copy)) > max_len_str_copy:
                    max_len_str_copy = len_str_copy
                copies.append(domain.create_copy(str_copy.strip()))

        return copies, max_len_str_copy

    @staticmethod
    def make_copy(copy, domain, path_to_domain_results):
        copy = domain.find_copy(copy)
        if not copy.lift_html:
            logger.info(f'Html was not found for {copy.str_rep}, trying to read from local file')
            file_name = copy.str_rep + ('-Priority' if copy.priority_info['is_priority'] else '')
            path = path_to_domain_results + f'{file_name}.html'
            if os.path.exists(path):
                copy.lift_html = open(path, 'r', encoding='utf-8').read()

            if not copy.lift_html:
                logger.warning('Can`t find copy html')
                return copy

        copy = domain.make_tracking_link(copy)
        copy = domain.make_unsub_link(copy)
        copy = domain.process_images(copy)

        styles_helper = copy_maker_core.styles_helper.StylesHelper(domain.styles)
        copy = styles_helper.apply_styles(copy)
        copy = styles_helper.add_template(copy)

        copy.lift_html = copy.lift_html.replace('urlhere', copy.tracking_link)

        return copy

    @staticmethod
    def get_copy_result(copy, max_len_str_copy):
        html_r = '+' if copy.html_found else '-'
        sl_r = '+' if copy.lift_sls else '-'
        pfooter_r = '+' if copy.priority_info['unsub_text'] else '-'
        link_maid = 'UNKNOWN_TYPE' not in copy.tracking_link
        link_r = '+' if link_maid else '-'
        result = f'{"Warning!:" if not link_maid else ""}{copy.str_rep + (' ' * (max_len_str_copy - len(copy.str_rep)))} : html {html_r} | sl {sl_r} | pfooter {pfooter_r} | link {link_r} | img {len(copy.lift_images)}'

        return result

    def save_copy(self, copy, domain_bc_name, date, path_to_domain_results):
        self.save_lift_file(copy, path_to_domain_results)

        self.save_sl_file(copy, domain_bc_name, date, path_to_domain_results)

        save_image_path = self.settings['ImagesDirectory'] + f'{date}/'
        if copy.img_code:
            self.find_custom_image(f'{copy.offer_name}_{copy.img_code}', save_image_path)

        if self.settings['SaveImages']:
            for index, image_url in enumerate(copy.lift_images):
                self.save_image(f'{copy.offer_name}{copy.lift_number}-image-{index + 1}', image_url, save_image_path)

    @staticmethod
    def save_lift_file(copy, path_to_domain_results):
        file_name = copy.str_rep + ('-Priority' if copy.priority_info['is_priority'] else '')
        path = path_to_domain_results + f'{file_name}.html'
        with open(path, 'w', encoding='utf-8') as file:
            file.write(copy.lift_html)
            logger.debug(f'Successfully saved lift file for {copy.str_rep}')

    @staticmethod
    def save_sl_file(copy, domain_bc_name, date, path_to_domain_results):
        path_to_sls_file = path_to_domain_results + f'SLs-{domain_bc_name}-{date}.txt'

        if os.path.exists(path_to_sls_file):
            with open(path_to_sls_file, 'r', encoding='utf-8') as file:
                sls_file_content = file.read()
                if copy.str_rep in sls_file_content:
                    logger.info(f'Did not add sls for {copy.str_rep} in SLs.txt file as already has them')
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
                copy.str_rep + suffix + f' | images : {len(copy.lift_images)}' + '\n\n' +

                f'Tracking link:\n{copy.tracking_link}\n\n' +
                unsub_url_str +
                custom_sls_block +

                'Sls:\n' +

                (copy.lift_sls if copy.lift_sls else '') +

                "\n----------------------------------------\n\n\n\n")

        with open(path_to_sls_file, 'a', encoding='utf-8') as file:
            file.write(copy_sls)
            logger.info(f'Successfully add sls for {copy.str_rep} in SLs.txt')

    @staticmethod
    def save_image(image_file_name, image_url, save_image_path):
        try:

            if not os.path.exists(save_image_path):
                os.makedirs(save_image_path)

            temp_full_image_path = 'Images/' + image_file_name

            with os.scandir(save_image_path) as entries:
                for entry in entries:
                    if entry.is_file() and image_file_name in entry.name:
                        logger.debug(f'Not saving {image_file_name} - image already saved')
                        return

            with os.scandir('Images/') as entries:
                for entry in entries:
                    if entry.is_file() and image_file_name in entry.name:
                        logger.debug(f'Image {image_file_name} already downloaded, copying')
                        shutil.copy(entry.path, save_image_path + entry.name)
                        return

            logger.debug(f'Saving {image_file_name} to {temp_full_image_path}')
            with open(temp_full_image_path, 'wb') as file:
                response = requests.get(image_url, stream=True)
                if not response.ok:
                    logger.warning(
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
            logger.error(f'Error while saving image {image_file_name}. Details : {e}')
            logger.debug(traceback.format_exc())

    @staticmethod
    def find_custom_image(image_file_name, save_image_path):
        if not os.path.exists(save_image_path):
            os.makedirs(save_image_path)

        with os.scandir(save_image_path) as entries:
            for entry in entries:
                if entry.is_file() and image_file_name in entry.name:
                    logger.debug(f'Not saving custom image {image_file_name} - image already saved')
                    return

        with os.scandir('Images/') as entries:
            for entry in entries:
                if entry.is_file() and image_file_name in entry.name:
                    logger.info(f'Found custom image {image_file_name}, copying')
                    shutil.copy(entry.path, save_image_path + entry.name)
                    return


core = Core()
