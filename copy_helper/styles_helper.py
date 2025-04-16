import logging
import re


class StylesHelper:
    def __init__(self, styles_settings):
        self.priority_footer_url_template = styles_settings['PriorityFooterUrlTemplate']
        self.links_color = styles_settings['LinksColor']
        self.font_family = styles_settings['FontFamily']
        self.font_size = styles_settings['FontSize']
        self.side_padding = styles_settings['SidePadding']
        self.upper_down_padding = styles_settings['UpperDownPadding']
        self.add_after_priority_block = styles_settings['AddAfterPriorityBlock']
        self.image_block = styles_settings['ImageBlock']

    def make_priority_footer_html(self, footer_text, url):
        footer_link_keywords = [
            'edit your e-mail notification preferences or unsubscribe',
            'Privacy Policy',
            'unsubscribe here',
            'here',
        ]

        if not url:
            priority_block = footer_text.replace('\n', '<br>')
            return priority_block

        for keyword in footer_link_keywords:
            if keyword in footer_text:
                unsub_footer_url = self.priority_footer_url_template

                unsub_footer_url = unsub_footer_url.replace('PRIORITY_FOOTER_URL', url)
                unsub_footer_url = unsub_footer_url.replace('PRIORITY_FOOTER_TEXT_URL', keyword)

                priority_block = footer_text.replace(keyword, unsub_footer_url)
                priority_block = priority_block.replace('\n', '<br>')
                return priority_block

        logging.warning(f'No keyword was found in {footer_text}')
        footer_text = footer_text.replace('\n', '<br>')
        footer_text += f'\n\nUNSUB-URL: {url}'
        return footer_text

    def apply_styles(self, lift_html):
        if self.links_color:
            lift_html = self.change_links_color(lift_html, self.links_color)

        if self.font_family:
            lift_html, success = self.replace_style('FontFamily', f'font-family:{self.font_family};', lift_html)
            if not success:
                lift_html = lift_html.replace('Roboto', self.font_family)

        if self.font_size:
            lift_html, success = self.replace_style('FontSize', f'font-size: {self.font_size};', lift_html)

        if self.side_padding:
            lift_html = lift_html.replace('padding:10px 25px', f'padding:10px {self.side_padding}')

        if self.upper_down_padding:
            lift_html = lift_html.replace('padding:20px 0', f'padding:{self.upper_down_padding} 0')
            lift_html = lift_html.replace('padding:10px 0', f'padding:{self.upper_down_padding} 0')

        return lift_html

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

    @staticmethod
    def replace_style(style_name, new_value, source):

        style_name_to_reqex = {'FontFamily': r'font-family\s*:\s*([^;]+);?',
                               'FontSize': r'font-size\s*:\s*(16|18)?px;',
                               'Color': r'color\s*:\s*([^;]+);?'}

        style_pattern = style_name_to_reqex[style_name]

        pattern = re.compile(style_pattern)
        if not pattern.search(source):
            return source, False

        new_lift_html = pattern.sub(lambda match: new_value, source)

        return new_lift_html, True

    @classmethod
    def change_links_color(cls, html_copy, link_color):
        a_tag_pattern = r'<a\s+([^>]*)'

        for old_a_tag in re.findall(a_tag_pattern, html_copy):
            new_a_tag = cls.change_link_color(link_color, old_a_tag)
            html_copy = html_copy.replace(old_a_tag, new_a_tag)

        return html_copy

    @classmethod
    def change_link_color(cls, link_color, a_tag):
        link_style = re.findall(r'style="([^"]*)"', a_tag)
        if link_style:
            old_link_style = link_style[0]
            new_link_style, success = cls.replace_style('Color', f'color: {link_color};', old_link_style)

            if not success:
                link_styles_list = old_link_style.split(';')
                link_styles_list.append(f'color: {link_color};')
                link_styles_list = list(filter(lambda el: el, link_styles_list))
                new_link_style = '; '.join(link_styles_list)

        else:
            old_link_style = ' '
            new_link_style = f' style="color: {link_color};"'

        new_a_tag = a_tag.replace(old_link_style, new_link_style)
        return new_a_tag
