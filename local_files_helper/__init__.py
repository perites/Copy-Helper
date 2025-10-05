import json
import logging
import os
import shutil
import traceback

import requests
from PIL import Image

from . import default_config

logger = logging.getLogger(__name__)


class SettingsHelper:
    def __init__(self, path_to_settings):
        self.path_to_settings = path_to_settings
        self.settings = {}
        self.check_paths()

        self.read_settings_file()

    def check_paths(self):
        if not os.path.exists(self.path_to_settings):
            open(self.path_to_settings, 'w').write(default_config.default_general_settings)
            logger.warning('Fill general settings file!')
            exit()

    def read_settings_file(self):
        logger.debug(f'Reading json file {self.path_to_settings}')
        print(self.path_to_settings)
        with open(self.path_to_settings, 'r', encoding="utf-8") as file:
            self.settings = json.load(file)

    def write_settings_file(self):
        logger.debug(f'Writing to {self.path_to_settings}')
        with open(self.path_to_settings, 'w') as file:
            json.dump(self.settings, file, indent=4)

    def update_credentials(self, new_info):
        self.read_settings_file()
        self.settings['Secrets']['CREDENTIALS'] = new_info
        self.write_settings_file()


class DomainsHelper:
    def __init__(self, path_to_domains, settings):
        self.path_to_domains = path_to_domains
        self.settings = settings

        self.domains_dicts = {}
        self.check_paths()

    def check_paths(self):
        default_domain_folder = f'{self.path_to_domains}/DefaultDomain'
        os.makedirs(default_domain_folder, exist_ok=True)
        if not os.path.exists(f'{default_domain_folder}/settings.json'):
            open(f'{default_domain_folder}/settings.json', 'w').write(default_config.default_domain_settings)
            logger.debug('DefaultDomain settings file created')

        if not os.path.exists(f'{default_domain_folder}/template.html'):
            open(f'{default_domain_folder}/template.html', 'w').write(default_config.default_domain_template)
            logger.debug('DefaultDomain template file created')

    def get_domains_dicts(self):
        domains_dicts = {}
        for name in os.listdir(self.path_to_domains):
            try:
                if name == 'DefaultDomain':
                    continue

                full_path = os.path.join(self.path_to_domains, name)
                if os.path.isdir(full_path):
                    domain_dict = json.load(open(full_path + '/settings.json'))
                    domain_dict['styles']['template'] = open(full_path + '/template.html').read()

                    domains_dicts[name] = domain_dict

            except Exception as e:
                logger.error(f'Error parsing domain in folder "{name}"')
                logger.debug(traceback.format_exc())

        self.domains_dicts = domains_dicts

    def create_new_domain(self, domain_name, template_domain_name=None):
        if not domain_name:
            logger.warning('Domain Name cant be empty !')
            return

        logger.info('Creating new Domain')
        domain_folder_path = f'{self.path_to_domains}' + f'{domain_name}/'
        try:
            os.makedirs(domain_folder_path)
        except FileExistsError:
            logger.warning('Domain must have a unique name! New domain was NOT created.')
            return

        if template_domain_name:
            shutil.copy(f'Domains/{template_domain_name}/settings.json', domain_folder_path)
            shutil.copy(f'Domains/{template_domain_name}/template.html', domain_folder_path)

        else:
            shutil.copy('Domains/DefaultDomain/settings.json', domain_folder_path)
            shutil.copy('Domains/DefaultDomain/template.html', domain_folder_path)

        logger.info(f'Successfully created new domain {domain_name}')

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

    def get_lifts_htmls(self, str_copies, domain_bc_name, broadcast_date):
        date = broadcast_date.replace('/', '.')
        path_to_domain_results = self.get_domain_result_path(domain_bc_name, date)

        manual_lifts_htmls = {}
        for str_copy in str_copies:
            path = path_to_domain_results + f'{str_copy}.html'
            path_p = path_to_domain_results + f'{str_copy}-Priority.html'

            if os.path.exists(path):
                lift_html = open(path, 'r', encoding='utf-8').read()
                manual_lifts_htmls[str_copy] = lift_html

            elif os.path.exists(path_p):
                lift_html = open(path_p, 'r', encoding='utf-8').read()
                manual_lifts_htmls[str_copy] = lift_html

        return manual_lifts_htmls

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


class ImageHelper:
    def __init__(self, path_to_images, settings):
        self.path_to_images = path_to_images
        self.settings = settings
        self.check_paths()

    def check_paths(self):
        os.makedirs(self.path_to_images, exist_ok=True)

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

    def save_images(self, copy, date):
        save_image_path = self.settings['ImagesDirectory'] + f'{date}/'
        if copy.img_code:
            self.find_custom_image(f'{copy.offer_name}_{copy.img_code}', save_image_path)

        if self.settings['SaveImages']:
            for index, image_url in enumerate(copy.lift_images):
                self.save_image(f'{copy.offer_name}{copy.lift_number}-image-{index + 1}', image_url, save_image_path)


class LocalFilesHelper:
    PATH_TO_SETTINGS = 'General-Settings.json'
    PATH_TO_DOMAINS = 'Domains'
    PATH_TO_IMAGES = 'Images'

    sh = SettingsHelper(PATH_TO_SETTINGS)
    dh = DomainsHelper(PATH_TO_DOMAINS, sh.settings)
    ih = ImageHelper(PATH_TO_IMAGES, sh.settings)

    @classmethod
    def save_copy(cls, copy, domain_bc_name, date):
        path_to_domain_results = cls.dh.get_domain_result_path(domain_bc_name, date)

        cls.dh.save_lift_file(copy, path_to_domain_results)
        cls.dh.save_sl_file(copy, domain_bc_name, date, path_to_domain_results)
        cls.ih.save_images(copy, date)
