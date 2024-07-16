from typing import Dict, Optional

from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap

class Painter:
    base_coord: Pos = (0, 0)

    def __init__(self):
        self.limit: Optional[Dict[int, int]] = None

    def set_limit(self, limit: Dict[int, int]):
        self.limit = limit

    def single_process(self, dungeon_tilemap: DungeonTileMap) -> None:
        pass

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        return self.base_coord
