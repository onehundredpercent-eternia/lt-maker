from typing import Dict

import glob
from PyQt5.QtGui import QImage, qRgb

from app.editor.tile_editor.autotiles import PaletteData, check_hashes

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.typing import Pos

def load_palettes(fn: str) -> Dict[Pos, PaletteData]:
    palettes = {}
    image = QImage(fn)
    num_tiles_x = image.width() // TILEWIDTH
    num_tiles_y = image.height() // TILEHEIGHT
    for x in range(num_tiles_x):
        for y in range(num_tiles_y):
            rect = (x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
            palette = image.copy(*rect)
            d = PaletteData(palette)
            palettes[(x, y)] = d
    return palettes

def get_color_exchange(a: PaletteData, b: PaletteData) -> Dict[qRgb, qRgb]:
    exchange = {}
    width, height = a.im.width(), a.im.height()
    for x in range(width):
        for y in range(height):
            color_a = a.im.pixel(x, y)
            color_b = b.im.pixel(x, y)
            exchange[color_a] = color_b
    return exchange

# python -m app.map_maker.scripts.palette_generation.simple_palette_exchanger
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    color_change_these_images = 'app/map_maker/palettes/witchfen/hill.png'
    original_palette = 'app/map_maker/palettes/journey/main.png'
    new_palette = 'app/map_maker/palettes/witchfen/main.png'

    change_images = glob.glob(color_change_these_images)
    print("Loading original palette...")
    original_palettes = load_palettes(original_palette)
    print("Loading new palette...")
    new_palettes = load_palettes(new_palette)

    palette_exchange: Dict[qRgb, qRgb] = {}
    for ocoord, orig in original_palettes.items():
        for ncoord, new in new_palettes.items():
            if check_hashes(orig, new):
                conv = get_color_exchange(orig, new)
                palette_exchange.update(conv)

    for im_path in change_images[:]:
        print(im_path)
        im = QImage(im_path)
        new_im = im.copy()
        for x in range(im.width()):
            for y in range(im.height()):
                color = im.pixel(x, y)
                new_color = palette_exchange.get(color, color)
                new_im.setPixel(x, y, new_color)
        new_im.save(im_path)

    print("Done!")
