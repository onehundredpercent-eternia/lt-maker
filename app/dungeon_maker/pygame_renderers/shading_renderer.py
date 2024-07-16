from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.pygame_renderers.renderer_utils import find_limit, get_image16
from app.engine import engine

class ShadingRenderer:
    def __init__(self, painter: Painter, main_image_fn: str, shading_image_fn: str):
        self.painter = painter
        self.main_image = engine.image_load(main_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        limit: int = find_limit(self.main_image, 0)
        self.painter.set_limit({0: limit})

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap,
                         position: Pos) -> engine.Surface:
        coord = self.painter.get_coord(dungeon_tilemap, position)
        shading_coord = self.painter.get_shading_coord(dungeon_tilemap, position)

        base_image = get_image16(self.main_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.shading_image, shading_coord)

        if shading_image:
            base_image.blit(shading_image, (0, 0))

        return base_image
