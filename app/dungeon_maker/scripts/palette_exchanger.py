# palette exchanger
from typing import Dict
import glob
from PyQt5.QtGui import QImage, qRgb, QColor

from app.editor.tile_editor.autotiles import PaletteData, similar, similar_fast

from app.constants import TILEWIDTH, TILEHEIGHT

def load_palettes(fn) -> list:
    palettes = []
    image = QImage(fn)
    num_tiles_x = image.width() // TILEWIDTH
    num_tiles_y = image.height() // TILEHEIGHT
    for x in range(num_tiles_x):
        for y in range(num_tiles_y):
            rect = (x * TILEWIDTH, y * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
            palette = image.copy(*rect)
            d = PaletteData(palette)
            palettes.append(d)
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

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # test_palette = 'app/map_maker/test_palette.png'
    # main_palette = 'app/map_maker/palettes/westmarch/main.png'
    # change_images = 'app/map_maker/palettes/witchfen/grass.png'
    test_palette = "app/dungeon_maker/palettes/rainlash_ruins_wintersun.png"
    main_palette = "app/dungeon_maker/palettes/6C00A36E.png"
    change_images = 'app/dungeon_maker/palettes/wintersun/*.png'

    print("Colors will be converted from main_palette colors to test_palette colors")
    change_images = glob.glob(change_images)
    print("Loading palette to use as base...")
    main_palettes = load_palettes(main_palette)
    print("Loading palette to convert colors to...")
    test_palettes = load_palettes(test_palette)

    # palette_exchange = {}
    # for m_palette in main_palettes:
    #     for t_palette in test_palettes:
    #         if similar(m_palette.palette, t_palette.palette) == 0:
    #             conv = get_color_exchange(m_palette, t_palette)
    #             palette_exchange.update(conv)

    # Simple palette_exchange
    palette_exchange = {}
    for main_palette, test_palette in zip(main_palettes, test_palettes):
        conv = get_color_exchange(main_palette, test_palette)
        palette_exchange.update(conv)

    color_exchange = [(QColor.fromRgba(a), QColor.fromRgba(b)) 
                      for a, b in palette_exchange.items()]
    for a, b in color_exchange:
        print(a.red(), a.green(), a.blue(), " -> ", b.red(), b.green(), b.blue())

    for im_path in change_images[:]:
        im = QImage(im_path)
        new_im = im.copy()
        for x in range(im.width()):
            for y in range(im.height()):
                color = im.pixel(x, y)
                new_color = palette_exchange.get(color, color)
                new_im.setPixel(x, y, new_color)
        new_im.save(im_path)

    print("Done!")
