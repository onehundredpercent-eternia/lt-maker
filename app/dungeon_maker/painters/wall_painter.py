from enum import Enum
from typing import List, Optional

from app.utilities import utils
from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painters import WangEdge2Painter
from app.dungeon_maker.utilities import random_choice

class WallPainter(WangEdge2Painter):
    terrain_like = (Terrain.WALL,)

    class WallKind(Enum):
        BOTTOM = 1
        TOP = 2

    def __init__(self):
        super().__init__()
        self.wall_grid = {}

    def single_process(self, dungeon_tilemap: DungeonTileMap) -> None:
        """
        Generates the wall grid, which is used to determine
        whether we need a TOP wall or a BOTTOM wall for this sprite
        """
        all_walls = {pos for pos, terrain in dungeon_tilemap.terrain_grid.items() if terrain == Terrain.WALL}

        # First, build standalone columns
        for pos in all_walls.copy():
            north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
            if east != Terrain.WALL and west != Terrain.WALL and south != Terrain.WALL:
                if dungeon_tilemap.calc_layer(pos) == 1 and north == Terrain.WALL:
                    self.wall_grid[pos] = self.WallKind.BOTTOM
                else:
                    self.wall_grid[pos] = self.WallKind.TOP
                all_walls.remove(pos)

        for pos in all_walls.copy():
            north, _, south, _ = dungeon_tilemap.get_cardinal_terrain(pos)
            if north == Terrain.WALL and south != Terrain.WALL:
                self.wall_grid[pos] = self.WallKind.BOTTOM
                all_walls.remove(pos)

        # All remaining walls are TOP walls
        for pos in all_walls:
            self.wall_grid[pos] = self.WallKind.TOP

    def _get_cardinal_wallgrid(self, pos: Pos) -> List[Optional[WallKind]]:
        return [self.wall_grid.get(adj, None) for adj in utils.get_cardinal_positions(pos)]

    def _get_diagonal_wallgrid(self, pos: Pos) -> List[Optional[WallKind]]:
        return [self.wall_grid.get(adj, None) for adj in utils.get_diagonal_positions(pos)]

    def _get_top_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        nwall, ewall, swall, wwall = self._get_cardinal_wallgrid(pos)
        newall, sewall, swwall, nwwall = self._get_diagonal_wallgrid(pos)
        # Edge is true when we have an adjacent walllike
        north_edge = bool(north in self.terrain_like and nwall != self.WallKind.BOTTOM)
        south_edge = bool(south in self.terrain_like and swall != self.WallKind.BOTTOM)
        east_edge = bool(east in self.terrain_like and ewall != self.WallKind.BOTTOM)
        west_edge = bool(west in self.terrain_like and wwall != self.WallKind.BOTTOM)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        coord = random_choice([(index, k) for k in range(self.limits[index])], pos)

        if index in (12, 13) and swwall == self.WallKind.TOP:
            coord = (15, 5)
        elif index in (6, 7) and sewall == self.WallKind.TOP:
            coord = (15, 4)
        elif index in (14, 15) and sewall == self.WallKind.TOP and swwall == self.WallKind.TOP:
            coord = (15, 3) 
        return coord

    def _determine_sprite_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = dungeon_tilemap.get_diagonal_terrain(pos)

        if self.wall_grid[pos] == self.WallKind.BOTTOM:
            left, right, shadow = True, True, False
            if west in self.terrain_like and southwest not in self.terrain_like:
                left = False
            if east in self.terrain_like and southeast not in self.terrain_like:
                right = False
            if southwest in self.terrain_like:  # or southwest == 'Pillar':
                shadow = True

            if left and right:
                north_pos = (pos[0], pos[1] - 1)
                if self.wall_grid.get(north_pos) == self.WallKind.TOP and self._get_top_coord(dungeon_tilemap, north_pos)[0] == 0:
                    coord = (6, 5)
                elif shadow:
                    coord = (5, 5)
                else:
                    coord = (0, 5)
            elif left:
                if shadow:
                    coord = (4, 5)
                else:
                    coord = (1, 5)
            elif right:
                coord = (2, 5)
            else:
                coord = (3, 5)

        # Display the normal upper portion of the wall
        elif self.wall_grid[pos] == self.WallKind.TOP: 
            coord = self.get_top_coord(dungeon_tilemap, pos)

        else:
            raise Exception("Wall was not correctly processed: %s" % pos)
        return coord
