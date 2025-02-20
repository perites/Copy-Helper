# TODO SLs are writed two times
# TODO logs  , error handlaig
# TODO improve
# TODO change logging  debug to info in some places

import argparse
import copy_helper
import logging
import sys
import os
import shutil
import git
import os

# logging.root =
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] : %(message)s',
    datefmt='%d-%m %H:%M:%S:%M',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main-log', mode='a', encoding='utf-8', )
    ]
)
logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)

parser = argparse.ArgumentParser(prog="CopyHelper", description="Program that automates and makes easier copy making")

parser.add_argument('action', choices=['make-domain', 'apply-style'])
parser.add_argument('domainname')
parser.add_argument('date')

parser.add_argument('-cs', '--copies', type=lambda s: s.split(','))

parser.add_argument('-c', '--copy')
parser.add_argument('-l', '--link')

parser.add_argument('-cc', '--clearcache')


#
# def parse_args():
#     args = parser.parse_args()
#
#     name_from_short_name = copy_helper.settings.GeneralSettings.domains_short_names.get(args.domainname)
#     domain_name = name_from_short_name if name_from_short_name else args.domainname
#
#     date = args.date
#
#     if args.clearcache:
#         copy_helper.offer.Offer.clear_cache(args.clearcache)
#
#     match args.action:
#         case 'make-domain':
#
#             copies = args.copies
#             if not copies:
#                 copies = copy_helper.Domain.get_copies(domain_name, date)
#
#                 # path_to_domain_folder = f'{copy_helper.settings.GeneralSettings.result_directory}/{domain_name}'
#                 # dir_path = os.path.dirname(path_to_domain_folder)
#                 #
#                 # if os.path.exists(dir_path):
#                 #     shutil.rmtree(dir_path)
#                 # os.makedirs(dir_path, exist_ok=True)
#
#             for str_copy in copies:
#                 copy_helper.Domain.get_and_save_files(domain_name, date, str_copy)
#
#                 copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)
#                 print(priority_block)
#                 change_copy(domain_name, date, str_copy, copy_link, priority_block)
#
#         case 'apply-style':
#             str_copy = args.copy
#             copy_link = args.link
#             priority_block = ''
#             if not copy_link:
#                 copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)
#
#             change_copy(domain_name, date, str_copy, copy_link, priority_block)

#
# def change_copy(domain_name, date, str_copy, copy_link, priority_block):
#     path_to_date_folder = f'{copy_helper.GeneralSettings.result_directory}/{domain_name}/{date.replace('/', '.')}'
#
#     html = copy_helper.tools.FileHelper.read_file(f'{path_to_date_folder}/{str_copy}.html')
#
#     html = html.replace("urlhere", copy_link)
#     new_html = copy_helper.Domain.apply_styles(domain_name, html, priority_block)
#
#     if priority_block:
#         copy_helper.tools.FileHelper.write_to_file(f'{path_to_date_folder}/{str_copy}-PRIORITY.html', new_html)
#         os.remove(f'{path_to_date_folder}/{str_copy}.html')
#     else:
#         copy_helper.tools.FileHelper.write_to_file(f'{path_to_date_folder}/{str_copy}.html', new_html)


# def get_commits():
#     repo = git.Repo('.')  # Open the current repository
#     current_commit = repo.head.commit.hexsha  # Local commit
#     remote_commit = repo.git.ls_remote("origin", repo.active_branch.name).split()[0]  # Remote commit
#
#     return current_commit, remote_commit


def cprint(*args, **kwargs):
    prefix = '///>'
    print(prefix, *args, **kwargs)


def cinput(hint=''):
    prefix = '///> ' + hint
    return input(prefix)


def main_page():
    cprint('Type what you want to do:')
    cprint('make-domain, apply-styles, exit')
    action = cinput()
    match action:
        case 'exit':
            exit()

        case 'make-domain':
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
                copies = cinput().split(' ')

            copies = list(filter(lambda copy: copy, map(copy_helper.Copy.create, copies)))

            cprint(f'Successfully processed {len(copies)} copies.')

            path_to_domain_results = copy_helper.settings.GeneralSettings.result_directory + f'/{date.replace('/', '.')}/{domain.name}/'
            for copy in copies:
                lift_file_content, sl_file_content = domain.get_copy_files_content(copy)
                tracking_link = domain.make_tracking_link(copy)
                priority_footer_block = domain.make_priority_block(copy.offer.name)
                
                domain.save_copy_files(lift_file_content, sl_file_content, path_to_domain_results, str(copy),
                                       bool(priority_footer_block))

        case 'apply-styles':
            pass


if __name__ == "__main__":
    print('Welcome to copy-helper alfa version')
    copy_helper.settings.GeneralSettings.set_settings()
    while True:
        try:
            main_page()
        except Exception as e:
            logging.exception(e)
            print('Returning to main page')
            main_page()

    #
    # current_commit, remote_commit = get_commits()
    # if current_commit != remote_commit:
    #     print("New update available")
    #     print("To update you can run: git pull origin")
    # parse_args()
