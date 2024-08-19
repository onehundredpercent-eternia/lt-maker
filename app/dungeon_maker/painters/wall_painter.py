from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painters import WangEdge2Painter
from app.dungeon_maker.utilities import random_choice

class WallTopPainter(WangEdge2Painter):
    terrain_like = (Terrain.WALL_TOP,)

    @staticmethod
    def get_index(dungeon_tilemap, pos):
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        north_edge = bool(north in WallTopPainter.terrain_like)
        south_edge = bool(south in WallTopPainter.terrain_like)
        east_edge = bool(east in WallTopPainter.terrain_like)
        west_edge = bool(west in WallTopPainter.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        index = WallTopPainter.get_index(dungeon_tilemap, pos)
        ne, se, sw, nw = dungeon_tilemap.get_diagonal_terrain(pos)
        # Edge is true when we have an adjacent walllike
        coord = random_choice([(index, k) for k in range(self.limit[index])], pos)

        if index in (12, 13) and sw == Terrain.WALL_TOP:
            coord = (15, 5)  # Requires walls at at least (W, SW, S)
        elif index in (6, 7) and se == Terrain.WALL_TOP:
            coord = (15, 4)  # Requires walls at at least (S, SE, E)
        elif index in (14, 15) and se == Terrain.WALL_TOP and sw == Terrain.WALL_TOP:
            coord = (15, 3)  # Requires walls at at least (S, SE, SW, E, W)
        elif index in (14, 15) and sw == Terrain.WALL_TOP:
            coord = (14, 5)  # Requires walls at at least (S, SW, E, W)
        elif index in (14, 15) and se == Terrain.WALL_TOP:
            coord = (14, 4)  # Requires walls at at least (S, SE, E, W)
        return coord

class WallBottomPainter(WangEdge2Painter):
    terrain_like = (Terrain.WALL_TOP, Terrain.WALL_BOTTOM)

    # Used by Floor Painter
    @staticmethod
    def is_a_column(dungeon_tilemap: DungeonTileMap, pos: Pos) -> bool:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        if west not in WallBottomPainter.terrain_like and east not in WallBottomPainter.terrain_like:
            north_pos = (pos[0], pos[1] - 1)
            # If north has no adjacent friends
            if north == Terrain.WALL_TOP and WallTopPainter.get_index(dungeon_tilemap, north_pos) == 0:
                return True
        return False

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        ne, se, sw, nw = dungeon_tilemap.get_diagonal_terrain(pos)

        ends_on_left, ends_on_right, shadow = True, True, False
        if west in self.terrain_like:
            ends_on_left = False
        if east in self.terrain_like:
            ends_on_right = False

        if west == Terrain.WALL_TOP:
            shadow = True
        elif sw in self.terrain_like:
            shadow = True
        elif west == Terrain.PILLAR:
            shadow = True

        if ends_on_left and ends_on_right:
            north_pos = (pos[0], pos[1] - 1)
            # If north has no adjacent friends
            if north == Terrain.WALL_TOP and WallTopPainter.get_index(dungeon_tilemap, north_pos) == 0:
                index = 6  # Is a column
            elif shadow:
                index = 5  # shadowcast on a wall that ends on both right and left
            else:
                index = 0  # Wall ends on both right and left
        elif shadow:
            if ends_on_right:
                index = 5  # shadowcast on a wall that ends on right
            else:
                index = 4  # Wall has a shadow cast on it
        elif ends_on_right:
            index = 2  # Wall ends on the right
        elif ends_on_left:
            index = 1  # Wall ends on the left
        else:
            index = 3  # Wall does not end on either side

        coord = index, 0
        return coord
