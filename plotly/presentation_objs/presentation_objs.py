"""
dashboard_objs
==========

A module for creating and manipulating spectacle-presentation dashboards.
"""

import copy
import random
import re
import string
import warnings

from plotly import exceptions, optional_imports

IPython = optional_imports.get_module('IPython')

HEIGHT = 700.0
WIDTH = 1000.0

CODEPANE_THEMES = ['tomorrow', 'tomorrowNight']
VALID_STYLE_KEYS = ['fontFamily', 'fontSize', 'margin', 'position',
                    'textAlign', 'opacity', 'color', 'fontStyle',
                    'fontWeight', 'lineHeight', 'minWidth', 'textDecoration',
                    'wordBreak']
VALID_PROPS_KEYS = ['theme', 'listType', 'href']
NEEDED_STYLE_KEYS = ['left', 'top', 'height', 'width']
VALID_LANGUAGES = ['cpp', 'cs', 'css', 'fsharp', 'go', 'haskell', 'java',
                   'javascript', 'jsx', 'julia', 'xml', 'matlab', 'php',
                   'python', 'r', 'ruby', 'scala', 'sql', 'yaml']
VALID_CLASS_STYLES = ['pictureleft', 'pictureright', 'picturemiddle',
                      'pictureleft_tiled', 'pictureright_tiled']

VALID_SLIDE_PROPS = ['class', 'transition', 'background-image',
                     'background-position', 'background-repeat',
                     'background-size', 'background_color']

VALID_TRANSITIONS = ['slide',  'zoom', 'fade', 'spin']

PRES_THEMES = ['moods', 'martik']

VALID_GROUPTYPES = [
    'leftgroup_v', 'rightgroup_v', 'middle', 'checkerboard_topleft',
    'checkerboard_topright'
]

fontWeight_dict = {
    'Thin': {'fontWeight': 100},
    'Thin Italic': {'fontWeight': 100, 'fontStyle': 'italic'},
    'Light': {'fontWeight': 300},
    'Light Italic': {'fontWeight': 300, 'fontStyle': 'italic'},
    'Regular': {'fontWeight': 400},
    'Regular Italic': {'fontWeight': 400, 'fontStyle': 'italic'},
    'Medium': {'fontWeight': 500},
    'Medium Italic': {'fontWeight': 500, 'fontStyle': 'italic'},
    'Bold': {'fontWeight': 700},
    'Bold Italic': {'fontWeight': 700, 'fontStyle': 'italic'},
    'Black': {'fontWeight': 900},
    'Black Italic': {'fontWeight': 900, 'fontStyle': 'italic'},
}

NEEDED_STYLE_ERROR_MESSAGE = (
    "'left', 'top', 'width', and 'height' parameters must be "
    "set equal to a number (percentage) or a number with "
    "'px' at the end of it. For example in "
    "\n\n.left=10;top=50px{{TEXT}}\n\n the top left corner of "
    "the TEXT block will be set 10 percent from the left of "
    "the presentation boarder, and 50 pixels from the top."
)


def list_of_options(iterable, conj='and', period=True):
    """
    Returns an English listing of objects seperated by commas ','

    For example, ['foo', 'bar', 'baz'] becomes 'foo, bar and baz'
    if the conjunction 'and' is selected.
    """
    if len(iterable) < 2:
        raise exceptions.PlotlyError(
            'Your list or tuple must contain at least 2 items.'
        )
    template = (len(iterable) - 2)*'{}, ' + '{} ' + conj + ' {}' + period*'.'
    return template.format(*iterable)


def _generate_id(size):
    letters_and_numbers = string.ascii_letters
    for num in range(10):
        letters_and_numbers += str(num)
    letters_and_numbers += str(num)
    id_str = ''
    for _ in range(size):
        id_str += random.choice(list(letters_and_numbers))

    return id_str

_paragraph_styles = {'Body': {'color': '#3d3d3d',
                              'fontFamily': 'Open Sans',
                              'fontSize': 11,
                              'fontStyle': 'normal',
                              'fontWeight': 400,
                              'lineHeight': 'normal',
                              'minWidth': 20,
                              'opacity': 1,
                              'textAlign': 'center',
                              'textDecoration': 'none'},
                     'Body Small': {'color': '#3d3d3d',
                                    'fontFamily': 'Open Sans',
                                    'fontSize': 10,
                                    'fontStyle': 'normal',
                                    'fontWeight': 400,
                                    'lineHeight': 'normal',
                                    'minWidth': 20,
                                    'opacity': 1,
                                    'textAlign': 'center',
                                    'textDecoration': 'none'},
                     'Caption': {'color': '#3d3d3d',
                                 'fontFamily': 'Open Sans',
                                 'fontSize': 11,
                                 'fontStyle': 'italic',
                                 'fontWeight': 400,
                                 'lineHeight': 'normal',
                                 'minWidth': 20,
                                 'opacity': 1,
                                 'textAlign': 'center',
                                 'textDecoration': 'none'},
                     'Heading 1': {'color': '#3d3d3d',
                                   'fontFamily': 'Open Sans',
                                   'fontSize': 26,
                                   'fontStyle': 'normal',
                                   'fontWeight': 400,
                                   'lineHeight': 'normal',
                                   'minWidth': 20,
                                   'opacity': 1,
                                   'textAlign': 'center',
                                   'textDecoration': 'none'},
                     'Heading 2': {'color': '#3d3d3d',
                                   'fontFamily': 'Open Sans',
                                   'fontSize': 20,
                                   'fontStyle': 'normal',
                                   'fontWeight': 400,
                                   'lineHeight': 'normal',
                                   'minWidth': 20,
                                   'opacity': 1,
                                   'textAlign': 'center',
                                   'textDecoration': 'none'},
                     'Heading 3': {'color': '#3d3d3d',
                                   'fontFamily': 'Open Sans',
                                   'fontSize': 11,
                                   'fontStyle': 'normal',
                                   'fontWeight': 700,
                                   'lineHeight': 'normal',
                                   'minWidth': 20,
                                   'opacity': 1,
                                   'textAlign': 'center',
                                   'textDecoration': 'none'}}


def _empty_slide(transition, id):
    empty_slide = {'children': [],
                   'id': id,
                   'props': {'style': {}, 'transition': transition}}
    return empty_slide


def _box(boxtype, text_or_url, left, top, height, width, id, props_attr,
         style_attr):
    children_list = []
    fontFamily = "Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace"
    if boxtype == 'Text':
        children_list = text_or_url.split('\n')
        props = {
            'isQuote': False,
            'listType': None,
            'paragraphStyle': 'Body',
            'size': 4,
            'style': {'color': '#3d3d3d',
                      'fontFamily': 'Open Sans',
                      'fontSize': 11,
                      'fontStyle': 'normal',
                      'fontWeight': 400,
                      'height': height,
                      'left': left,
                      'lineHeight': 'normal',
                      'minWidth': 20,
                      'opacity': 1,
                      'position': 'absolute',
                      'textAlign': 'center',
                      'textDecoration': 'none',
                      'top': top,
                      'width': width,
                      'wordBreak': 'break-word'}
        }
    elif boxtype == 'Image':
        props = {
            'height': 512,
            'imageName': None,
            'src': text_or_url,
            'style': {'height': height,
                      'left': left,
                      'opacity': 1,
                      'position': 'absolute',
                      'top': top,
                      'width': width},
            'width': 512
        }
    elif boxtype == 'Plotly':
        props = {
            'frameBorder': 0,
            'scrolling': 'no',
            'src': text_or_url + '.embed?link=false',
            'style': {'height': height,
                      'left': left,
                      'position': 'absolute',
                      'top': top,
                      'width': width}
        }
    elif boxtype == 'CodePane':
        props = {
            'language': 'python',
            'source': text_or_url,
            'style': {'fontFamily': fontFamily,
                      'fontSize': 13,
                      'height': height,
                      'left': left,
                      'margin': 0,
                      'position': 'absolute',
                      'textAlign': 'left',
                      'top': top,
                      'width': width},
            'theme': 'tomorrowNight'
        }

    # update props and style attributes
    for item in props_attr.items():
        props[item[0]] = item[1]
    for item in style_attr.items():
        props['style'][item[0]] = item[1]

    child = {
        'children': children_list,
        'id': id,
        'props': props,
        'type': boxtype
    }

    if boxtype == 'Text':
        child['defaultHeight'] = 36
        child['defaultWidth'] = 52
        child['resizeVertical'] = False
    if boxtype == 'CodePane':
        child['defaultText'] = 'Code'

    return child


def _percentage_to_pixel(value, side):
    if side == 'left':
        return WIDTH * (0.01 * value)
    elif side == 'top':
        return HEIGHT * (0.01 * value)
    elif side == 'height':
        return HEIGHT * (0.01 * value)
    elif side == 'width':
        return WIDTH * (0.01 * value)


def _return_box_position(left, top, height, width):
    values_dict = {
        'left': left,
        'top': top,
        'height': height,
        'width': width,
    }
    for key in values_dict.keys():
        if isinstance(values_dict[key], str):
            if values_dict[key][-2:] != 'px':
                raise exceptions.PlotlyError(
                    NEEDED_STYLE_ERROR_MESSAGE
                )
            try:
                var = float(values_dict[key][: -2])
            except ValueError:
                raise exceptions.PlotlyError(
                    NEEDED_STYLE_ERROR_MESSAGE
                )

        else:
            var = _percentage_to_pixel(values_dict[key], key)
        values_dict[key] = var

    return (values_dict['left'], values_dict['top'],
            values_dict['height'], values_dict['width'])


def _remove_extra_whitespace_from_line(line):
    while line.startswith('\n') or line.startswith(' '):
        line = line[1:]
    while line.endswith('\n') or line.endswith(' '):
        line = line[: -1]
    return line


def _list_of_slides(markdown_string):
    if not markdown_string.endswith('\n---\n'):
        markdown_string += '\n---\n'

    text_blocks = re.split(
        '\n--\n|\n---\n|\n----\n|\n-----\n|\n------\n', markdown_string
    )
    list_of_slides = []
    for j, text in enumerate(text_blocks):
        if not all(char in ['\n', '-', ' '] for char in text):
            list_of_slides.append(text)

    if '\n-\n' in markdown_string:
        msg = ("You have at least one '-' by itself on its own line in your "
               "markdown string. If you are trying to denote a new slide, "
               "make sure that the line has 3 '-'s like this: \n\n---\n\n"
               "A new slide will NOT be created here.")
        warnings.warn(msg)

    return list_of_slides


def _boxes_in_slide(slide):
    boxes = []
    slide_copy = copy.deepcopy(slide)
    prop_split = ';'
    prop_val_sep = '='

    while '.left' in slide_copy:
        prop_dict = {}
        left_idx = slide_copy.find('.left')
        l_brace_idx = slide_copy[left_idx:].find('{{') + left_idx
        properties = slide_copy[left_idx + 1: l_brace_idx].split(
            prop_split
        )

        # remove white chars from properties
        empty_props = []
        for prop in properties:
            if all(char in [' ', '\n'] for char in prop):
                empty_props.append(prop)

        for prop in empty_props:
            properties.remove(prop)

        for prop in properties:
            prop_name = prop.split(prop_val_sep)[0]
            prop_val = prop.split(prop_val_sep)[1]

            try:
                prop_val = float(prop_val)
            except ValueError:
                pass
            prop_dict[prop_name] = prop_val

        r_brace_idx = slide_copy[l_brace_idx:].find('}}') + l_brace_idx
        box = slide_copy[l_brace_idx + 2: r_brace_idx]
        box_no_breaks = _remove_extra_whitespace_from_line(box)
        boxes.append((box_no_breaks, prop_dict))

        slide_copy = slide_copy[r_brace_idx + 2:]
    return boxes


def _top_spec_for_text_at_bottom(text_block, width_per, per_from_bottom=0,
                                 min_top=30):
    # TODO: customize this function for different fonts/sizes
    max_lines = 37
    one_char_percent_width = 0.764
    chars_in_full_line = width_per / one_char_percent_width

    num_of_lines = 0
    char_group = 0
    for char in text_block:
        if char == '\n':
            num_of_lines += 1
            char_group = 0
        else:
            if char_group >= chars_in_full_line:
                char_group = 0
                num_of_lines += 1
            else:
                char_group += 1

    num_of_lines += 1
    top_frac = (max_lines - num_of_lines) / float(max_lines)
    top = top_frac * 100 - per_from_bottom

    # to be safe
    return max(top, min_top)


def _box_specs_gen(num_of_boxes, grouptype='leftgroup_v', width_range=50,
                   height_range=50, margin=2, betw_boxes=4, middle_center=50):
    # the (l, t, w, h) specs are added to 'specs_for_boxes'
    specs_for_boxes = []
    if num_of_boxes == 1 and grouptype in ['leftgroup_v', 'rightgroup_v']:
        if grouptype == 'rightgroup_v':
            left_shift = (100 - width_range)
        else:
            left_shift = 0

        box_spec = (
            left_shift + (margin / WIDTH) * 100,
            (margin / HEIGHT) * 100,
            100 - (2 * margin / HEIGHT * 100),
            width_range - (2 * margin / WIDTH) * 100
        )
        specs_for_boxes.append(box_spec)

    elif num_of_boxes > 1 and grouptype in ['leftgroup_v', 'rightgroup_v']:
        if grouptype == 'rightgroup_v':
            left_shift = (100 - width_range)
        else:
            left_shift = 0

        if num_of_boxes % 2 == 0:
            box_width_px = 0.5 * (
                (float(width_range)/100) * WIDTH - 2 * margin - betw_boxes
            )
            box_width = (box_width_px / WIDTH) * 100

            height = (200.0 / (num_of_boxes * HEIGHT)) * (
                HEIGHT - (num_of_boxes / 2 - 1) * betw_boxes - 2 * margin
            )

            left1 = left_shift + (margin / WIDTH) * 100
            left2 = left_shift + (
                ((margin + betw_boxes) / WIDTH) * 100 + box_width
            )
            for left in [left1, left2]:
                for j in range(num_of_boxes / 2):
                    top = (margin * 100 / HEIGHT) + j * (
                        height + (betw_boxes * 100 / HEIGHT)
                    )
                    specs = (
                        left,
                        top,
                        height,
                        box_width
                    )
                    specs_for_boxes.append(specs)

        if num_of_boxes % 2 == 1:
            width = width_range - (200 * margin) / WIDTH
            height = (100.0 / (num_of_boxes * HEIGHT)) * (
                HEIGHT - (num_of_boxes - 1) * betw_boxes - 2 * margin
            )
            left = left_shift + (margin / WIDTH) * 100
            for j in range(num_of_boxes):
                top = (margin / HEIGHT) * 100 + j * (
                    height + (betw_boxes / HEIGHT) * 100
                )
                specs = (
                    left,
                    top,
                    height,
                    width
                )
                specs_for_boxes.append(specs)

    elif grouptype == 'middle':
        # margin is not used
        #top = (100 - float(height_range)) / 2
        top = float(middle_center - (height_range / 2))
        height = height_range
        width = (1 / float(num_of_boxes)) * (
            width_range - (num_of_boxes - 1) * (100*betw_boxes/WIDTH)
        )
        for j in range(num_of_boxes):
            left = ((100 - float(width_range)) / 2) + j * (
                width + (betw_boxes / WIDTH) * 100
            )
            specs = (left, top, height, width)
            specs_for_boxes.append(specs)

    elif 'checkerboard' in grouptype and num_of_boxes == 2:
        if grouptype == 'checkerboard_topleft':
            for j in range(2):
                left = j * 50
                top = j * 50
                height = 50
                width = 50
                specs = (
                    left,
                    top,
                    height,
                    width
                )
                specs_for_boxes.append(specs)
        else:
            for j in range(2):
                left = 50 * (1 - j)
                top = j * 50
                height = 50
                width = 50
                specs = (
                    left,
                    top,
                    height,
                    width
                )
                specs_for_boxes.append(specs)
    return specs_for_boxes


def _return_layout_specs(num_of_boxes, url_lines, title_lines, text_block,
                         code_blocks, slide_num, style):
    # returns specs of the form (left, top, height, width)

    # default settings
    code_theme = 'tomorrowNight'
    if style == 'martik':
        title_fontFamily = 'Raleway'
        text_fontFamily = 'Roboto'
        title_fontWeight = fontWeight_dict['Bold']['fontWeight']
        text_fontWeight = fontWeight_dict['Regular']['fontWeight']
        title_fontSize = 40
        specs_for_boxes = []
        margin = 18  # in pxs

        # order is bkgd_color, title_font_color, text_font_color
        colors_dict = {
            'darkslide': ('#0D0A1E', '#F4FAFB', '#F4FAFB'),
            'lightslide': ('#F4FAFB', '#0D0A1E', '#96969C')
        }

        (bkgd_color,
         title_font_color,
         text_font_color) = colors_dict['lightslide']
        if num_of_boxes == 0 and slide_num == 0:
            text_textAlign = 'center'
        else:
            text_textAlign = 'left'
        if num_of_boxes == 0:
            specs_for_title = (0, 50, 20, 100)
            specs_for_text = (15, 60, 50, 70)
            title_fontSize = 55
            (bkgd_color,
             title_font_color,
             text_font_color) = colors_dict['darkslide']
        elif num_of_boxes == 1:
            if code_blocks != [] or (
                url_lines != [] and 'https://plot.ly' in url_lines[0]
            ):
                if code_blocks != []:
                    w_range = 40
                else:
                    w_range = 60
                text_top = _top_spec_for_text_at_bottom(
                    text_block, 80,
                    per_from_bottom=(margin / HEIGHT) * 100
                )
                specs_for_title = (0, 3, 20, 100)
                specs_for_text = (10, text_top, 30, 80)
                specs_for_boxes = _box_specs_gen(
                    num_of_boxes, grouptype='middle', width_range=w_range,
                    height_range=60, margin=margin, betw_boxes=4
                )
                (bkgd_color,
                 title_font_color,
                 text_font_color) = colors_dict['darkslide']
                code_theme = 'tomorrow'
            elif title_lines == [] and text_block == '':
                specs_for_title = (0, 50, 20, 100)
                specs_for_text = (15, 60, 50, 70)
                specs_for_boxes = _box_specs_gen(
                    num_of_boxes, grouptype='middle', width_range=50,
                    height_range=80, margin=0, betw_boxes=0
                )
            else:
                title_text_width = 40 - (margin / WIDTH) * 100

                text_top = _top_spec_for_text_at_bottom(
                    text_block, title_text_width,
                    per_from_bottom=(margin / HEIGHT) * 100
                )
                specs_for_title = (60, 3, 20, 40)
                specs_for_text = (60, text_top, 1, title_text_width)
                specs_for_boxes = _box_specs_gen(
                    num_of_boxes, grouptype='leftgroup_v', width_range=60,
                    margin=margin, betw_boxes=4
                )
                (bkgd_color,
                 title_font_color,
                 text_font_color) = colors_dict['darkslide']
        elif num_of_boxes == 2 and url_lines != []:
            text_top = _top_spec_for_text_at_bottom(
                text_block, 46, per_from_bottom=(margin / HEIGHT) * 100,
                min_top=50
            )
            specs_for_title = (0, 3, 20, 50)
            specs_for_text = (52, text_top, 40, 46)
            specs_for_boxes = _box_specs_gen(
                num_of_boxes, grouptype='checkerboard_topright'
            )
            (bkgd_color,
             title_font_color,
             text_font_color) = colors_dict['lightslide']
        elif num_of_boxes >= 2 and url_lines == []:
            text_top = _top_spec_for_text_at_bottom(
                text_block, 92, per_from_bottom=(margin / HEIGHT) * 100,
                min_top=15
            )
            if num_of_boxes == 2:
                betw_boxes = 90
            else:
                betw_boxes = 10
            specs_for_title = (0, 3, 20, 100)
            specs_for_text = (4, text_top, 1, 92)
            specs_for_boxes = _box_specs_gen(
                num_of_boxes, grouptype='middle', width_range=92,
                height_range=60, margin=margin, betw_boxes=betw_boxes
            )
            (bkgd_color,
             title_font_color,
             text_font_color) = colors_dict['lightslide']
            code_theme = 'tomorrow'
        else:
            text_top = _top_spec_for_text_at_bottom(
                text_block, 40 - (margin / WIDTH) * 100,
                per_from_bottom=(margin / HEIGHT) * 100
            )
            specs_for_title = (0, 3, 20, 40 - (margin / WIDTH) * 100)
            specs_for_text = (
                (margin / WIDTH) * 100, text_top, 50,
                40 - (margin / WIDTH) * 100
            )
            specs_for_boxes = _box_specs_gen(
                num_of_boxes, grouptype='rightgroup_v', width_range=60,
                margin=margin, betw_boxes=4
            )
            (bkgd_color,
             title_font_color,
             text_font_color) = colors_dict['lightslide']

    elif style == 'moods':
        specs_for_boxes = []
        margin = 18
        code_theme = 'tomorrowNight'
        title_fontFamily = 'Roboto'
        text_fontFamily = 'Roboto'
        title_fontWeight = fontWeight_dict['Black']['fontWeight']
        text_fontWeight = fontWeight_dict['Thin']['fontWeight']
        title_fontSize = 42
        # order is bkgd_color, title_font_color, text_font_color
        colors_dict = {
            'darkslide': ('#F7F7F7', '#000016', '#000016'),
            'lightslide': ('#FFFFFF', '#000016', '#000016')
        }

        # besides first page
        (bkgd_color,
         title_font_color,
         text_font_color) = colors_dict['lightslide']
        if num_of_boxes == 0 and slide_num == 0:
            text_textAlign = 'center'
        else:
            text_textAlign = 'left'
        if num_of_boxes == 0:
            title_fontSize = 55
            if slide_num == 0 or text_block == '':
                (bkgd_color,
                 title_font_color,
                 text_font_color) = colors_dict['darkslide']
                specs_for_title = (0, 50, 20, 100)
                specs_for_text = (15, 60, 50, 70)
            else:
                (bkgd_color,
                 title_font_color,
                 text_font_color) = colors_dict['darkslide']
                text_top = _top_spec_for_text_at_bottom(
                    text_block, width_per=90,
                    per_from_bottom=(margin / HEIGHT) * 100,
                    min_top=20
                )
                specs_for_title = (0, 2, 20, 100)
                specs_for_text = (5, text_top, 50, 90)

        elif num_of_boxes == 1:
            if code_blocks != []:
                # code
                if text_block == '':
                    margin = 5
                    specs_for_title = (0, 3, 20, 100)
                    specs_for_text = (0, 0, 0, 0)
                    top = 12
                    specs_for_boxes = [
                        (margin, top, 100 - top - margin, 100 - 2 * margin)
                    ]

                elif slide_num % 2 == 0:
                    # middle center
                    width_per = 90
                    height_range = 60
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=100 - height_range / 2.
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='middle',
                        width_range=50, height_range=60, margin=margin,
                    )
                    specs_for_title = (0, 3, 20, 100)
                    specs_for_text = (
                        5, text_top, 2, width_per
                    )
                else:
                    # right
                    width_per = 50
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=30
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='rightgroup_v',
                        width_range=50, margin=40,
                    )
                    specs_for_title = (0, 3, 20, 50)
                    specs_for_text = (
                        2, text_top, 2, width_per - 2
                    )
            elif url_lines != [] and 'https://plot.ly' in url_lines[0]:
                # url
                if slide_num % 2 == 0:
                    # top half
                    width_per = 95
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=60
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='middle',
                        width_range=100, height_range=60,
                        middle_center=30
                    )
                    specs_for_title = (0, 60, 20, 100)
                    specs_for_text = (
                        2.5, text_top, 2, width_per
                    )
                else:
                    # middle across
                    width_per = 95
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=60
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='middle',
                        width_range=100, height_range=60
                    )
                    specs_for_title = (0, 3, 20, 100)
                    specs_for_text = (
                        2.5, text_top, 2, width_per
                    )
            else:
                # image
                if slide_num % 2 == 0:
                    # right
                    width_per = 50
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=30
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='rightgroup_v',
                        width_range=50, margin=0,
                    )
                    specs_for_title = (0, 3, 20, 50)
                    specs_for_text = (
                        2, text_top, 2, width_per - 2
                    )
                else:
                    # left
                    width_per = 50
                    text_top = _top_spec_for_text_at_bottom(
                        text_block, width_per=width_per,
                        per_from_bottom=(margin / HEIGHT) * 100,
                        min_top=30
                    )
                    specs_for_boxes = _box_specs_gen(
                        num_of_boxes, grouptype='leftgroup_v',
                        width_range=50, margin=0,
                    )
                    specs_for_title = (50, 3, 20, 50)
                    specs_for_text = (
                        52, text_top, 2, width_per - 2
                    )
        elif num_of_boxes == 2:
            # right stack
            width_per = 50
            text_top = _top_spec_for_text_at_bottom(
                text_block, width_per=width_per,
                per_from_bottom=(margin / HEIGHT) * 100,
                min_top=30
            )
            specs_for_boxes = [(50, 0, 50, 50), (50, 50, 50, 50)]
            specs_for_title = (0, 3, 20, 50)
            specs_for_text = (
                2, text_top, 2, width_per - 2
            )
        elif num_of_boxes == 3:
            # middle top
            width_per = 95
            text_top = _top_spec_for_text_at_bottom(
                text_block, width_per=width_per,
                per_from_bottom=(margin / HEIGHT) * 100,
                min_top=40
            )
            specs_for_boxes = _box_specs_gen(
                num_of_boxes, grouptype='middle',
                width_range=100, height_range=40, middle_center=30
            )
            specs_for_title = (0, 3, 20, 100)
            specs_for_text = (
                2.5, text_top, 2, width_per
            )
        else:
            # right stack
            width_per = 40
            text_top = _top_spec_for_text_at_bottom(
                text_block, width_per=width_per,
                per_from_bottom=(margin / HEIGHT) * 100,
                min_top=30
            )
            specs_for_boxes = _box_specs_gen(
                num_of_boxes, grouptype='rightgroup_v',
                width_range=60, margin=0,
            )
            specs_for_title = (0, 3, 20, 40)
            specs_for_text = (
                2, text_top, 2, width_per - 2
            )


    # set title and text style attributes
    title_style_attr = {
        'color': title_font_color,
        'fontFamily': title_fontFamily,
        'fontWeight': title_fontWeight,
        'textAlign': 'center',
        'fontSize': title_fontSize,
    }

    text_style_attr = {
        'color': text_font_color,
        'fontFamily': text_fontFamily,
        'fontWeight': text_fontWeight,
        'textAlign': text_textAlign,
        'fontSize': 16,
    }
    return (specs_for_boxes, specs_for_title, specs_for_text, bkgd_color,
            title_style_attr, text_style_attr, code_theme)


class Presentation(dict):
    def __init__(self, markdown_string=None, style='moods'):
        self['presentation'] = {
            'slides': [],
            'slidePreviews': [None for _ in range(496)],
            'version': '0.1.3',
            'paragraphStyles': _paragraph_styles
        }

        if markdown_string:
            if style not in PRES_THEMES:
                raise exceptions.PlotlyError(
                    "Your presentation style must be {}".format(
                        list_of_options(PRES_THEMES, conj='or', period=True)
                    )
                )
            self._markdown_to_presentation(markdown_string, style)
        else:
            self._add_empty_slide()

    def _markdown_to_presentation(self, markdown_string, style):
        list_of_slides = _list_of_slides(markdown_string)

        for slide_num, slide in enumerate(list_of_slides):
            lines_in_slide = slide.split('\n')
            title_lines = []

            # validate blocks of code
            if slide.count('```') % 2 != 0:
                raise exceptions.PlotlyError(
                    "If you are putting a block of code into your markdown "
                    "presentation, make sure your denote the start and end "
                    "of the code environment with the '```' characters. For "
                    "example, your markdown string would include something "
                    "like:\n\n```python\nx = 2\ny = 1\nprint x\n```\n\n"
                    "Notice how the language that you want the code to be "
                    "displayed in is immediately to the right of first "
                    "entering '```', i.e. '```python'."
                )

            # find code blocks
            code_indices = []
            code_blocks = []
            wdw_size = len('```')
            for j in range(len(slide)):
                if slide[j:j+wdw_size] == '```':
                    code_indices.append(j)

            for k in range(len(code_indices) / 2):
                l = 2 * k
                code_blocks.append(
                    slide[code_indices[l]:code_indices[l + 1]]
                )

            lang_and_code_tuples = []
            for code_block in code_blocks:
                # validate code blocks
                code_by_lines = code_block.split('\n')
                language = _remove_extra_whitespace_from_line(
                    code_by_lines[0][3:]
                ).lower()
                if language == '' or language not in VALID_LANGUAGES:
                    raise exceptions.PlotlyError(
                        "The language of your code block should be "
                        "clearly indicated after the first ``` that "
                        "begins the code block. The valid languages to "
                        "choose from are" + list_of_options(
                            VALID_LANGUAGES
                        )
                    )
                lang_and_code_tuples.append(
                    (language, string.join(code_by_lines[1:], '\n'))
                )

            # collect text, code and urls
            title_lines = []
            url_lines = []
            text_lines = []
            inCode = False
            slidestyle = None

            for index, line in enumerate(lines_in_slide):
                # inCode handling
                if line[:3] == '```' and len(line) > 3:
                    inCode = True
                if line == '```':
                    inCode = False

                if not inCode and line != '```':
                    if len(line) > 0 and line[0] == '#':
                        title_lines.append(line)
                    elif line.startswith('url('):
                        url_lines.append(line)
                    else:
                        # find and set transition properties
                        trans = 'transition:'
                        if line.startswith(trans) and title_lines == []:
                            slide_trans = line[len(trans):]
                            slide_trans = _remove_extra_whitespace_from_line(
                                slide_trans
                            )
                            slide_transition_list = []
                            for key in VALID_TRANSITIONS:
                                if key in slide_trans:
                                    slide_transition_list.append(key)

                            if slide_transition_list == []:
                                slide_transition_list.append('slide')
                            self._set_transition(
                                slide_transition_list, slide_num
                            )

                        else:
                            text_lines.append(line)

            # clean titles
            for title_index, title in enumerate(title_lines):
                while '#' in title:
                    title = title[1:]
                title = _remove_extra_whitespace_from_line(title)
                title_lines[title_index] = title

            # make text block
            for i in range(2):
                try:
                    while text_lines[-i] == '':
                        text_lines.pop(-i)
                except IndexError:
                    pass

            text_block = string.join(text_lines, '\n')
            num_of_boxes = len(url_lines) + len(lang_and_code_tuples)

            (specs_for_boxes, specs_for_title, specs_for_text, bkgd_color,
             title_style_attr, text_style_attr,
             code_theme) = _return_layout_specs(
                num_of_boxes, url_lines, title_lines, text_block, code_blocks,
                slide_num, style
            )

            # background color
            self._color_background(bkgd_color, slide_num)

            # insert title, text, code, and images
            if len(title_lines) > 0:
                self._insert(
                    box='Text', text_or_url=title_lines[0],
                    left=specs_for_title[0], top=specs_for_title[1],
                    height=specs_for_title[2], width=specs_for_title[3],
                    slide=slide_num, style_attr=title_style_attr
                )

            # text
            if len(text_lines) > 0:
                self._insert(
                    box='Text', text_or_url=text_block,
                    left=specs_for_text[0], top=specs_for_text[1],
                    height=specs_for_text[2], width=specs_for_text[3],
                    slide=slide_num, style_attr=text_style_attr
                )

            url_and_code_blocks = list(url_lines + lang_and_code_tuples)
            for k, specs in enumerate(specs_for_boxes):
                url_or_code = url_and_code_blocks[k]
                if isinstance(url_or_code, tuple):
                    # code
                    language = url_or_code[0]
                    code = url_or_code[1]
                    box_name = 'CodePane'

                    # code style
                    props_attr = {}
                    props_attr['language'] = language
                    props_attr['theme'] = code_theme

                    self._insert(box=box_name, text_or_url=code,
                                 left=specs[0], top=specs[1],
                                 height=specs[2], width=specs[3],
                                 slide=slide_num, props_attr=props_attr)
                else:
                    # url
                    url = url_or_code[4: -1]
                    if 'https://plot.ly' in url:
                        box_name = 'Plotly'
                    else:
                        box_name = 'Image'

                    self._insert(box=box_name, text_or_url=url,
                                 left=specs[0], top=specs[1],
                                 height=specs[2], width=specs[3],
                                 slide=slide_num)

    def _add_empty_slide(self):
        self['presentation']['slides'].append(
            _empty_slide(['slide'], _generate_id(9))
        )

    def _add_missing_slides(self, slide):
        # add slides if desired slide number isn't in the presentation
        try:
            self['presentation']['slides'][slide]['children']
        except IndexError:
            num_of_slides = len(self['presentation']['slides'])
            for _ in range(slide - num_of_slides + 1):
                self._add_empty_slide()

    def _insert(self, box, text_or_url, left, top, height, width, slide=0,
                props_attr={}, style_attr={}):
        self._add_missing_slides(slide)

        left, top, height, width = _return_box_position(left, top, height,
                                                        width)
        new_id = _generate_id(9)
        child = _box(box, text_or_url, left, top, height, width, new_id,
                     props_attr, style_attr)

        self['presentation']['slides'][slide]['children'].append(child)

    def _color_background(self, color, slide):
        self._add_missing_slides(slide)

        loc = self['presentation']['slides'][slide]
        loc['props']['style']['backgroundColor'] = color

    def _background_image(self, url, slide, bkrd_image_dict):
        self._add_missing_slides(slide)

        loc = self['presentation']['slides'][slide]['props']

        # default settings
        size = 'stretch'
        repeat = 'no-repeat'

        if 'background-size:' in bkrd_image_dict:
            size = bkrd_image_dict['background-size:']
        if 'background-repeat:' in bkrd_image_dict:
            repeat = bkrd_image_dict['background-repeat:']

        if size == 'stretch':
            backgroundSize = '100% 100%'
        elif size == 'original':
            backgroundSize = 'auto'
        elif size == 'contain':
            backgroundSize = 'contain'
        elif size == 'cover':
            backgroundSize = 'cover'

        style = {
            'backgroundImage': 'url({})'.format(url),
            'backgroundPosition': 'center center',
            'backgroundRepeat': repeat,
            'backgroundSize': backgroundSize
        }

        for item in style.items():
            loc['style'].setdefault(item[0], item[1])

        loc['backgroundImageSrc'] = url
        loc['backgroundImageName'] = None

    def _set_transition(self, transition, slide):
        self._add_missing_slides(slide)
        loc = self['presentation']['slides'][slide]['props']
        loc['transition'] = transition