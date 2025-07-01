from typing import Any, Dict, Optional

from app.map_maker import simplex_noise

from app.utilities.typing import NID, Pos

def generate_terrain(theme: Dict[NID, Any], seed: int) -> WorldTileMap:
    while True:
        result = _generate_terrain_process(theme, seed)
        seed += 1  # If that didn't work, try a different seed
        if result:
            break

    return result

def _generate_terrain_process(theme: Dict[NID, Any], seed: int) -> Optional[WorldTileMap]:
    tilemap = WorldTileMap(theme, seed)

    # 1. Generate a simplex noise field of the right size and parameters from the theme
    terrain_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width, tilemap.height), seed, theme['starting_frequency'],
        theme['starting_amplitude'], theme['octaves'], theme['lacunarity'],
        theme['gain'])

    # 2. Assign terrain based on the simplex noise field
    tilemap.generate_terrain_grid_from_noise(terrain_noise_map)

    # 3. Figure out where cliffs go
    # 4. Figure out where rivers go

    # 5. Figure out where forests go
    forest_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width, tilemap.height), seed, theme['forest_starting_frequency'],
        theme['forest_starting_amplitude'], theme['forest_octaves'], theme['forest_lacunarity'],
        theme['forest_gain'])
    tilemap.determine_forests_from_noise(forest_noise_map)

    # 6. Figure out where roads go
    # 7. Figure out where houses, castles, and ruins go

    return tilemap

class WorldTileMap:
    def __init__(self, theme: Dict[NID, Any], seed: int):
        self.random = static_random.LCG(seed)
        self.theme = theme
        self.width, self.height = theme["size"]
        self.terrain_grid: Dict[Pos, Terrain] = {}

    def get_terrain(self, pos: Pos) -> Optional[Terrain]:
        return self.terrain_grid.get(pos, None)

    def check_bounds(self, pos: Pos) -> bool:
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def generate_terrain_grid_from_noise(self, noise_map: Dict[Pos, float]):
        for x in range(self.width):
            for y in range(self.height):
                value: float = noise_map[(x, y)]
                if value >= 0.95:
                    terrain = Terrain.MOUNTAIN
                elif 0.95 > value >= 0.8:
                    terrain = Terrain.HILL
                elif 0.8 > value >= 0.4:
                    terrain = Terrain.NOISY_GRASS
                elif 0.4 > value >= 0.3:
                    terrain = Terrain.SAND
                else:
                    terrain = Terrain.SEA
                self.terrain_grid[(x, y)] = terrain

    def determine_forests_from_noise(self, noise_map: Dict[Pos, float]):
        for x in range(self.width):
            for y in range(self.height):
                value: float = noise_map[(x, y)]
                if self.get_terrain((x, y)) != Terrain.NOISY_GRASS:
                    continue  # Don't bother if not grass
                
                if value >= (1 - self.theme['thick_forest_threshold']):
                    self.terrain_grid[(x, y)] = Terrain.THICKET
                elif (1 - self.theme['thick_forest_threshold']) > value >= (1 - self.theme['forest_threshold']):
                    self.terrain_grid[(x, y)] = Terrain.FOREST
