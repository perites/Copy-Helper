import argparse
import copy_helper
import logging
import sys

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

parser.add_argument('action', choices=['make-copies', 'apply-styles'])
parser.add_argument('-dn', '--domainname')
parser.add_argument('-d', '--date')

parser.add_argument('-cs', '--copies', type=lambda s: s.split(','))

parser.add_argument('-c', '--copy')
parser.add_argument('-l', '--link')


def parse_args():
    args = parser.parse_args()
    match args.action:
        case 'make-copies':
            name_from_short_name = copy_helper.settings.GeneralSettings.domains_short_names.get(args.domainname)
            domain_name = name_from_short_name if name_from_short_name else args.domainname
            date = args.date

            copies = args.copies
            if not copies:
                copies = copy_helper.Domain.get_copies(domain_name, date)

            for str_copy in copies:
                copy_helper.Domain.get_and_save_files(domain_name, date, str_copy)
                apply_style(domain_name, date, str_copy)

        case 'apply-style':
            name_from_short_name = copy_helper.settings.GeneralSettings.domains_short_names.get(args.domainname)
            domain_name = name_from_short_name if name_from_short_name else args.domainname
            date = args.date
            str_copy = args.copy

            copy_link = args.link
            priority_block = [None, None]
            if not copy_link:
                copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)

            change_copy(domain_name, date, str_copy, copy_link, priority_block)


def apply_style(domain_name, date, str_copy):
    copy_link, priority_block = copy_helper.Domain.make_links(domain_name, str_copy)
    change_copy(domain_name, date, str_copy, copy_link, priority_block)


def change_copy(domain_name, date, str_copy, copy_link, priority_block):
    path_to_file = f'{copy_helper.GeneralSettings.result_directory}/{domain_name}/{date.replace('/', '.')}/{str_copy}.html'

    html = copy_helper.tools.FileHelper.read_file(path_to_file)

    html = html.replace("urlhere", copy_link)
    new_html = copy_helper.Domain.apply_styles(domain_name, html, priority_block)

    copy_helper.tools.FileHelper.write_to_file(path_to_file, new_html)


if __name__ == "__main__":
    copy_helper.settings.GeneralSettings.set_settings()
    parse_args()
