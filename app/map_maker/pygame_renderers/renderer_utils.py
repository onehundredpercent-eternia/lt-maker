from typing import Tuple

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.typing import Pos

from app.engine import engine

def _get_image(base_image: engine.Surface, coord: Pos, tile_size: Tuple[int, int]) -> engine.Surface:
    width, height = tile_size
    im = engine.subsurface(base_image, (
        coord[0] * width,
        coord[1] * height,
        width, height))
    return im.copy()

def get_image8(base_image: engine.Surface, coord: Pos) -> engine.Surface:
    return _get_image(base_image, coord, (TILEWIDTH // 2, TILEHEIGHT // 2))

def get_image16(base_image: engine.Surface, coord: Pos) -> engine.Surface:
    return _get_image(base_image, coord, (TILEWIDTH, TILEHEIGHT))

def _find_limit(image: engine.Surface, idx: int, skip: Tuple[int, int]) -> int:
    bg_color = (0, 0, 0)
    x = idx * skip[0]
    for y in range(0, image.get_height(), skip[1]):
        current_color = image.get_at((x, y))
        # If we've reached the bottom of the column in our image
        if current_color[:3] == bg_color[:3]:
            return y // skip[1]
    return image.get_height() // skip[1]

def find_limit8(image: engine.Surface, idx: int) -> int:
    return _find_limit(image, idx, (TILEWIDTH // 2, TILEHEIGHT // 2))

def find_limit16(image: engine.Surface, idx: int) -> int:
    return _find_limit(image, idx, (TILEWIDTH, TILEHEIGHT))
