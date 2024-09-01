from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.pygame_renderers.renderer_utils import find_limit16, get_image16
from app.engine import engine

class SimpleRenderer:
    def __init__(self, painter: Painter, image_fn: str):
        self.painter = painter
        self.image = engine.image_load(image_fn)
        limit = find_limit16(self.image, 0)
        self.painter.set_limit({0: limit})

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos) -> engine.Surface:
        coord = self.painter.get_coord(dungeon_tilemap, position)
        return get_image16(self.image, coord)
