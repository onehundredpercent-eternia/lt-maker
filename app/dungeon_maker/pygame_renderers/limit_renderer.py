from typing import Dict
from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.pygame_renderers.renderer_utils import find_limit, get_image16
from app.engine import engine

class LimitRenderer:
    def __init__(self, painter: Painter, image_fn: str):
        self.painter = painter
        self.image = engine.image_load(image_fn)
        limits: Dict[int, int] = {k: find_limit(self.image, k) for k in range(16)}
        self.painter.set_limit(limits)

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos) -> engine.Surface:
        coord = self.painter.get_coord(dungeon_tilemap, position)
        return get_image16(self.image, coord)
