# TODO SLs are writed two times
# TODO logs  , error handlaig
# TODO improve


import argparse
import copy_helper
import logging
import sys
import os
import shutil
import git

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] : %(message)s',
    datefmt='%d-%m %H:%M:%S:%M',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main-log', mode='a', encoding='utf-8', )
    ]
)

parser = argparse.ArgumentParser(prog="CopyHelper", description="Program that automates and makes easier copy making")

parser.add_argument('action', choices=['make-copies', 'apply-style'])
parser.add_argument('domainname')
parser.add_argument('date')

parser.add_argument('-cs', '--copies', type=lambda s: s.split(','))

parser.add_argument('-c', '--copy')
parser.add_argument('-l', '--link')

parser.add_argument('-cc', '--clearcache')


def parse_args():
    args = parser.parse_args()

    name_from_short_name = copy_helper.settings.GeneralSettings.domains_short_names.get(args.domainname)
    domain_name = name_from_short_name if name_from_short_name else args.domainname

    date = args.date

    if args.clearcache:
        copy_helper.tools.clear_cache(args.clearcache)

    match args.action:
        case 'make-copies':

            copies = args.copies
            if not copies:
                copies = copy_helper.Domain.get_copies(domain_name, date)

            if copy_helper.settings.GeneralSettings.clear_old_copies:

                path_to_domain_folder = f'{copy_helper.settings.GeneralSettings.result_directory}/{domain_name}/'
                dir_path = os.path.dirname(path_to_domain_folder)
                if os.path.exists(dir_path):
                    for filename in os.listdir(dir_path):
                        if filename == date.replace('/', '.'):
                            continue

                        file_path = os.path.join(dir_path, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.remove(file_path)  # Remove files
                            elif os.path.isdir(file_path):

                                shutil.rmtree(file_path)  # Remove subdirectories
                        except Exception as e:
                            print(f"Failed to delete {file_path}: {e}")

                # path_to_domain_folder = f'{copy_helper.settings.GeneralSettings.result_directory}/{domain_name}'
                # dir_path = os.path.dirname(path_to_domain_folder)
                #
                # if os.path.exists(dir_path):
                #     shutil.rmtree(dir_path)
                # os.makedirs(dir_path, exist_ok=True)

            for str_copy in copies:
                copy_helper.Domain.get_and_save_files(domain_name, date, str_copy)

                copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)
                print(priority_block)
                change_copy(domain_name, date, str_copy, copy_link, priority_block)

        case 'apply-style':
            str_copy = args.copy
            copy_link = args.link
            priority_block = ''
            if not copy_link:
                copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)

            change_copy(domain_name, date, str_copy, copy_link, priority_block)


def change_copy(domain_name, date, str_copy, copy_link, priority_block):
    path_to_date_folder = f'{copy_helper.GeneralSettings.result_directory}/{domain_name}/{date.replace('/', '.')}'

    html = copy_helper.tools.FileHelper.read_file(f'{path_to_date_folder}/{str_copy}.html')

    html = html.replace("urlhere", copy_link)
    new_html = copy_helper.Domain.apply_styles(domain_name, html, priority_block)

    if priority_block:
        copy_helper.tools.FileHelper.write_to_file(f'{path_to_date_folder}/{str_copy}-PRIORITY.html', new_html)
        os.remove(f'{path_to_date_folder}/{str_copy}.html')
    else:
        copy_helper.tools.FileHelper.write_to_file(f'{path_to_date_folder}/{str_copy}.html', new_html)


def get_commits():
    repo = git.Repo('.')  # Open the current repository
    current_commit = repo.head.commit.hexsha  # Local commit
    remote_commit = repo.git.ls_remote("origin", repo.active_branch.name).split()[0]  # Remote commit

    return current_commit, remote_commit


if __name__ == "__main__":
    copy_helper.settings.GeneralSettings.set_settings()

    current_commit, remote_commit = get_commits()
    if current_commit != remote_commit:
        print("New update available")
        print("To update you can run: git pull origin")
    parse_args()
