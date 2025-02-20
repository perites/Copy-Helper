import dataclasses
import logging

from . import google_services
from . import settings

from . import tools

import re
import os


@dataclasses.dataclass
class DomainSettings:
    page: str
    tracking_link_info: dict
    priority_link_info: dict
    styles_settings: dict
    antispam: bool

    @classmethod
    def create_from_dict(cls, domain_info):
        return cls(
            page=domain_info['PageInBroadcast'],
            tracking_link_info=domain_info['TrackingLinkInfo'],
            priority_link_info=domain_info['CustomPriorityUnsubLinkInfo'],
            styles_settings=domain_info['StylesSettings'],
            antispam=domain_info['AntiSpam']
        )


class DomainStylesHelper:
    def __init__(self, styles_settings):
        self.priority_footer_url_template = styles_settings['PriorityFooterUrlTemplate']
        self.links_color = styles_settings['LinksColor']
        self.font_family = styles_settings['FontFamily']
        self.font_size = styles_settings['FontSize']
        self.side_padding = styles_settings['SidePadding']
        self.upper_down_padding = styles_settings['UpperDownPadding']
        self.add_after_priority_block = styles_settings['AddAfterPriorityBlock']

    def make_priority_footer_html(self, footer_text, url):
        footer_link_keywords = [
            'edit your e-mail notification preferences or unsubscribe',
            'Privacy Policy',
            'unsubscribe here',
            'unsubscribe',
            'click here',
        ]

        for keyword in footer_link_keywords:
            if keyword in footer_text:
                unsub_footer_url = self.priority_footer_url_template

                unsub_footer_url = unsub_footer_url.replace('PRIORITY_FOOTER_URL', url)
                unsub_footer_url = unsub_footer_url.replace('PRIORITY_FOOTER_TEXT_URL', keyword)

                priority_block = footer_text.replace(keyword, unsub_footer_url)
                priority_block = priority_block.replace('\n', '<br>')
                return priority_block

        logging.warning(f'No keyword was found in {footer_text}')
        footer_text = footer_text.repalace('\n', '<br>')
        footer_text += f'\nUNSUB-URL: {url}'
        return footer_text

    def apply_styles(self, lift_html):
        lift_html = self.change_links_color(lift_html, self.links_color)

        lift_html, success = self.replace_style('FontFamily', f'font-family:{self.font_family};', lift_html)
        if not success:
            lift_html = lift_html.replace('Roboto', self.font_family)

        lift_html, success = self.replace_style('FontSize', f'font-size: {self.font_size};', lift_html)

        html_copy = lift_html.replace('padding:10px 25px', f'padding:10px {self.side_padding}')
        html_copy = html_copy.replace('padding:20px 0', f'padding:{self.upper_down_padding} 0')
        html_copy = html_copy.replace('padding:10px 0', f'padding:{self.upper_down_padding} 0')

        return html_copy

    @staticmethod
    def antispam_text(text):

        replacements = settings.GeneralSettings.anti_spam_replacements

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

    @staticmethod
    def replace_style(style_name, new_value, lift_html):

        style_name_to_reqex = {'FontFamily': r'font-family\s*:\s*([^;]+);?',
                               'FontSize': r'font-size\s*:\s*(16|18)?px;',
                               'Color': r'color\s*:\s*([^;]+);?'}

        style_pattern = style_name_to_reqex[style_name]

        pattern = re.compile(style_pattern)
        if not pattern.search(lift_html):
            return lift_html, False

        new_lift_html = pattern.sub(lambda match: new_value, lift_html)

        return new_lift_html, True

    @classmethod
    def change_links_color(cls, html_copy, link_color):
        a_tag_pattern = r'<\ba\b[\S\s]*?>'

        for old_a_tag in re.findall(a_tag_pattern, html_copy):
            new_a_tag = cls.change_link_color(link_color, old_a_tag)
            html_copy = html_copy.replace(old_a_tag, new_a_tag)

        return html_copy

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


class DomainGoogleSheetsHelper(google_services.GoogleSheets):
    @classmethod
    def get_copies(cls, name, page, date):

        broadcast_id = settings.GeneralSettings.broadcast_id

        domain_index = cls.get_table_index_of_value(broadcast_id, name, f'{page}!1:1')

        if not domain_index:
            logging.warning(f'Could not find domain {name} in Broadcast')
            return

        date_index = cls.get_table_index_of_value(broadcast_id, date, f'{page}!A:A', False)
        if not domain_index:
            logging.warning(f'Could not find date {date} in Broadcast')
            return

        date_row = date_index + 1
        copies_range = f'{page}!{date_row}:{date_row}'
        copies_for_date = cls.get_data_from_range(broadcast_id, copies_range)
        copies_for_domain = copies_for_date[0][domain_index]
        if not copies_for_domain:
            logging.warning(f'Could not find copies in range {copies_range} in Broadcast')
            return

        return copies_for_domain.split(' ')

    @classmethod
    def get_priority_footer_values(cls, offer_name, priority_link_info):
        priority_products_table_id = settings.GeneralSettings.priority_products_table_id

        for page in ['Other PP', 'FIT']:
            priority_product_index = cls.get_table_index_of_value(priority_products_table_id, offer_name, f'{page}!A:A',
                                                                  is_row=False)

            if priority_product_index:
                page = page
                break

        if not priority_product_index:
            return None, None

        priority_product_index += 1

        text_value = cls.get_data_from_range(priority_products_table_id, f'{page}!C{priority_product_index}')[0][0]

        if priority_link_info:
            match priority_link_info['Type']:
                case 'VolumeGreen':
                    id = cls.get_data_from_range(priority_products_table_id, f'{page}!E{priority_product_index}')[0][0]

                    url = priority_link_info['Start'] + id + priority_link_info['End']

                case '':
                    url = cls.get_data_from_range(priority_products_table_id, f'{page}!F{priority_product_index}')[0][0]

                case _:
                    logging.warning('Unsupported priority link type, returning regular url')
                    url = cls.get_data_from_range(priority_products_table_id, f'{page}!F{priority_product_index}')[0][0]

        else:
            url = cls.get_data_from_range(priority_products_table_id, f'{page}!F{priority_product_index}')[0][0]

        return text_value, url


class Domain:
    def __init__(self, domain_name):
        self.name = domain_name
        self.settings = DomainSettings.create_from_dict(self.get_file_data('settings'))
        self.gsh_helper = DomainGoogleSheetsHelper()

        default_style_settings = settings.GeneralSettings.default_style_settings
        user_domain_styles_settings = self.settings.styles_settings

        self.styles_helper = DomainStylesHelper({**default_style_settings, **user_domain_styles_settings})

    def get_file_data(self, file_name):
        path_to_domain = f'Settings/Domains/{self.name}'
        match file_name:
            case 'settings':
                return tools.read_json_file(f'{path_to_domain}/settings.json')

            case 'template':
                with open('path_to_domain}/template.html', 'r', encoding='utf-8') as file:
                    return file.read()

    def get_copies(self, date):
        return self.gsh_helper.get_copies(self.name, self.settings.page, date)

    def apply_styles(self, lift_file_html):
        logging.info('Applying styles to copy')
        if not lift_file_html:
            logging.warning('Got nothing as lift file html')
            return ''

        return self.styles_helper.apply_styles(lift_file_html)

    def anti_spam_text(self, text):
        return self.styles_helper.antispam_text(text)

    @staticmethod
    def add_link_to_lift(tracking_link, lift_copy_html):
        return lift_copy_html.replace('urlhere', tracking_link)

    def add_template(self, html_copy, priority_block):
        template = self.get_file_data('template')

        if not template:
            return html_copy + "\n\n\n" + priority_block

        template = template.replace('<<<-COPY_HERE->>>', html_copy)

        done_template = template.replace('<<<-PRIORITY_FOOTER_HERE->>>',
                                         priority_block + self.styles_helper.add_after_priority_block if priority_block else "")

        return done_template

    def make_tracking_link(self, copy):
        try:
            logging.info(f'Creating link for domain {self.name} copy {str(copy)}')
            tracking_link_info = self.settings.tracking_link_info

            match tracking_link_info['Type']:
                case "RT TM":
                    tracking_link = tracking_link_info['Start'] + copy.offer.info.tracking_id('rt_tm') + \
                                    tracking_link_info[
                                        'End'] + str(copy)

                case 'IT2':
                    tracking_link = tracking_link_info['Start'] + copy.offer.info.tracking_id('volume_green') + \
                                    tracking_link_info[
                                        'End'] + f'{copy.offer.info.tracking_id('img_it')}_{copy.lift_number}{copy.img_code}'
                case _:
                    logging.warning(f"Got unsupported link type {tracking_link_info['Type']}")
                    tracking_link = tracking_link_info['Start'] + "UNSUPPORTED_TYPE" + tracking_link_info[
                        'End'] + "UNSUPPORTED_TYPE"

            return tracking_link

        except Exception:
            logging.exception(f'Error while creating tracking link for {self.name} copy {copy.name}')
            return 'ERROR_CREATING_LINK'

    def make_priority_block(self, offer_name):
        footer_text, url = self.gsh_helper.get_priority_footer_values(offer_name, self.settings.priority_link_info)
        if footer_text:
            logging.info(f'Priority footer was found for {offer_name}')
            priority_footer_html = self.styles_helper.make_priority_footer_html(footer_text, url)
            return priority_footer_html
        else:
            logging.info(f'No priority footer text was found for {offer_name}')
            return ''

    def get_copy_files_content(self, copy):
        try:
            lift_file, sl_file = copy.offer.get_copy_files(copy.lift_number)

            if lift_file:
                lift_file_content = self.get_copy_file_content(lift_file)
            else:
                logging.warning(f'Could not get lift file for offer {copy.offer.name}')
                lift_file_content = ''

            if sl_file:
                sl_file_content = self.get_copy_file_content(sl_file)
            else:
                logging.warning(f'Could not get sl file for offer {copy.offer.name}')
                sl_file_content = ''

            return lift_file_content, sl_file_content

        except Exception:
            logging.exception(f'Error while receiving lift files for copy {str(copy)}')
            return None, None

    @staticmethod
    def get_copy_file_content(copy_file):
        copy_file_content = google_services.GoogleDrive.get_file_content(copy_file)
        if not copy_file_content:
            logging.warning(f'Could not receive content of file {copy_file}')
            return ''

        return copy_file_content

    def save_copy_files(self, lift_file_content, sl_file_content, path_to_domain_results, str_copy, is_priority,
                        tracking_link):
        os.makedirs(path_to_domain_results, exist_ok=True)
        self.save_lift_file(lift_file_content, path_to_domain_results, str_copy, is_priority)
        self.save_sl_file(sl_file_content, path_to_domain_results, str_copy, is_priority, tracking_link)

    @staticmethod
    def save_lift_file(lift_file_content, path_to_domain_results, str_copy, is_priority):
        try:
            file_name = str_copy + ('-Priority' if is_priority else '')
            path = path_to_domain_results + f'{file_name}.html'
            with open(path, 'w', encoding='utf-8') as file:
                file.write(lift_file_content)
                logging.info(f'Successfully saved Copy file for {str_copy}')

        except Exception:
            logging.exception(f'Error while saving lift file for {str_copy}')

    @staticmethod
    def save_sl_file(sl_file_content, path_to_domain_results, str_copy, is_priority, tracking_link):
        try:
            path_to_sls_file = path_to_domain_results + 'SLs.txt'
            try:
                with open(path_to_sls_file, 'r', encoding='utf-8') as file:
                    sls_file_content = file.read()

                    if str_copy in sls_file_content:
                        logging.info(f'Did not add sls for {str_copy} in SLs.txt file as it already have them')
                        return

            except FileNotFoundError:
                pass

            copy_sls = (
                    str_copy + ('-Priority' if is_priority else '') + '\n\n' +

                    f'Tracking link:\n{tracking_link}\n\n' +

                    'Sls:\n' +

                    sl_file_content +

                    "\n----------------------------------------\n\n\n\n")

            with open(path_to_sls_file, 'a', encoding='utf-8') as file:
                file.write(copy_sls)
                logging.info(f'Successfully saved add sls for {str_copy} in SLs.txt')

        except Exception:
            logging.exception(f'Error while adding sls for {str_copy} in SLs.txt')
