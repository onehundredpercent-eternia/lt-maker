from ast import Tuple
from dataclasses import dataclass, field
from typing import Dict, List
from app.data.resources.resources import RESOURCES
from app.engine import bmpfont, image_mods
from app.utilities.typing import NID

class FontPalette(list):
    def __init__(self, *args):
        self += args

    def primary(self):
        if len(self) > 0:
            return self[0]
        return None

    def outline(self):
        if len(self) > 1:
            return self[1]
        return None

@dataclass
class FontType():
    name: str
    default_color: str
    is_outline_font: bool
    fallback_font: str = "app/engine/fireflysung.ttf"
    colors: Dict[str, FontPalette] = field(default_factory=dict) # str -> list of rgba

NORMAL_FONT_COLORS = ['white', 'blue', 'green', 'red', 'orange', 'grey', 'yellow', 'brown', 'purple']

text = FontType('text', 'white', True)
text.colors['white'] = FontPalette((248, 248, 248, 255), (56, 48, 40, 255), (160, 136, 216, 255))
text.colors['blue'] = FontPalette((192, 248, 248, 255), (24, 24, 88, 255), (80, 112, 248, 255))
text.colors['green'] = FontPalette((72, 232, 32, 255), (24, 88, 24, 255), (112, 160, 72, 255))
text.colors['red'] = FontPalette((224, 96, 80, 255), (88, 24, 24, 255), (160, 88, 72, 255))
text.colors['orange'] = FontPalette((248, 168, 88, 255), (138, 64, 0, 255), (160, 100, 85, 255))
text.colors['grey'] = FontPalette((184, 176, 176, 255), (56, 48, 40, 255), (136, 128, 120, 255))
text.colors['yellow'] = FontPalette((248, 240, 136, 255), (72, 64, 8, 255), (168, 168, 72, 255))
text.colors['brown'] = FontPalette((248, 248, 248, 255), (80, 40, 0, 255), (144, 112, 88, 255))
text.colors['purple'] = FontPalette((199, 155, 232, 255), (62, 37, 82, 255), (147, 61, 212, 255))
#growth colors stat < 20 to stat < 100
text.colors['red-orange'] = FontPalette((248, 64, 64), (80, 24, 32), (152, 72, 96))
text.colors['light-red'] = FontPalette((248, 88, 96), (80, 24, 32), (152, 72, 96))
text.colors['pink-orange'] = FontPalette((248, 128, 96), (80, 24, 32), (152, 72, 96))
text.colors['light-orange'] = FontPalette((248, 168, 88), (80, 24, 32), (152, 72, 96))
text.colors['corn-yellow'] = FontPalette((232, 248, 112), (64, 56, 24), (80, 152, 72))
text.colors['light-green'] = FontPalette((200, 232, 136), (24, 88, 24), (80, 152, 72))
text.colors['olive-green'] = FontPalette((168, 208, 96), (24, 88, 24), (80, 152, 72))
text.colors['soft-green'] = FontPalette((128, 192, 104), (24, 88, 24), (80, 152, 72))
text.colors['yellow-green'] = FontPalette((57, 206, 16), (24, 88, 24), (80, 152, 72))

narrow = FontType('narrow', 'white', True)
narrow.colors = text.colors


small = FontType('small', 'white', True)
small.colors = text.colors

info = FontType('info', 'black', False)
info.colors['black'] = FontPalette((56, 48, 40, 255), (160, 136, 216, 255))
info.colors['grey'] = FontPalette((56, 48, 40, 255), (184, 176, 176, 255))
info.colors['white'] = FontPalette((248, 248, 248, 255), (184, 176, 176, 255))

convo = FontType('convo', 'black', False)
convo.colors['black'] = FontPalette((40, 40, 40, 255), (184, 184, 184, 255))
convo.colors['brown'] = FontPalette((86, 69, 43, 255), (216, 190, 127, 255))
convo.colors['red'] = FontPalette((160, 0, 0, 255), (248, 200, 168, 255))
convo.colors['white'] = FontPalette((248, 248, 248, 255), (136, 144, 144, 255))
convo.colors['orange'] = FontPalette((255, 128, 0, 255), (255, 204, 153, 255))
convo.colors['yellow'] = FontPalette((248, 240, 136, 255), (168, 168, 72, 255))
convo.colors['green'] = FontPalette((112, 160, 72, 255), (197, 223, 176, 255))
convo.colors['blue'] = FontPalette((80, 112, 248, 255), (204, 229, 255, 255))
convo.colors['indigo'] = FontPalette((75, 0, 130, 255), (204, 204, 255, 255))
convo.colors['violet'] = FontPalette((127, 0, 255, 255), (229, 204, 255, 255))
convo.colors['pink'] = FontPalette((255, 102, 178, 255), (255, 204, 229, 255))

nconvo = FontType('nconvo', 'black', False)
nconvo.colors = convo.colors

iconvo = FontType('iconvo', 'black')
iconvo.colors = convo.colors

bconvo = FontType('bconvo', 'black')
bconvo.colors = convo.colors

chapter = FontType('chapter', 'yellow', True)
chapter.colors['yellow'] = FontPalette((248, 248, 248, 255), (232, 240, 96, 255), (168, 176, 128, 255),
                            (144, 152, 112, 255), (128, 128, 96, 255), (96, 104, 56, 255),
                            (80, 80, 64, 255))
chapter.colors['grey'] = FontPalette((248, 248, 248, 255), (232, 232, 232, 255), (200, 200, 200, 255),
                          (200, 200, 200, 255), (152, 152, 152, 255), (112, 112, 112, 255),
                          (56, 56, 56, 255))
chapter.colors['black'] = FontPalette((96, 96, 96, 255), (88, 88, 88, 255), (80, 80, 80, 255),
                           (80, 80, 80, 255), (64, 64, 64, 255), (40, 40, 40, 255),
                           (24, 24, 24, 255))
chapter.colors['white'] = FontPalette((248, 248, 248, 255), (204, 196, 136, 255), (168, 168, 144, 255),
                           (144, 144, 128, 255), (128, 120, 112, 255), (104, 96, 72, 255),
                           (80, 80, 80, 255))
chapter.colors['green'] = FontPalette((232, 232, 232, 255), (144, 224, 160, 255), (128, 208, 144, 255),
                           (104, 184, 120, 255), (112, 160, 104, 255), (56, 112, 64, 255),
                           (16, 8, 8, 255))

stat = FontType('stat', 'white', True)
stat.colors['white'] = FontPalette((248, 248, 200, 255), (248, 112, 40, 255), (152, 32, 0, 255), (80, 56, 32, 255))
stat.colors['purple'] = FontPalette((184, 184, 248, 255), (104, 156, 184, 255), (0, 120, 152, 255), (80, 56, 32, 255))

klass = FontType('class', 'purple', True)
klass.colors['purple'] = FontPalette((248, 248, 248, 255), (64, 56, 152, 255), (208, 208, 232, 255), (136, 128, 184, 255), (32, 24, 72, 255))

credit = FontType('credit', 'white', True)
credit.colors['white'] = FontPalette((240, 240, 240, 255), (104, 104, 104, 255))

credit_title = FontType('credit_title', 'white', True)
credit_title.colors['white'] = FontPalette((176, 176, 176, 255), (64, 64, 64, 255))

label = FontType('label', 'white', True)
label.colors['white'] = FontPalette((240, 240, 248, 255), (80, 56, 32, 255), (232, 216, 200, 255), (192, 176, 160), (136, 112, 96))

number = FontType('number', 'big2', True)
number.colors['big2'] = FontPalette((248, 248, 144, 255), (0, 0, 0, 255))

reel = FontType('reel', 'white', True)
reel.colors['white'] = FontPalette((232, 232, 232, 255), (48, 64, 136, 255))

font_types = [text, narrow, small, info, nconvo, convo, chapter, stat, klass, credit, credit_title, label, number, reel]

FONT: Dict[NID, bmpfont.BmpFont] = {}
def init_fonts():
    global FONT
    # Load in default, uncolored fonts
    for font in RESOURCES.fonts.values():
        title = font.nid.split('-')[0]
        idx_path = font.full_path.replace(font.nid, title).replace('.png', '.idx')
        font_type = [ftype for ftype in font_types if ftype.name == title][0]
        FONT[font.nid] = bmpfont.BmpFont(font_type, font.full_path, idx_path, font_type.default_color)
        # new, general font objects
        FONT[title] = bmpfont.BmpFont(font_type, font.full_path, idx_path, font_type.default_color)

    # Convert colors
    for font_type in font_types:
        for color, value in font_type.colors.items():
            if color == font_type.default_color:
                continue
            text = FONT[font_type.name]
            new_text = font_type.name + '-' + color
            FONT[new_text] = bmpfont.BmpFont(font_type, text.png_path, text.idx_path, color)
            dic = {a: b for a, b in zip(font_type.colors[font_type.default_color], font_type.colors[color])}
            color_surf = image_mods.color_convert_alpha(FONT[new_text].surfaces[color], dic)
            FONT[new_text].surfaces[color] = color_surf

            # new: add colors to new, generalized font objects
            # the above code is left intact for legacy purposes
            title = font_type.name
            FONT[title].surfaces[color] = color_surf
