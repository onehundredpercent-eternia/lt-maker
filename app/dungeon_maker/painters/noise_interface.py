from typing import Dict
from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.utilities import get_random_seed
from app.map_maker import simplex_noise

class NoiseInterface:
    def single_process(self, tilemap: DungeonTileMap):
        # Generate a noise map and use that to fill the noise_vertices with True or False
        # depending on threshold
        seed = get_random_seed()
        noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
            (tilemap.width * 2 + 1, tilemap.height * 2 + 1), seed,
            starting_frequency=0.125)
        self.noise_vertices = {pos: value > self.noise_threshold for pos, value in noise_map.items()}
