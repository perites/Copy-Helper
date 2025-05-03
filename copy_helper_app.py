import datetime
import json
import logging
import os
import traceback

import logger


def cinput():
    prefix = f'{datetime.datetime.now():{logger.datefmt}} [INPUT] > '
    return input(prefix).strip()


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
        domain = copy_helper.domain.Domain(domain_name)
        return domain
    except FileNotFoundError:
        logging.info(
            f'Cant find domain {domain_identifier}, ensure that you entering name correctly and {domain_name} in Settings/Domains')
        return


def get_str_copies(domain, date):
    str_copies = domain.get_copies(date)
    if not str_copies:
        logging.info(
            'Copies were not found, you can enter them manually (separated by space as in brodcast) or just press enter to return to begining')
        str_copies = cinput().split(' ')

    return str_copies


def main_cycle():
    domain_dict = json.load(open('Settings/Domains/WorldFinReport.com/settings.json'))
    domain_dict['styles']['template'] = open('Settings/Domains/WorldFinReport.com/template.html').read()
    domain = copy_helper.domain.Domain(domain_dict)
    str_copies = domain.get_copies_from_broadcast('2/20')
    copies = [domain.create_copy(str_copy) for str_copy in str_copies]
    for copy in copies:
        copy = domain.find_copy(copy)
        copy = domain.make_tracking_link(copy)
        copy = domain.make_unsub_link(copy)

        copy = copy_helper.image_helper.ImageHelper.process_images(copy, domain.styles['imageBlock'])

        styles_helper = copy_helper.styles_helper.StylesHelper(domain.styles)
        copy = styles_helper.apply_styles(copy)
        copy = styles_helper.add_template(copy)
        copy.lift_html = copy.lift_html.replace('urlhere', copy.tracking_link)
        print(copy.lift_html)
        print(copy.lift_sls)
        print(copy.lift_images)
    exit()

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
            copy_helper.offer.OffersCache.clear_cache(option)

        case 'add-domain':
            logging.info('To create new domain enter name it below. Name should be same as in broadcast')
            domain_name = cinput()
            copy_helper.create_new_domain(domain_name)

        case 'make-domain' | 'md':

            logging.info(
                'To make domain, enter <domain-name> <date>(same as column in broadcast)')

            added_domains = get_added_domains(copy_helper.paths.PATH_TO_FOLDER_DOMAINS_SETTINGS)
            logging.info(f'Added domains : {', '.join(added_domains)}')

            domain_name_date_str = cinput().split(' ')
            if len(domain_name_date_str) != 2:
                logging.warning('Wrong input')
                return

            domain_name, broadcast_date = domain_name_date_str[0], domain_name_date_str[1]

            domain = get_domain(domain_name)
            if not domain:
                return

            str_copies = get_str_copies(domain, broadcast_date)
            if not str_copies:
                return

            copies_results = []
            for str_copy in str_copies:
                try:
                    copy_maker = copy_helper.copy_maker.CopyMaker(domain, str_copy, broadcast_date.replace('/', '.'))
                    results = copy_maker.make_copy()
                    copies_results.append(results)
                except copy_helper.copy_maker.CopyMakerException as e:
                    logging.error(
                        f'Error while making copy {str_copy} for domain {domain.name} for date {broadcast_date}. Details : {e}')

                except copy_helper.offer.OfferException as e:
                    logging.error(f'Error with offer {e.offer_name}. Details : {e}')

                except Exception as e:
                    logging.error(f'Unknown error while making copy {str_copy}. Details : {e}')
                    logging.debug(traceback.format_exc())

            logging.info(f'Finished making domain {domain.name} for date {broadcast_date}')
            for results in copies_results:
                logging.info(str(results))

            logging.info('======================')

        case 'apply-styles':
            logging.info(
                'To apply styles of domain to already saving copy, enter <domain-name> <date>(same as column in broadcast) <COPY>(copy that already saved in result directory)')

            domain_name, broadcast_date, str_copy = cinput().split(' ')
            domain = get_domain(domain_name)
            if not domain:
                return

            try:
                copy_maker = copy_helper.copy_maker.CopyMaker(domain, str_copy, broadcast_date.replace('/', '.'))
                results = copy_maker.make_copy(set_content_from_local=True)
                logging.info(str(results))
            except copy_helper.copy_maker.CopyMakerException as e:
                logging.error(
                    f'Error while making copy {str_copy} for domain {domain.name} for date {broadcast_date}. Details : {e}')

            except copy_helper.offer.OfferException as e:
                logging.error(f'Error with offer {e.offer_name}. Details : {e}')

            except Exception as e:
                logging.error(f'Unknown error while making copy {str_copy}. Details : {e}')
                logging.debug(traceback.format_exc())

            logging.info(f'Finished making copy {str_copy} for domain {domain.name}')
            logging.info('======================')


if __name__ == "__main__":
    logging.root = logger.logger
    import copy_helper

    logger.configure_console_logger(copy_helper.settings.GeneralSettings.logging_level)

    logging.info('Welcome to copy-helper test')

    while True:
        try:
            main_cycle()
        except Exception as e:
            logging.critical(f'Got Unexpected Error! Details : {e}')
            logging.debug(traceback.format_exc())
            logging.info('Returning to main page')
            exit()
