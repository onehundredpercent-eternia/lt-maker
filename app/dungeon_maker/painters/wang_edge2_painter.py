from typing import Tuple
from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.utilities import random_choice

class WangEdge2Painter(Painter):
    """
    Selects the correct painter coordinate for the tile by determining which
    cardinally adjacent tiles are of a similar terrain type.
    Which column is determined by the method below, and which row is randomized
    from available rows.
    0 - No adjacent
    1 - North
    2 - East
    3 - North and East
    4 - South
    5 - South and North
    6 - South and East
    etc.
    """
    terrain_like: Tuple[Terrain] = tuple()

    def _determine_index(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> int:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def get_coord(self, dungeon_tilemap: DungeonTileMap, position: Pos) -> Pos:
        col_idx = self.determine_index(dungeon_tilemap, position)
        coord = random_choice([(col_idx, k) for k in range(self.limit[col_idx])], position)
        return coord
