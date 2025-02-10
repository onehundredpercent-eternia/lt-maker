from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painter_utils import Painter

class StairsUpDownPainter(Painter):
    """
    Determines which coordinate should be used for the stairs based
    on a small set of adjacency rules
    """
    terrain_like = (Terrain.STAIRS_UP, Terrain.STAIRS_DOWN)

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        _, east, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        left, right = False, False
        if east not in self.terrain_like:
            right = True
        if west not in self.terrain_like:
            left = True

        if left and right:
            coord = (0, 0)
        elif left:
            coord = (1, 0)
        elif right:
            coord = (2, 0)
        else:
            coord = (3, 0)
        return coord

class StairsLeftPainter(Painter):
    """
    Determines which coordinate should be used for the stairs based
    on a small set of adjacency rules
    """
    terrain_like = (Terrain.STAIRS_LEFT, )

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, _, south, _ = dungeon_tilemap.get_cardinal_terrain(pos)
        if north not in self.terrain_like:
            coord = (0, 0)
        else:
            coord = (1, 0)
        return coord

class StairsRightPainter(StairsLeftPainter):
    """
    Determines which coordinate should be used for the stairs based
    on a small set of adjacency rules
    """
    terrain_like = (Terrain.STAIRS_RIGHT, )
