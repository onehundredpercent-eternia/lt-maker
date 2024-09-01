from __future__ import annotations
from typing import TYPE_CHECKING

from app.utilities.typing import Pos
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.utilities import random_choice

if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap

class RandomPainter(Painter):
    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        return coord
