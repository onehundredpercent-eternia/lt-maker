from typing import Tuple

from app.utilities.typing import Pos

from PyQt5.QtGui import QPixmap

def _get_pixmap(pixmap: QPixmap, coord: Pos, tile_size: Tuple[int, int]) -> QPixmap:
    width, height = tile_size
    pix = pixmap.copy(
        coord[0] * width,
        coord[1] * height,
        width, height)
    return pix

def get_pixmap16(self, pixmap: QPixmap, coord: Pos) -> QPixmap:
    return _get_pixmap(pixmap, coord, (16, 16))
