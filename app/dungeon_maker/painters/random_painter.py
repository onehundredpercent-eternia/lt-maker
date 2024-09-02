from __future__ import annotations
from typing import Tuple, TYPE_CHECKING

from app.utilities.typing import Pos
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.utilities import random_choice
from app.dungeon_maker.terrain import Terrain

if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap

class RandomPainter(Painter):
    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        return coord

class RandomShadingPainter(Painter):
    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[Pos, Pos]:
        coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        
        # Figure out shading
        shading_coord = None
        _, _, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        if west in (Terrain.WALL_TOP, Terrain.WALL_BOTTOM, Terrain.PILLAR):
            shading_coord = (coord[0] + 1, coord[1])

        return coord, shading_coord
