from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.typing import Pos

from app.engine import engine

def get_image16(base_image: engine.Surface, coord: Pos) -> engine.Surface:
    im = engine.subsurface(base_image, (
        coord[0] * TILEWIDTH,
        coord[1] * TILEHEIGHT,
        TILEWIDTH, TILEHEIGHT))
    return im.copy()

def find_limit(image: engine.Surface, idx: int) -> int:
    bg_color = (0, 0, 0)
    x = idx * TILEWIDTH
    for y in range(0, image.get_height(), TILEHEIGHT):
        current_color = image.get_at((x, y))
        # If we've reached the bottom of the column in our image
        if current_color[:3] == bg_color[:3]:
            return y // TILEHEIGHT
    return image.get_height() // TILEHEIGHT
