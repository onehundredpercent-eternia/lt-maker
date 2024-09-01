from typing import Dict, Tuple

from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painters.floor_painter import FloorPainter
from app.dungeon_maker.painters.noise_interface import NoiseInterface
from app.dungeon_maker.utilities import random_choice

class GrassPainter(FloorPainter, NoiseInterface):
    """
    # Implements 8x8 Floor with Grass
    """
    noise_vertices: Dict[Pos, bool] = {}
    noise_threshold: float = 0.55

    @staticmethod
    def get_index(dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[int, int, int, int]:
        center = GrassPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = GrassPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = GrassPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = GrassPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = GrassPainter.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = GrassPainter.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = GrassPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = GrassPainter.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = GrassPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

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
        index1, index2, index3, index4 = GrassPainter.get_index(dungeon_tilemap, pos)
        coord1 = random_choice([(index1, k) for k in range(self.limit[index1])], (pos[0] * 2, pos[1] * 2))
        coord2 = random_choice([(index2, k) for k in range(self.limit[index2])], (pos[0] * 2 + 1, pos[1] * 2))
        coord3 = random_choice([(index3, k) for k in range(self.limit[index3])], (pos[0] * 2 + 1, pos[1] * 2 + 1))
        coord4 = random_choice([(index4, k) for k in range(self.limit[index4])], (pos[0] * 2, pos[1] * 2 + 1))

        shading_coord = self.get_shading_coord(dungeon_tilemap, pos)

        return ((coord1, coord2, coord3, coord4), shading_coord)
