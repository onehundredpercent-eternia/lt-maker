from typing import Dict, Tuple

from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painters.floor_painter import FloorPainter
from app.dungeon_maker.painters.noise_interface import NoiseInterface
from app.dungeon_maker.utilities import random_choice
from app.dungeon_maker.terrain import Terrain

class GrassPainter(NoiseInterface, FloorPainter):
    """
    # Implements 8x8 Floor with Grass
    """
    noise_vertices: Dict[Pos, bool] = {}
    noise_threshold: float = 0.55

    def get_index(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[int, int, int, int]:
        center = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = self.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

        # since it doesn't look good, make sure the green sections don't overlap
        # the forest tiles
        n, e, s, w = dungeon_tilemap.get_cardinal_terrain(pos)
        ne, se, sw, nw = dungeon_tilemap.get_diagonal_terrain(pos)
        north &= (all(k != Terrain.SPARSE_FOREST for k in (n, ne, nw, e, w)))
        east &= (all(k != Terrain.SPARSE_FOREST for k in (e, ne, se, s, n)))
        south &= (all(k != Terrain.SPARSE_FOREST for k in (s, se, sw, e, w)))
        west &= (all(k != Terrain.SPARSE_FOREST for k in (w, nw, sw, s, n)))
        northeast &= (all(k != Terrain.SPARSE_FOREST for k in (ne, n, e)))
        southeast &= (all(k != Terrain.SPARSE_FOREST for k in (se, s, e)))
        southwest &= (all(k != Terrain.SPARSE_FOREST for k in (sw, s, w)))
        northwest &= (all(k != Terrain.SPARSE_FOREST for k in (nw, n, w)))
        center &= (all(k != Terrain.SPARSE_FOREST for k in (n, e, s, w)))

        # Topleft
        index1 = 1 * north + \
            2 * center + \
            4 * west + \
            8 * northwest
        # Topright
        index2 = 1 * northeast + \
            2 * east + \
            4 * center + \
            8 * north
        # Bottomright
        index3 = 1 * east + \
            2 * southeast + \
            4 * south + \
            8 * center
        # Bottomleft
        index4 = 1 * center + \
            2 * south + \
            4 * southwest + \
            8 * west
        return index1, index2, index3, index4

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[Tuple[Pos, Pos, Pos, Pos], Pos]:
        index1, index2, index3, index4 = self.get_index(dungeon_tilemap, pos)
        coord1 = random_choice([(index1, k) for k in range(self.limit[index1])], (pos[0] * 2, pos[1] * 2))
        coord2 = random_choice([(index2, k) for k in range(self.limit[index2])], (pos[0] * 2 + 1, pos[1] * 2))
        coord3 = random_choice([(index3, k) for k in range(self.limit[index3])], (pos[0] * 2 + 1, pos[1] * 2 + 1))
        coord4 = random_choice([(index4, k) for k in range(self.limit[index4])], (pos[0] * 2, pos[1] * 2 + 1))

        shading_coord = self.get_shading_coord(dungeon_tilemap, pos)

        return ((coord1, coord2, coord3, coord4), shading_coord)
