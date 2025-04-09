import logging
import os

from . import tools

PATH_TO_FOLDER_SYSTEM_DATA = 'SystemData/'
PATH_TO_FOLDER_GENERAL_SETTINGS = 'Settings/'
PATH_TO_FOLDER_DOMAINS_SETTINGS = PATH_TO_FOLDER_GENERAL_SETTINGS + 'Domains/'

PATH_TO_FILE_OFFERS_CACHE = PATH_TO_FOLDER_SYSTEM_DATA + 'offers_info_cache.json'
PATH_TO_FILE_GENERAL_SETTINGS = PATH_TO_FOLDER_GENERAL_SETTINGS + 'General-Settings.json'
PATH_TO_FILE_OAUTH = PATH_TO_FOLDER_SYSTEM_DATA + 'OAuth_Client.json'


def create_general_settings():
    logging.info('Creating General Settings')
    tools.write_json_file(PATH_TO_FILE_GENERAL_SETTINGS, {
        "YourTeamBroadcastSheetID": "",
        "FolderWithPartners": "1-WFEkKNjVjaJDNt2XKBeJhpIQUviBVim",
        "PriorityProductsTableId": "1e40khWM1dKTje_vZi4K4fL-RA8-D6jhp2wmZSXurQH0",
        "DirectoryToStoreResults": "",
        "ResultDirectoryType": "",
        "AutoImagesSavePath": "",
        "Niche": "Finance",
        "InformationLevel": "All",
        "DomainsShortNames": {
            "DOMAIN_ABR": "DomainNameAsInBroadcast"
        },
        "DefaultStyles": {
            "FontSize": "21px",
            "FontFamily": "Roboto",
            "LinksColor": "#2402fb",
            "SidePadding": "30px",
            "UpperDownPadding": "10px",
            "AddAfterPriorityBlock": "<br><br>",
            "PriorityFooterUrlTemplate": "<b><a target=\"_blank\" href=\"PRIORITY_FOOTER_URL\" style=\"text-decoration: underline; color: #ffffff;\">PRIORITY_FOOTER_TEXT_URL</a></b>",
            "ImageBlock": "<table align=\"center\"><tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr>\n<tr>\n  <td class=\"img-bg-block\" align=\"center\">\n    <a href=\"urlhere\" target=\"_blank\">\n      <img alt=\"ALT_TEXT\" height=\"auto\" src=\"IMAGE_URL\" style=\"border:0;display:block;outline:none;text-decoration:none;height:auto;width:100%;max-width: 550px;font-size:13px;\" width=\"280\" />\n        </a>\n  </td>\n</tr>\n<tr>\n  <td height=\"20\" width=\"100%\" style=\"max-width: 100%\" class=\"horizontal-space\"></td>\n</tr></table>"
        },
        "AntiSpamReplacements": {
            "A": "А",
            "E": "Е",
            "I": "І",
            "O": "О",
            "P": "Р",
            "T": "Т",
            "H": "Н",
            "K": "К",
            "X": "Х",
            "C": "С",
            "B": "В",
            "M": "М",
            "e": "е",
            "y": "у",
            "i": "і",
            "o": "о",
            "a": "а",
            "x": "х",
            "c": "с",
            "%": "％",
            "$": "＄"
        }
    })


def create_new_domain(domain_name):
    if not domain_name:
        logging.warning('Domain Name cant be empty')
        return
    logging.info('Creating new Domain')
    domain_folder_path = PATH_TO_FOLDER_DOMAINS_SETTINGS + f'{domain_name}/'
    try:
        os.makedirs(domain_folder_path)
    except FileExistsError:
        logging.warning('Domain must have unique name')
        return
    tools.write_json_file(domain_folder_path + f'settings.json', {
        "Name": f"{domain_name}",
        "PageInBroadcast": "",
        "AntiSpam": False,
        "TrackingLinkInfo": {
            "Type": "",
            "Start": "",
            "End": ""
        },
        "CustomPriorityUnsubLinkInfo": {
            "Type": "",
            "Start": "",
            "End": ""
        },
        "StylesSettings": {
        }
    })

    with open(domain_folder_path + 'template.html', 'w', encoding='utf-8') as file:
        file.write('''
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->
<!--COPY_STARTS_HERE-->


<<<-COPY_HERE->>> 


<!--COPY_END_HERE-->
<!--COPY_END_HERE-->
<!--COPY_END_HERE-->
<!--COPY_END_HERE-->





<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->
<!--FOOTER_START_HERE-->



<<<-PRIORITY_FOOTER_HERE->>>



<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
<!--FOOTER_END_HERE-->
''')


def validate_paths():
    if not os.path.exists(PATH_TO_FOLDER_SYSTEM_DATA):
        logging.debug(f'Creating {PATH_TO_FOLDER_SYSTEM_DATA}')
        os.makedirs(PATH_TO_FOLDER_SYSTEM_DATA)

    if not os.path.exists(PATH_TO_FILE_OFFERS_CACHE):
        logging.debug(f'Creating {PATH_TO_FILE_OFFERS_CACHE} with without data')
        with open(PATH_TO_FILE_OFFERS_CACHE, 'w', encoding='utf-8') as file:
            file.write('{}')

    if not os.path.exists(PATH_TO_FOLDER_GENERAL_SETTINGS):
        logging.debug(f'Creating {PATH_TO_FOLDER_GENERAL_SETTINGS}')
        os.makedirs(PATH_TO_FOLDER_GENERAL_SETTINGS)

    if not os.path.exists(PATH_TO_FILE_GENERAL_SETTINGS):
        create_general_settings()

    if not os.path.exists(PATH_TO_FOLDER_DOMAINS_SETTINGS):
        os.makedirs(PATH_TO_FOLDER_DOMAINS_SETTINGS)
        create_new_domain('DomainNameAsInBroadcast')

    if not os.path.exists(PATH_TO_FILE_OAUTH):
        logging.warning('Put OAuth_Client.json file inside SystemData folder')
        exit()


validate_paths()
