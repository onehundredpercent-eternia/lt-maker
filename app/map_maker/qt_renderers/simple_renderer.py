from app.utilities.typing import Pos

from PyQt5.QtGui import QPixmap

from app.map_maker.painter_utils import Painter
from app.map_maker.qt_renderers.qt_palette import QtPalette
from app.map_maker.qt_renderers.renderer_utils import find_limit16

class SimpleRenderer:
    def __init__(self, painter: Painter, palette: QtPalette):
        self.painter = painter
        self.palette = palette
        limit = find_limit16(palette, 0)
        self.painter.set_limit({0: limit})

    def set_palette(self, palette: QtPalette):
        self.palette = palette

    def determine_sprite(self, tilemap, position: Pos, autotile_num: int) -> QPixmap:
        coord = self.painter.get_coord(tilemap, position)
        return self.palette.get_pixmap(coord, autotile_num)
