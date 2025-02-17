import logging

from . import google_services
from . import settings

from . import tools
from bs4 import BeautifulSoup

from . import offer

import shutil
import os


class Domain:

    @staticmethod
    def get_copies(name, date):
        domain_settings = tools.FileHelper.read_json_data(f'Settings/Domains/{name}/general.json')
        page = domain_settings['PageInBroadcast']

        domain_index = google_services.GoogleSheets.get_table_index_of_value(settings.GeneralSettings.broadcast_id,
                                                                             name,
                                                                             f'{page}!1:1')
        date_index = google_services.GoogleSheets.get_table_index_of_value(settings.GeneralSettings.broadcast_id, date,
                                                                           f'{page}!A:A',
                                                                           False)

        date_row = date_index + 1

        copies_for_date = google_services.GoogleSheets.get_data_from_range(settings.GeneralSettings.broadcast_id,
                                                                           f'{page}!{date_row}:{date_row}')
        copies_for_domain = copies_for_date[0][domain_index]

        return copies_for_domain.split(' ')

    @classmethod
    def apply_styles(cls, name, html_copy, priority_block):

        default_style_settings = tools.FileHelper.read_json_data(f'Settings/General-Setting.json').get('DefaultStyles')
        user_domain_styles_settings = tools.FileHelper.read_json_data(f'Settings/Domains/{name}/styles.json')

        domain_styles_settings = default_style_settings
        if user_domain_styles_settings:
            domain_styles_settings = {**default_style_settings, **user_domain_styles_settings}

        html_copy = cls.change_link_style(html_copy, domain_styles_settings['LinkColor'])
        html_copy, success = tools.RegExHelper.regex_replace('FontFamily', html_copy,
                                                             f'font-family:{domain_styles_settings['FontFamily']};')
        if not success:
            html_copy = html_copy.replace('Roboto', domain_styles_settings['FontFamily'])

        html_copy, success = tools.RegExHelper.regex_replace('FontSize', html_copy,
                                                             f'font-size: {domain_styles_settings['FontSize']};')

        html_copy = html_copy.replace('padding:10px 25px', f'padding:10px {domain_styles_settings['LeftRightPadding']}')
        html_copy = html_copy.replace('padding:20px 0', f'padding:{domain_styles_settings['UpperDownPadding']} 0')

        # priority_block_text = ''
        # if priority_block[0]:
        #     priority_block_text, priority_block_url = priority_block[0], priority_block[1]
        #
        #     priority_block_url_text = domain_styles_settings['PriorityFooterUrl'].replace('PRIORITY_FOOTER_URL',
        #                                                                                   priority_block_url)
        #     if priority_block_url_text:
        #         priority_block_text += f'<br>{priority_block_url_text}'

        domain_general_settings = tools.FileHelper.read_json_data(f'Settings/Domains/{name}/general.json')
        if domain_general_settings['AntiSpam'] == 'yes':
            html_copy = cls.anti_spam_text(html_copy)

        html_copy = cls.add_template(name, html_copy, priority_block)
        return html_copy

    @staticmethod
    def anti_spam_text(text):
        default_replacements = {
            'A': 'А',
            'E': 'Е',
            'I': 'І',
            'O': 'О',
            'P': 'Р',
            'T': 'Т',
            'H': 'Н',
            'K': 'К',
            'X': 'Х',
            'C': 'С',
            'B': 'В',
            'M': 'М',
            'e': 'е',
            'y': 'у',
            'i': 'і',
            'o': 'о',
            'a': 'а',
            'x': 'х',
            'c': 'с',
            '%': '％',
            '$': '＄',
        }
        user_replacements = tools.FileHelper.read_json_data('Settings/General-Setting.json').get('AntiSpamReplacements')
        replacements = {**default_replacements, **user_replacements}

        new_text = ''
        is_inside_tag = False
        entity = ''
        for char in text:

            if char == '<':
                is_inside_tag = True

            elif char == '>':
                is_inside_tag = False

            replaced_char = replacements.get(char) or char if not is_inside_tag else char

            new_text += replaced_char

        return new_text
        # if char == "&":
        #     entity = '&'
        # elif char == ";" and entity:
        #     entity += ';'
        #     replaced_char = replacements.get(entity) if replacements.get(entity) else char
        #     entity = ''
        # elif entity:
        #     entity += char
        #
        #
        # replaced_char = char

    @classmethod
    def change_link_style(cls, html_copy, link_color):
        soup = BeautifulSoup(html_copy, 'html.parser')
        for a_tag in soup.find_all('a', style=True):
            link_style = a_tag['style']
            link_style, success = tools.RegExHelper.regex_replace('LinkColor', link_style,
                                                                  f'color: {link_color};')
            if not success:
                link_style_list = link_style.split(';')
                link_style_list.append(f'color: {link_color};')
                link_style_list = list(filter(lambda el: el, link_style_list))
                link_style = '; '.join(link_style_list)

            a_tag['style'] = link_style

        return soup.prettify()

    @classmethod
    def add_template(cls, name, html_copy, priority_block):
        template = tools.FileHelper.read_file(f'Settings/Domains/{name}/template.html')

        if not template:
            return

        done_template = template.replace('<<<-COPY_HERE->>>', html_copy)

        done_template = done_template.replace('<<<-PRIORITY_FOOTER_HERE->>>',
                                              priority_block + "<br><br>" if priority_block else "")

        return done_template

    @classmethod
    def make_links(cls, name, str_copy):
        domain_settings = tools.FileHelper.read_json_data(f'Settings/Domains/{name}/general.json')
        offer_name, lift_number, img_code = tools.RegExHelper.match_str_copy(str_copy)

        tracking_link = cls.make_tracking_link(domain_settings['TrackingLink'], offer_name, lift_number, img_code)
        priority_block = cls.get_priority_block(domain_settings['PriorityLink'], offer_name)

        return tracking_link, priority_block

    @classmethod
    def make_tracking_link(cls, domain_tracking_link_settings, offer_name, lift_number, img_code):

        offer_info = offer.Offer.get_offer_info(offer_name)

        match domain_tracking_link_settings['Type']:
            case "RT TM":
                link = domain_tracking_link_settings['Start'] + offer_info["rt_tm"] + domain_tracking_link_settings[
                    'End'] + offer_name + lift_number + img_code

            case 'IT2':
                link = domain_tracking_link_settings['Start'] + offer_info["volume_green"] + \
                       domain_tracking_link_settings[
                           'End'] + f'{offer_info['img_it']}_{lift_number}{img_code}'
            case _:
                logging.warning(f"Got unsupported link type {domain_tracking_link_settings['Type']}")
                link = None

        return link

    @classmethod
    def get_priority_block(cls, domain_priority_link_settings, offer_name):

        priority_products_table_id = '1e40khWM1dKTje_vZi4K4fL-RA8-D6jhp2wmZSXurQH0'

        priority_product_index = google_services.GoogleSheets.get_table_index_of_value(priority_products_table_id,
                                                                                       offer_name,
                                                                                       'Other PP!A:A',
                                                                                       is_row=False)
        page = 'Other PP'

        if not priority_product_index:
            priority_product_index = google_services.GoogleSheets.get_table_index_of_value(priority_products_table_id,
                                                                                           offer_name, "FIT!A:A",
                                                                                           is_row=False)
            page = 'FIT'

        if not priority_product_index:
            return ''

        text_value = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                      f'{page}!C{priority_product_index + 1}')[0][0]
        if domain_priority_link_settings:
            match domain_priority_link_settings['Type']:
                case 'VolumeGreen':
                    id = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                          f'{page}!E{priority_product_index + 1}')[0][0]

                    url = domain_priority_link_settings['Start'] + id + domain_priority_link_settings['End']

                case _:
                    url = None

        else:
            url = google_services.GoogleSheets.get_data_from_range(priority_products_table_id,
                                                                   f'{page}!F{priority_product_index + 1}')[0][0]

        return cls.make_priority_block(text_value, url)

    @classmethod
    def make_priority_block(cls, text_value: str, url):
        footer_link_keywords = [
            'edit your e-mail notification preferences or unsubscribe',
            'Privacy Policy',
            'unsubscribe here',
            'unsubscribe',
            'click here',
        ]

        for keyword in footer_link_keywords:
            if keyword in text_value:
                style_url = tools.FileHelper.read_json_data('Settings/Domains/WorldFinReport.com/styles.json')[
                    'PriorityFooterUrl']

                # print(url, 'before')

                style_url = style_url.replace('PRIORITY_FOOTER_URL', url)
                style_url = style_url.replace('PRIORITY_FOOTER_TEXT_URL', keyword)
                # print(url, 'afret')
                priority_block = text_value.replace(keyword, style_url)
                priority_block = priority_block.replace('\n', '<br>')
                return priority_block

        logging.warning(f'No keyword was found in {text_value}')
        return ''

    @classmethod
    def get_and_save_files(cls, domain_name, date, str_copy):
        offer_name, lift_number, img_code = tools.RegExHelper.match_str_copy(str_copy)

        google_drive_folder_id = offer.Offer.get_offer_info(offer_name)['google_drive_folder_id']

        copy_file, sl_file = offer.Offer.get_lift_files(offer_name, google_drive_folder_id, lift_number)

        copy_file_content = google_services.GoogleDrive.get_file_content(copy_file)
        sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
        sl_file_content = (f'{str_copy}\n----------------------------------------\n' + sl_file_content +
                           "\n----------------------------------------\n\n\n")

        path_to_domain_folder = f'{settings.GeneralSettings.result_directory}/{domain_name}'

        tools.FileHelper.write_to_file(
            f'{path_to_domain_folder}/{date.replace('/', '.')}/{str_copy}.html',
            copy_file_content)

        info_file_text = tools.FileHelper.read_file(
            f'{path_to_domain_folder}/info.txt')

        if info_file_text and (str_copy in info_file_text):
            return

        tools.FileHelper.write_to_file(
            f'{path_to_domain_folder}/{date.replace('/', '.')}/info.txt',
            sl_file_content, 'a')
