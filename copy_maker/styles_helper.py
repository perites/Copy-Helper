import logging
import random
import re

logger = logging.getLogger(__name__)


class StylesHelper:
    def __init__(self, styles_settings):
        self.styles_settings = styles_settings

    def apply_styles(self, copy):

        if self.styles_settings['antispam']:
            copy.lift_html = self.antispam_text(copy.lift_html, self.styles_settings['antispamReplacements'])

        if self.styles_settings['fontSize']:
            font_size = self.calculate_value(self.styles_settings['fontSize'])

            copy.lift_html, success = self.replace_style(r'font-size\s*:\s*(16|18)?px;',
                                                         f'font-size: {font_size};',
                                                         copy.lift_html)

        if self.styles_settings['fontFamily']:

            font_family = self.calculate_value(self.styles_settings['fontFamily'])

            copy.lift_html, success = self.replace_style(r'font-family\s*:\s*([^;]+);?',
                                                         f'font-family:{font_family};',
                                                         copy.lift_html)
            if not success:
                copy.lift_html = copy.lift_html.replace('Roboto', self.styles_settings['fontFamily'])

        if self.styles_settings['sideElementsPadding'] and self.styles_settings['upperDownElementsPadding']:
            upper_down_elements_padding = self.calculate_value(self.styles_settings['upperDownElementsPadding'])
            side_elements_padding = self.calculate_value(self.styles_settings['sideElementsPadding'])

            copy.lift_html, success = self.replace_style(r'padding\s*:\s*10px\s+25px',
                                                         f'padding:{upper_down_elements_padding} {side_elements_padding}',
                                                         copy.lift_html)

        if self.styles_settings['upperDownCopyPadding']:
            upper_down_copy_padding = self.calculate_value(self.styles_settings['upperDownCopyPadding'])

            copy.lift_html, success = self.replace_style(r'padding\s*:\s*(10|20)px\s+0(px|)',
                                                         f'padding:{upper_down_copy_padding} 0', copy.lift_html)

        if self.styles_settings['lineHeight']:
            line_height = self.calculate_value(self.styles_settings['lineHeight'])
            copy.lift_html, success = self.replace_style(r'line-height\s*:\s*1.5', f'line-height:{line_height}',
                                                         copy.lift_html)

        links_color = self.styles_settings['linksColor'] if self.styles_settings[
                                                                'linksColor'] != 'random-blue' else self.get_random_blue()
        add_es_button = self.styles_settings['addEsButton']
        copy.lift_html = self.change_links(copy.lift_html, links_color, add_es_button)

        return copy

    @staticmethod
    def get_random_blue():
        r = random.randint(0, 64)
        g = random.randint(48, 160)
        b = random.randint(192, 255)
        return f'#{r:02x}{g:02x}{b:02x}'

    @staticmethod
    def calculate_value(value):

        if isinstance(value, list):
            return random.choice(value)

        elif isinstance(value, dict):
            return round(random.uniform(value['min'], value['max']), 4)

        else:
            return value

    @staticmethod
    def replace_style(style_pattern, new_style, source):

        pattern = re.compile(style_pattern)
        if not pattern.search(source):
            return source, False

        new_lift_html = pattern.sub(lambda match: new_style, source)

        return new_lift_html, True

    @classmethod
    def change_links(cls, html_copy, link_color, add_es_button):
        a_tag_pattern = r'<a\s+([^>]*)'

        all_a_tags = re.findall(a_tag_pattern, html_copy)

        for old_a_tag in all_a_tags:
            new_a_tag = old_a_tag
            if link_color:
                new_a_tag = cls.change_link_color(link_color, old_a_tag)
            if add_es_button:
                new_a_tag = cls.add_es_button(new_a_tag)
                add_es_button = False

            html_copy = html_copy.replace(old_a_tag, new_a_tag, 1)

        return html_copy

    @classmethod
    def add_es_button(cls, a_tag):
        new_a_tag = a_tag + ' class="es-button"'
        return new_a_tag

    @classmethod
    def change_link_color(cls, link_color, a_tag):
        link_style = re.findall(r'style\s*=\s*"([^"]*)"', a_tag)
        if link_style:
            old_link_style = link_style[0]

            if ('background-color' in old_link_style) or ('background' in old_link_style):
                logger.debug('Button detected, not changing color')
                return a_tag

            new_link_style, success = cls.replace_style(r'(?<![-\w])color\s*:\s*([^;"]+)', f'color: {link_color}',
                                                        old_link_style)

            if not success:
                link_styles_list = old_link_style.split(';')
                link_styles_list.append(f'color: {link_color};')
                link_styles_list = list(filter(lambda el: el, link_styles_list))
                new_link_style = '; '.join(link_styles_list)

        else:
            old_link_style = ' '
            new_link_style = f' style="color: {link_color};" '

        new_a_tag = a_tag.replace(old_link_style, new_link_style)
        return new_a_tag

    @staticmethod
    def antispam_text(text, custom_replacements):

        replacements = {
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

        replacements = {**replacements, **custom_replacements}

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

    def make_priority_footer_html(self, footer_text, url):
        footer_link_keywords = [
            'edit your e-mail notification preferences or unsubscribe',
            'Privacy Policy',
            'unsubscribe here',
            'Unsubscribe Here',
            'click here',
            'here',
        ]

        footer_text = footer_text.replace('\n', '<br>')
        if not url:
            return footer_text

        for keyword in footer_link_keywords:
            if keyword in footer_text:
                unsub_footer_url = self.styles_settings['priorityBlockLink']

                unsub_footer_url = unsub_footer_url.replace('[PRIORITY_UNSUB_URL]', url)
                unsub_footer_url = unsub_footer_url.replace('[PRIORITY_UNSUB_TEXT_URL]', keyword)

                priority_block = footer_text.replace(keyword, unsub_footer_url)
                return priority_block

        logger.warning(f'No keyword was found in {footer_text}')
        footer_text += f'\n\nUNSUB-URL: {url}'
        return footer_text

    def add_template(self, copy):
        template = self.styles_settings['template']

        if copy.priority_info['is_priority']:
            priority_body = self.make_priority_footer_html(copy.priority_info['unsub_text'],
                                                           copy.priority_info['unsub_link'])

            priority_block = self.styles_settings['priorityBlock'].replace('[PRIORITY_BODY]', priority_body)

        else:
            priority_block = ''

        if not template:
            return copy.lift_html + '<br><br><br><br><br>' + priority_block

        template = template.replace('[COPY_HERE]', copy.lift_html)
        template = template.replace('[PRIORITY_FOOTER_HERE]', priority_block)

        copy.lift_html = template

        return copy
