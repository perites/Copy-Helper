# TODO change logging  debug to info in some places
# TODO move get_priority_footer_values to offer
import logging
import logger
import copy_helper
import os


def cprint(*args, **kwargs):
    prefix = '///>'
    print(prefix, *args, **kwargs)


def cinput(hint=''):
    prefix = '///> ' + hint
    return input(prefix)


def process_copy_files_content(domain, copy, path_to_domain_results, lift_file_content, sl_file_content, date):
    tracking_link = domain.make_tracking_link(copy)

    if copy.offer.info.is_priority:
        footer_text, url = domain.gsh_helper.get_priority_footer_values(copy.offer, domain.settings.priority_link_info)
        priority_info = {
            'text': footer_text,
            'url': url,
        }

        priority_footer_block = domain.make_priority_block(footer_text, url, copy.offer.name)
    else:
        priority_info = {
            'text': None,
            'url': None,
        }
        priority_footer_block = ''

    if not lift_file_content:
        domain.save_copy_files(lift_file_content, sl_file_content, path_to_domain_results, str(copy),
                               priority_info, tracking_link, date)
        return

    lift_file_content = copy_helper.ImageHelper.process_images(copy, domain.styles_helper.image_block,
                                                               lift_file_content, date)

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
    cprint('make-domain (md) | apply-styles | add-domain | clear-cache | exit')
    action = cinput().strip()
    match action:
        case 'exit':
            exit()

        case 'clear-cache':
            print('Please specify clear all cache or specific offer, note that cache auto refreshes every 6 hours')
            option = cinput()
            copy_helper.Offer.clear_cache(option)

        case 'add-domain':
            cprint('To create new domain enter name it below. Name should be same as in broadcast')
            domain_name = cinput()
            copy_helper.settings.GeneralSettings.create_new_domain(domain_name)

        case 'make-domain' | 'md':
            path_to_domains = 'Settings/Domains/'
            if not os.path.exists(path_to_domains):
                os.makedirs(path_to_domains)

            cprint('To make domain, enter <domain-name>(full name or abbreviate) <date>(same as column in broadcast)')
            added_domains = []
            domain_folders_names = [entry.name for entry in os.scandir(path_to_domains) if entry.is_dir()]

            for domain_folder_name in domain_folders_names:
                abr_found = False
                for domain_abr, domain_full_name in copy_helper.settings.GeneralSettings.domains_short_names.items():
                    if domain_folder_name == domain_full_name:
                        added_domains.append(domain_abr + f' ({domain_folder_name})')
                        abr_found = True
                        break

                if not abr_found:
                    added_domains.append(domain_folder_name)

            cprint(f'Added domains : {', '.join(added_domains)}')

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

    logging.root = logger.logger

    copy_helper.settings.GeneralSettings.set_settings()
    logger.configure_console_logger(copy_helper.settings.GeneralSettings.logging_level)

    while True:
        try:
            main_page()
        except Exception as e:
            logging.critical('Got Unexpected Error!')
            logging.exception(e)
            print('Returning to main page')
