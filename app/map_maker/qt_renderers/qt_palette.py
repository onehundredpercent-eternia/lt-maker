from typing import Dict

from dataclasses import dataclass, field

from PyQt5.QtGui import QPixmap, QPainter

from app.utilities.typing import Pos

from app.map_maker.qt_renderers.renderer_utils import get_pixmap8, get_pixmap16

@dataclass
class QtPalette:
    fn: str
    autotile_fn: str = None
    autotiles: Dict[Pos, int] = field(default_factory=dict)
    pixmap: QPixmap = None

    def has_autotiles(self) -> bool:
        return self.autotiles

    def get_full_pixmap(self) -> QPixmap:
        if not self.pixmap:
            self.pixmap = QPixmap(self.fn)
        return self.pixmap

    def get_pixmap16(self, coord: Pos, autotile_num: int) -> QPixmap:
        if not self.pixmap:
            self.pixmap = QPixmap(self.fn)
        if self.has_autotiles() and coord in self.autotiles:
            column = self.autotiles[coord]
            return get_pixmap16(self.pixmap, (column, autotile_num))
        else:
            return get_pixmap16(self.pixmap, coord)

    def subsurface8(self, coord: Pos, autotile_num: int) -> QPixmap:
        if not self.pixmap:
            self.pixmap = QPixmap(self.fn)
        if self.has_autotiles() and coord in self.autotiles:
            column = self.autotiles[coord]
            return get_pixmap8(self.pixmap, (column, autotile_num))
        else:
            return get_pixmap8(self.pixmap, coord)

    def get_pixmap8(self, coord1: Pos, coord2: Pos, coord3: Pos, coord4: Pos, autotile_num: int) -> QPixmap:
        if not self.pixmap:
            self.pixmap = QPixmap(self.fn)
        base_pixmap = QPixmap(16, 16)
        topleft = self.subsurface8(coord1, autotile_num)
        topright = self.subsurface8(coord2, autotile_num)
        bottomright = self.subsurface8(coord3, autotile_num)
        bottomleft = self.subsurface8(coord4, autotile_num)
        painter = QPainter()
        painter.begin(base_pixmap)
        painter.drawPixmap(0, 0, topleft)
        painter.drawPixmap(8, 0, topright)
        painter.drawPixmap(0, 8, bottomleft)
        painter.drawPixmap(8, 8, bottomright)
        painter.end()
        return base_pixmap
