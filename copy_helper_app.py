# TODO change logging  debug to info in some places
# TODO move get_priority_footer_values to offer
import logging
import logger
import copy_helper
import os
import datetime


def cinput():
    prefix = f'{datetime.datetime.now():{logger.datefmt}} [INPUT] > '
    return input(prefix).strip()


def process_copy_files_content(domain, copy, path_to_domain_results, lift_file_content, sl_file_content, date):
    tracking_link = domain.make_tracking_link(copy)

    if copy.offer.is_priority:
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

    lift_file_content = domain.apply_styles(lift_file_content, str(copy))

    if domain.settings.antispam:
        lift_file_content = domain.anti_spam_text(lift_file_content)
        priority_footer_block = domain.anti_spam_text(priority_footer_block)
        sl_file_content = domain.anti_spam_text(sl_file_content)

    lift_file_content = domain.add_template(lift_file_content, priority_footer_block)

    lift_file_content = domain.add_link_to_lift(tracking_link, lift_file_content)

    domain.save_copy_files(lift_file_content, sl_file_content, path_to_domain_results, str(copy),
                           priority_info, tracking_link, date)


def get_added_domains(path_to_domains):
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

    return added_domains


def get_domain_name(domain_identifier):
    domain_name = copy_helper.settings.GeneralSettings.domains_short_names.get(domain_identifier)

    if domain_name:
        return domain_name

    else:
        logging.debug(f'Did not found abbreviate {domain_identifier} in settings')
        return domain_identifier


def get_domain(domain_identifier):
    domain_name = get_domain_name(domain_identifier)
    try:
        domain = copy_helper.Domain(domain_name)
        return domain
    except FileNotFoundError:
        logging.info(
            f'Cant find that domain, ensure that you entering name correctly and {domain_name} in Settings/Domains')
        return


def get_str_copies(domain, date):
    str_copies = domain.get_copies(date)
    if not str_copies:
        logging.info(
            'Copies were not found for some reason, you can enter them manually (separated by space as in brodcast) or just press enter to return to begining')
        str_copies = cinput().split(' ')

    return str_copies


def main_cycle():
    logging.info('Type what you want to do:')
    logging.info('make-domain (md) | apply-styles | add-domain | clear-cache | exit')
    action = cinput()
    match action:
        case 'exit':
            exit()

        case 'clear-cache':
            logging.info(
                'Please specify clear all cache or specific offer, note that cache auto refreshes every 6 hours')
            option = cinput()
            copy_helper.Offer.clear_cache(option)

        case 'add-domain':
            logging.info('To create new domain enter name it below. Name should be same as in broadcast')
            domain_name = cinput()
            copy_helper.settings.GeneralSettings.create_new_domain(domain_name)

        case 'make-domain' | 'md':
            path_to_domains = 'Settings/Domains/'
            if not os.path.exists(path_to_domains):
                os.makedirs(path_to_domains)

            logging.info(
                'To make domain, enter <domain-name> <date>(same as column in broadcast)')

            added_domains = get_added_domains(path_to_domains)
            logging.info(f'Added domains : {', '.join(added_domains)}')

            domain_name_date_str = cinput().split(' ')
            if len(domain_name_date_str) != 2:
                logging.warning('Wrong input')
                return

            domain_name, date = domain_name_date_str[0], domain_name_date_str[1]

            domain = get_domain(domain_name)
            if not domain:
                return

            str_copies = get_str_copies(domain, date)
            if not str_copies:
                return

            copies = list(filter(lambda copy: copy, map(copy_helper.Copy.create, str_copies)))

            logging.info(f'Successfully processed {len(copies)} copies.')

            path_to_domain_results = copy_helper.settings.GeneralSettings.result_directory + f'/{domain.name}/{date.replace('/', '.')}/'
            for copy in copies:
                # copy_maker
                # copy_maker.get_copy_files()
                # copy_maker.create_track_link()
                # if copy_maker.copy.offer.is_priority:
                #     get_priority_footer_values
                #     make_priority_block
                # if not lift_file_content:
                #     save_copy_files
                # process_images
                # apply_styles
                # if domain.settings.antispam:
                #     ...
                # add_template
                # add_link_to_lift
                # save_copy_files

                lift_file_content, sl_file_content = copy.get_copy_files_content()
                process_copy_files_content(domain, copy, path_to_domain_results, lift_file_content, sl_file_content,
                                           date.replace('/', '.'))

            logging.info(f'Finished making domain {domain.name} for date {date}')
            logging.info('======================')

        case 'apply-styles':
            logging.info(
                'To apply styles of domain to already saving copy, enter <domain-name> <date>(same as column in broadcast) <COPY>(copy that already saved in result directory)')

            domain_name, date, str_copy = cinput().split(' ')

            domain = get_domain(domain_name)
            if not domain:
                return

            path_to_domain_results = copy_helper.settings.GeneralSettings.result_directory + f'/{domain.name}/{date.replace('/', '.')}/'
            logging.info(f'Trying to read {path_to_domain_results + str_copy}.html')

            try:
                with open(path_to_domain_results + f'{str_copy}.html', 'r', encoding='utf-8') as file:
                    lift_file_content = file.read()

            except FileNotFoundError:
                logging.warning('Copy file not found')
                return

            process_copy_files_content(domain, copy_helper.Copy.create(str_copy), path_to_domain_results,
                                       lift_file_content, "", date.replace('/', '.'))


if __name__ == "__main__":
    logging.root = logger.logger

    logging.info('Welcome to copy-helper test')

    copy_helper.settings.GeneralSettings.set_settings()
    logger.configure_console_logger(copy_helper.settings.GeneralSettings.logging_level)

    while True:
        try:
            main_cycle()
        except Exception as e:
            logging.critical('Got Unexpected Error!')
            logging.exception(e)
            logging.info('Returning to main page')
