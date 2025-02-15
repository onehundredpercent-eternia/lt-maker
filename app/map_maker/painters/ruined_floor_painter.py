from typing import Dict, Tuple

from app.utilities.typing import Pos
from app.map_maker.painters import FloorPainter
from app.map_maker.painters.noise_interface import NoiseInterface
from app.map_maker.utilities import random_choice

class RuinedFloorPainter(NoiseInterface, FloorPainter):
    """
    # Implements 16x16 Floor with Ruins
    """
    noise_vertices: Dict[Pos, bool] = {}
    noise_threshold: float = 0.5

    def _get_index(self, tilemap, pos: Pos) -> int:
        center = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = self.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

        topleft = center + north + west + northwest >= 3
        topright = center + north + east + northeast >= 3
        bottomleft = center + south + west + southwest >= 3
        bottomright = center + south + east + southeast >= 3

        index = 1 * topright + \
            2 * bottomright + \
            4 * bottomleft + \
            8 * topleft
        return index

    def get_coord(self, tilemap, pos: Pos) -> Tuple[Pos, Pos]:
        index = self._get_index(tilemap, pos)
        coord = random_choice([(index, k) for k in range(self.limit[index])], pos)
        return coord
