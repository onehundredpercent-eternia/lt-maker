from typing import Dict

from dataclasses import dataclass, field

from PyQt5.QtGui import QPixmap

from app.typing.utilities import Pos
from app.map_maker.qt_renderers.renderer_utils import get_pixmap16

@dataclass
class QtPalette:
    fn: str
    autotiles: Dict[Pos, int] = field(default_factory=dict)
    pixmap: QPixmap = None

    def has_autotiles(self) -> bool:
        return self.autotiles

    def get_pixmap16(self, coord: Pos, autotile_num: int) -> QPixmap:
        if not self.pixmap:
            self.pixmap = QPixmap(self.fn)
        if self.has_autotiles() and coord in self.autotiles:
            column = self.autotiles[coord]
            return get_pixmap16(self.pixmap, (column, autotile_num))
        else:
            return get_pixmap16(self.pixmap, coord)
