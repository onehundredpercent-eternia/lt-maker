from typing import Optional, Tuple
from app.utilities.typing import Pos

from app.map_maker.painter_utils import Painter
from app.map_maker.utilities import random_choice
from app.map_maker.painters.wall_painter import WallBottomPainter
from app.map_maker.terrain import Terrain

class FloorPainter(Painter):
    """
    Selects the correct painter coordinate for the tile by determining
    what kind of shading should be painted on the floor.
    For instance, if a wall is to the left of this floor tile, the painter
    will select a tile that has shading on the left to make the shadow appear
    """

    def get_coord(self, tilemap, pos: Pos) -> Pos:
        coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        return coord

    @staticmethod
    def is_column_bottom(tilemap, pos: Pos) -> bool:
        """
        Returns whether the position is the bottom of a wall column
        """
        north, _, _, _ = tilemap.get_cardinal_terrain(pos)
        if north == Terrain.WALL_BOTTOM and WallBottomPainter.is_a_column(tilemap, (pos[0], pos[1] - 1)):
            return True
        return False

    @staticmethod
    def get_pillar_coord(dungeon_tilemap, pos: Pos) -> Optional[Pos]:
        """
        Returns coordinate on shading tileset for the bottom of the pillar
        """
        north, _, _, _ = dungeon_tilemap.get_cardinal_terrain(pos)
        _, left, corner = FloorPainter.get_shading(dungeon_tilemap, pos)
        if north == Terrain.PILLAR:
            if left or corner:
                return (6, 0)
            else:
                return (5, 0)
        return None

    @staticmethod
    def get_shading(dungeon_tilemap, pos: Pos) -> Tuple[bool, bool, bool]:
        north, _, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        _, _, _, northwest = dungeon_tilemap.get_diagonal_terrain(pos)
        top, left, corner = False, False, False

        if north in (Terrain.WALL_TOP, Terrain.WALL_BOTTOM):
            top = True
        if west in (Terrain.WALL_TOP, Terrain.WALL_BOTTOM):
            left = True
        if northwest == Terrain.PILLAR:
            corner = True
        if west == Terrain.PILLAR:
            left = True
        if west == Terrain.STAIRS_LEFT and northwest in (Terrain.WALL_TOP, Terrain.WALL_BOTTOM):
            corner = True
        if northwest in (Terrain.WALL_TOP, Terrain.WALL_BOTTOM) \
                and west in (Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER) \
                and FloorPainter.is_column_bottom(dungeon_tilemap, (pos[0] - 1, pos[1])):
            corner = True
        return top, left, corner

    def get_shading_coord(self, dungeon_tilemap, pos: Pos) -> Pos:
        top, left, corner = FloorPainter.get_shading(dungeon_tilemap, pos)

        shading_coord = None
        if top and left:
            shading_coord = (3, 0)
        elif top and corner:
            shading_coord = (4, 0)
        elif left:
            shading_coord = (0, 0)
        elif corner:
            shading_coord = (2, 0)
        elif top:
            shading_coord = (1, 0)

        return shading_coord
