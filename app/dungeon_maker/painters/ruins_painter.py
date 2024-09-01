from typing import Dict, Tuple

from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painters.floor_painter import FloorPainter
from app.dungeon_maker.painters.noise_interface import NoiseInterface
from app.dungeon_maker.utilities import random_choice

class RuinsPainter(FloorPainter, NoiseInterface):
    """
    # Implements 16x16 Floor with Ruins
    """
    noise_vertices: Dict[Pos, bool] = {}
    noise_threshold: float = 0.5

    @staticmethod
    def get_index(dungeon_tilemap: DungeonTileMap, pos: Pos) -> int:
        center = RuinsPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = RuinsPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = RuinsPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = RuinsPainter.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = RuinsPainter.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = RuinsPainter.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = RuinsPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = RuinsPainter.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = RuinsPainter.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

        topleft = center + north + west + northwest >= 3
        topright = center + north + east + northeast >= 3
        bottomleft = center + south + west + southwest >= 3
        bottomright = center + south + east + southeast >= 3

        index = 1 * topright + \
            2 * bottomright + \
            4 * bottomleft + \
            8 * topleft
        return index

    def get_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Tuple[Pos, Pos]:
        index = RuinsPainter.get_index(dungeon_tilemap, pos)

        coord = random_choice([(index, k) for k in range(self.limit[index])], pos)
        shading_coord = self.get_shading_coord(dungeon_tilemap, pos)

        return coord, shading_coord
