import random
import string
from kivy.core.text import Label as CoreLabel
from textwrap import fill


class StringLines():

    def estimate_columns(self, font_size, widget_width):
        s = ''.join(random.choices(string.ascii_lowercase, k = 80)) +\
            ''.join(random.choices(string.ascii_uppercase, k = 20))
        l = CoreLabel(font_size= font_size)
        per_char = l.get_extents(s)[0] // 100
        return widget_width // per_char -1

    def multiline_string(self, string, max_columns, max_lines = None):
        if len(string) > max_columns:
            multiline = fill(str(string), max_columns)
            if max_lines:
                # Setting max_lines may truncate the string
                lines = multiline.split('\n')
                return '\n'.join(lines[:max_lines])
            else:
                return multiline
        else:
            return string
