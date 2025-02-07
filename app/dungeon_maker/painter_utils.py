from __future__ import annotations
from typing import Dict, Optional, TYPE_CHECKING

from app.utilities.typing import Pos
if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap

class Painter:
    base_coord: Pos = (0, 0)

    def __init__(self, display_coord: Optional[Pos] = None):
        self.limit: Optional[Dict[int, int]] = None
        self.base_coord = display_coord or self.base_coord or (0, 0)

    def set_limit(self, limit: Dict[int, int]):
        self.limit = limit

    def single_process(self, dungeon_tilemap: DungeonTileMap) -> None:
        pass

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        return self.base_coord
