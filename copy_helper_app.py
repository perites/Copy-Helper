# TODO change logging  debug to info in some places

import logging
import sys

import copy_helper

datefmt = '%d-%m %H:%M:%S:%M'
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] : %(message)s',
    datefmt=datefmt,
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main-log', mode='a', encoding='utf-8', )
    ]
)
logging.getLogger("googleapiclient").setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def cprint(*args, **kwargs):
    prefix = '///>'
    print(prefix, *args, **kwargs)


def cinput(hint=''):
    prefix = '///> ' + hint
    return input(prefix)


def process_copy_files_content(domain, copy, path_to_domain_results, lift_file_content, sl_file_content, date):
    tracking_link = domain.make_tracking_link(copy)

    footer_text, url = domain.gsh_helper.get_priority_footer_values(copy.offer.name, domain.settings.priority_link_info)
    priority_info = {
        'text': footer_text,
        'url': url,
    }

    priority_footer_block = domain.make_priority_block(footer_text, url, copy.offer.name)

    if not lift_file_content:
        domain.save_copy_files(lift_file_content, sl_file_content, path_to_domain_results, str(copy),
                               priority_info, tracking_link, date)
        return

    lift_file_content = copy_helper.ImageHelper.process_images(copy, domain.styles_helper.image_block,
                                                               lift_file_content)

    lift_file_content = domain.apply_styles(lift_file_content)

    if domain.settings.antispam:
        lift_file_content = domain.anti_spam_text(lift_file_content)
        priority_footer_block = domain.anti_spam_text(priority_footer_block)
        sl_file_content = domain.anti_spam_text(sl_file_content)

    lift_file_content = domain.add_template(lift_file_content, priority_footer_block)

    lift_file_content = domain.add_link_to_lift(tracking_link, lift_file_content)

    domain.save_copy_files(lift_file_content, sl_file_content, path_to_domain_results, str(copy),
                           priority_info, tracking_link, date)


def main_page():
    cprint('Type what you want to do:')
    cprint('make-domain | apply-styles | add-domain | exit')
    action = cinput().strip()
    match action:
        case 'exit':
            exit()

        case 'add-domain':
            cprint('To create new domain enter name it below. Name should be same as in broadcast')
            domain_name = cinput()
            copy_helper.settings.GeneralSettings.create_new_domain(domain_name)

        case 'make-domain' | 'md':
            cprint('To make domain, enter <domain-name>(full name or abbreviate) <date>(same as column in broadcast)')
            domain_name, date = cinput().split(' ')
            domain_name = copy_helper.settings.GeneralSettings.domains_short_names.get(domain_name)
            if not domain_name:
                cprint('Did not found that abbreviate in settings')

            domain = copy_helper.Domain(domain_name)
            if not domain:
                cprint(
                    f'Cant find that domain, ensure that you entering name correctly and {domain_name} in Settings/Domains')
                raise Exception

            copies = domain.get_copies(date)
            if not copies:
                cprint(
                    'Copies were not found for some reason, you can enter them manually (separated by space as in brodcast) or just press enter to return to begining')
                copies = cinput().strip().split(' ')

            copies = list(filter(lambda copy: copy, map(copy_helper.Copy.create, copies)))

            cprint(f'Successfully processed {len(copies)} copies.')

            path_to_domain_results = copy_helper.settings.GeneralSettings.result_directory + f'/{domain.name}/{date.replace('/', '.')}/'
            for copy in copies:
                lift_file_content, sl_file_content = domain.get_copy_files_content(copy)
                process_copy_files_content(domain, copy, path_to_domain_results, lift_file_content, sl_file_content,
                                           date.replace('/', '.'))

        case 'apply-styles':
            cprint(
                'To apply styles of domain to already existing copy, enter <domain-name>(full name or abbreviate) <date>(same as column in broadcast) <COPY>(exampe BTUA7 or CONO601TS2)')
            domain_name, date, str_copy = cinput().split(' ')
            domain_name = copy_helper.settings.GeneralSettings.domains_short_names.get(domain_name)
            if not domain_name:
                cprint('Did not found that abbreviate in settings')

            domain = copy_helper.Domain(domain_name)
            if not domain:
                cprint(
                    f'Cant find that domain, ensure that you entering name correctly and {domain_name} in Settings/Domains')
                raise Exception

            path_to_domain_results = copy_helper.settings.GeneralSettings.result_directory + f'/{domain.name}/{date.replace('/', '.')}/'
            logging.info(f'Trying to read {path_to_domain_results + str_copy}.html')
            with open(path_to_domain_results + f'{str_copy}.html', 'r', encoding='utf-8') as file:
                lift_file_content = file.read()

            process_copy_files_content(domain, copy_helper.Copy.create(str_copy), path_to_domain_results,
                                       lift_file_content, "", date.replace('/', '.'))


if __name__ == "__main__":
    cprint('Welcome to copy-helper alfa test')

    copy_helper.settings.GeneralSettings.set_settings()
    while True:
        try:
            main_page()
        except Exception as e:
            logging.critical('Got Unexpected Error!')
            logging.exception(e)
            print('Returning to main page')
