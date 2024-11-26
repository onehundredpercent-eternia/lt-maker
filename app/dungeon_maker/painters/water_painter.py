from typing import Tuple
from app.utilities.typing import Pos
from app.utilities import utils

from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.utilities import random_choice, random_random
from app.dungeon_maker.painters.wall_painter import WallBottomPainter

class WaterPainter(Painter):
    """
    Selects the correct painter coordinate for the tile by determining
    what kind of shading should be painted on the water.
    For instance, if a wall/floor is to the left of this tile, the painter
    will select a tile that has shading on the left to make the shadow appear
    """

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        dist = self._distance_to_closest(dungeon_tilemap, pos)
        if dist > (1 + 2*random_random(pos)):  # Open Sea
            coord = random_choice([(1, k) for k in range(self.limit[0])], pos)
        else:  # Close Sea
            coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        return coord

    def _distance_to_closest(self, dungeon_tilemap: DungeonTileMap, pos: tuple) -> float:
        min_distance = 99
        for other_pos in dungeon_tilemap.terrain_grid.keys():
            if dungeon_tilemap.get_terrain(other_pos) != Terrain.WATER:
                distance = utils.distance(pos, other_pos)
                if distance < min_distance:
                    min_distance = distance
        return min_distance

    @staticmethod
    def is_column_bottom(dungeon_tilemap: DungeonTileMap, pos: Pos) -> bool:
        """
        Returns whether the position is the bottom of a wall column
        """
        north, _, _, _ = dungeon_tilemap.get_cardinal_terrain(pos)
        if north == Terrain.WALL_BOTTOM and WallBottomPainter.is_a_column(dungeon_tilemap, (pos[0], pos[1] - 1)):
            return True
        return False

    @staticmethod
    def get_pillar_coord(dungeon_tilemap: DungeonTileMap, pos: Pos):
        return None

    @staticmethod
    def get_shading(dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[bool, bool, bool]:
        north, _, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        top, left, column = False, False, False

        if north != Terrain.WATER:
            top = True
        if west != Terrain.WATER:
            left = True
        if WaterPainter.is_column_bottom(dungeon_tilemap, pos):
            column = True
        return top, left, column

    def get_shading_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        top, left, column = WaterPainter.get_shading(dungeon_tilemap, pos)

        shading_coord = None
        if column and left:
            shading_coord = (4, 0)
        elif column:
            shading_coord = (3, 0)
        elif top and left:
            shading_coord = (2, 0)
        elif left:
            shading_coord = (0, 0)
        elif top:
            shading_coord = (1, 0)

        return shading_coord

class WaterBridgePainter(Painter):
    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        coord = random_choice([(0, k) for k in range(self.limit[0])], pos)
        return coord

    @staticmethod
    def get_shading(dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[bool, bool, bool]:
        _, _, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        left = False

        if west not in (Terrain.WATER, Terrain.WATERBRIDGE, Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER):
            left = True
        return left

    def get_shading_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        left = WaterBridgePainter.get_shading(dungeon_tilemap, pos)

        shading_coord = None
        if left:
            shading_coord = (1, 0)

        return shading_coord
