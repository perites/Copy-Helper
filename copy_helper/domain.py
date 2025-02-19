import dataclasses
import logging

from . import google_services
from . import settings

from . import tools

from . import offer as offer_cls

import re


@dataclasses.dataclass
class DomainSettings:
    page: str

    @classmethod
    def create_from_dict(cls, domain_info):
        return cls(
            page=domain_info['PageInBroadcast']
        )


class DomainGoogleSheetsHelper(google_services.GoogleSheets):
    @staticmethod
    def _get_copies(name, page, date):
        domain_index = google_services.GoogleSheets.get_table_index_of_value(settings.GeneralSettings.broadcast_id,
                                                                             name,
                                                                             f'{page}!1:1')

        if not domain_index:
            logging.warning(f'Could not find domain {name} in Broadcast')
            return

        date_index = google_services.GoogleSheets.get_table_index_of_value(settings.GeneralSettings.broadcast_id, date,
                                                                           f'{page}!A:A',
                                                                           False)
        if not domain_index:
            logging.warning(f'Could not find date {date} in Broadcast')
            return

        date_row = date_index + 1
        copies_range = f'{page}!{date_row}:{date_row}'
        copies_for_date = google_services.GoogleSheets.get_data_from_range(settings.GeneralSettings.broadcast_id,
                                                                           copies_range)
        copies_for_domain = copies_for_date[0][domain_index]
        if not copies_for_domain:
            logging.warning(f'Could not find copies in range {copies_range} in Broadcast')
            return

        return copies_for_domain.split(' ')


class Domain(DomainGoogleSheetsHelper):
    def __init__(self, domain_name):
        self.name = domain_name
        self.settings = DomainSettings.create_from_dict(self.get_file_data('settings'))

    def get_file_data(self, file_name):
        path_to_domain = f'Settings/Domains/{self.name}'
        match file_name:
            case 'settings':
                return tools.read_json_file(f'{path_to_domain}/general.json')

            case 'styles':
                return tools.read_json_file(f'{path_to_domain}/styles.json')

            case 'template':
                return tools.read_json_file(f'{path_to_domain}/template.html')

    def get_copies(self, date):
        return self._get_copies(self.name, self.settings.page, date)

    @classmethod
    def apply_styles(cls, name, html_copy, priority_block):

        default_style_settings = tools.FileHelper.read_json_data(f'Settings/General-Setting.json').get('DefaultStyles')
        user_domain_styles_settings = tools.FileHelper.read_json_data(f'Settings/Domains/{name}/styles.json')

        domain_styles_settings = default_style_settings
        if user_domain_styles_settings:
            domain_styles_settings = {**default_style_settings, **user_domain_styles_settings}

        html_copy = cls.change_links_color(html_copy, domain_styles_settings['LinkColor'])
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
        inside_tag = False
        inside_entity = False
        for char in text:

            match char:
                case '<':
                    inside_tag = True

                case '>':
                    inside_tag = False

                case '&':
                    inside_entity = True

                case ';':
                    inside_entity = False

            if (not inside_tag) and (not inside_entity) and replacements.get(char):
                replaced_char = replacements.get(char)
            else:
                replaced_char = char

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

    @staticmethod
    def change_link_color(link_color, a_tag):
        link_style = re.findall(r'style=".*?"', a_tag)
        if link_style:
            old_link_style = link_style[0].split('"')[1]
            new_link_style, success = tools.RegExHelper.regex_replace('Color', old_link_style,
                                                                      f'color: {link_color};')
            if not success:
                link_styles_list = old_link_style.split(';')
                link_styles_list.append(f'color: {link_color};')
                link_styles_list = list(filter(lambda el: el, link_styles_list))
                new_link_style = '; '.join(link_styles_list)

        else:
            old_link_style = ' '
            new_link_style = f'style="color: {link_color};"'

        new_a_tag, _ = tools.RegExHelper.regex_replace(old_link_style, a_tag, new_link_style)

        return new_a_tag

    @classmethod
    def change_links_color(cls, html_copy, link_color):  # dark html staff here
        a_tag_pattern = r'<\ba\b[\S\s]*?>'

        for old_a_tag in re.findall(a_tag_pattern, html_copy):
            new_a_tag = cls.change_link_color(link_color, old_a_tag)
            html_copy = html_copy.replace(old_a_tag, new_a_tag)

        return html_copy

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
        try:
            offer = offer_cls.Offer(offer_name)
        except Exception as e:
            logging.error(e)
            return None

        match domain_tracking_link_settings['Type']:
            case "RT TM":
                link = domain_tracking_link_settings['Start'] + offer.info.tracking_id('rt_tm') + \
                       domain_tracking_link_settings['End'] + offer_name + lift_number + img_code

            case 'IT2':
                link = domain_tracking_link_settings['Start'] + offer.info.tracking_id('volume_green') + \
                       domain_tracking_link_settings[
                           'End'] + f'{offer.info.tracking_id('img_it')}_{lift_number}{img_code}'
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

    def save_copy_files(self, copy, path_to_domain_results):
        lift_file, sl_file = copy.offer.get_copy_files(copy.lift_number)

        if lift_file:
            self.save_lift_file(lift_file, path_to_domain_results, str(copy))
        else:
            logging.warning(f'Could not get copy file for offer {copy.offer.name}')

        if sl_file:
            self.get_and_save_files(sl_file, path_to_domain_results, str(copy))
        else:
            logging.warning(f'Could not get sl file for offer {copy.offer.name}')

    @staticmethod
    def save_lift_file(copy_file, path_to_domain_results, str_copy):
        try:
            copy_file_content = google_services.GoogleDrive.get_file_content(copy_file)
            if not copy_file_content:
                logging.warning(f'Could nor receive content of file {copy_file}')
                return

            path = path_to_domain_results + f'{str_copy}.html'
            with open(path, 'r', encoding='utf-8') as file:
                file.write(copy_file)

        except Exception:
            logging.exception(f'Error while saving copy file {copy_file} for {str_copy}')

    @staticmethod
    def save_sl_file(sl_file, path_to_domain_results, str_copy):
        try:
            sl_file_content = google_services.GoogleDrive.get_file_content(sl_file)
            if not sl_file_content:
                logging.warning(f'Could nor receive content of file {sl_file}')
                return

            path_to_sls_file = f'{path_to_domain_results}/SLs.txt'
            try:
                with open(path_to_sls_file, 'r', encoding='utf-8') as file:
                    sls_file_content = file.read()

                    print(sls_file_content)

                    if str_copy in sls_file_content:
                        return

            except FileNotFoundError:
                pass

            copy_sls = (f'{str_copy}\n----------------------------------------\n' + sl_file_content +
                        "\n----------------------------------------\n\n\n")

            with open(path_to_sls_file, 'a', encoding='utf-8') as file:
                file.write(copy_sls)


        except Exception:
            logging.exception(f'Error while saving sl file {sl_file} for {str_copy}')
