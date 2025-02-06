from app.utilities.typing import Pos

from app.map_maker.painters import WangEdge16Painter
from app.map_maker.terrain import Terrain
from app.map_maker.utilities import random_choice

class RiverPainter(WangEdge16Painter):
    terrain_like = (Terrain.RIVER, Terrain.SEA, Terrain.BRIDGEH, Terrain.BRIDGEV)

    def get_coord(self, tilemap, pos: Pos) -> Pos:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        northeast_edge = bool(not northeast or northeast in self.terrain_like)
        southeast_edge = bool(not southeast or southeast in self.terrain_like)
        southwest_edge = bool(not southwest or southwest in self.terrain_like)
        northwest_edge = bool(not northwest or northwest in self.terrain_like)
        if random_choice([1, 2], pos) == 1:
            use_top = True
        else:
            use_top = False
        # Handle true diagonals
        # Topleft
        if north_edge and west_edge and not south_edge and not east_edge:
            if use_top:
                new_coord2 = (9, 0)
                new_coord4 = (9, 1)
                new_coord3 = (8, 0)
                if northwest_edge:
                    new_coord1 = (2, 7)
                else:
                    new_coord1 = (2, 5)
            else:
                new_coord2 = (9, 2)
                new_coord4 = (9, 3)
                new_coord3 = (8, 1)
                if northwest_edge:
                    new_coord1 = (2, 6)
                else:
                    new_coord1 = (2, 4)
        # Topright
        elif north_edge and east_edge and not south_edge and not west_edge:
            if use_top:
                new_coord1 = (3, 0)
                new_coord3 = (3, 1)
                new_coord4 = (1, 0)
                if northeast_edge:
                    new_coord2 = (4, 6)
                else:
                    new_coord2 = (4, 4)
            else:
                new_coord1 = (3, 2)
                new_coord3 = (3, 3)
                new_coord4 = (1, 1)
                if northeast_edge:
                    new_coord2 = (4, 7)
                else:
                    new_coord2 = (4, 5)
        # Bottomleft
        elif south_edge and west_edge and not north_edge and not east_edge:
            if use_top:
                new_coord1 = (12, 0)
                new_coord3 = (12, 1)
                new_coord2 = (4, 1)
                if southwest_edge:
                    new_coord4 = (1, 7)
                else:
                    new_coord4 = (1, 5)
            else:
                new_coord1 = (12, 2)
                new_coord3 = (12, 3)
                new_coord2 = (4, 0)
                if southwest_edge:
                    new_coord4 = (1, 6)
                else:
                    new_coord4 = (1, 4)
        # Bottomright
        elif south_edge and east_edge and not north_edge and not west_edge:
            if use_top:
                new_coord2 = (6, 1)
                new_coord4 = (6, 0)
                new_coord1 = (2, 0)
                if southeast_edge:
                    new_coord3 = (8, 6)
                else:
                    new_coord3 = (8, 4)
            else:
                new_coord2 = (6, 2)
                new_coord4 = (6, 3)
                new_coord1 = (2, 1)
                if southeast_edge:
                    new_coord3 = (8, 7)
                else:
                    new_coord3 = (8, 5)

        # Waterfall -- TODO check the chirality of the cliff
        elif south_edge and north_edge and west and Terrain.cliff(west) and east and Terrain.cliff(east):
            new_coord1 = (0, 8)
            new_coord2 = (1, 8)
            new_coord3 = (1, 9)
            new_coord4 = (0, 9)
        else:
            index1 = 6 + 1 * north_edge + 8 * west_edge
            index2 = 12 + 1 * north_edge + 2 * east_edge
            index3 = 9 + 4 * south_edge + 2 * east_edge
            index4 = 3 + 4 * south_edge + 8 * west_edge
            new_coord1 = random_choice([(index1, k) for k in range(self.limits[index1])], pos)
            new_coord2 = random_choice([(index2, k) for k in range(self.limits[index2])], pos, offset=1)
            new_coord3 = random_choice([(index3, k) for k in range(self.limits[index3])], pos, offset=2)
            new_coord4 = random_choice([(index4, k) for k in range(self.limits[index4])], pos, offset=3)
            # Handle using the same set for vertical edges
            if index1 == 7:
                new_coord1 = (index1, random_choice([0, 1, 2, 3, 4], pos)*2)
            if index4 == 7:
                new_coord4 = (index4, random_choice([0, 1, 2, 3, 4], pos)*2 + 1)
            if index2 == 13:
                new_coord2 = (index2, random_choice([0, 1, 2, 3, 4], pos)*2)
            if index3 == 13:
                new_coord3 = (index3, random_choice([0, 1, 2, 3, 4], pos)*2 + 1)

        return new_coord1, new_coord2, new_coord3, new_coord4
