from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Tuple

import bisect
import math
import random
import time

from app.map_maker.terrain import Terrain
from app.map_maker import simplex_noise

from app.utilities import direction, static_random, utils
from app.utilities.typing import NID, Pos

NOISE_LACUNARITY = 2.0
NOISE_GAIN = 0.5
# Derived seeds -- distinct fields must not correlate, so each gets seed + its own offset.
HILL_SEED_OFFSET = 1
PASS_SEED_OFFSET = 2
# The pass field modulates mountain-spine width along each ridge; finer than the hill
# field so a low patch cuts *across* a ridge rather than tracking it. 2x -> a pass is
# roughly half a hill wavelength wide (a few tiles at the default frequency).
PASS_FREQUENCY_MULTIPLIER = 2.0
# Exponent on the pass field in the spine score. At 1.0 the hill budget spreads evenly
# between thinning skirts and cutting passes; >1 spends it on carving passes through
# ridges first, keeping skirts mountainous right up to the band edge elsewhere.
PASS_STRENGTH = 2.0

def derive_octaves(frequency: float) -> int:
    """Octaves whose wavelength falls below ~2 tiles (the tile Nyquist limit)
    add nothing visible, so octave depth follows from frequency."""
    return max(1, math.ceil(math.log2(0.5 / frequency)))

def get_threshold_from_percent(noise_map: Dict[Pos, float], percent: float,
                               width: int, height: int,
                               positions: Optional[Iterable[Pos]] = None) -> float:
    """Value v such that `percent`% of in-bounds tiles have noise < v.
    Mirrors Civ 4's CyFractal.getHeightFromPercent. Only in-bounds tiles
    (0 <= x < width, 0 <= y < height) count; the border ring is excluded.
    `positions`, if given, restricts the percentile pool to that subset
    (e.g. land tiles only) instead of the full width x height grid."""
    if positions is None:
        positions = [(x, y) for x in range(width) for y in range(height)]
    values = sorted(noise_map[pos] for pos in positions)
    if percent <= 0:
        return values[0] - 1.0
    if percent >= 100:
        return values[-1] + 1.0
    index = min(len(values) - 1, int(len(values) * percent / 100))
    return values[index]

def generate_terrain(theme: Dict[NID, Any], seed: int) -> WorldTileMap:
    if seed == -1:  # Random seed
        random.seed(time.time())
        seed = random.randint(0, 999_999)
        print("Random Seed: %d" % seed)
    orig_seed = seed
    while True:
        result = _generate_terrain_process(theme, seed)
        seed += 1  # If that didn't work, try a different seed
        if result:
            break
        if seed > orig_seed + 10:
            return None

    return result

def generate_topology(theme: Dict[NID, Any], seed: int) -> Tuple[WorldTileMap, Dict[Pos, float], float, float]:
    """Elevation classification (SEA/SAND/land) plus hill/peak bands -- everything up to,
    but not including, the terrain-mutating passes (rivers/cliffs/forests). Split out from
    `_generate_terrain_process` so tests can measure band classification in isolation from
    those later passes, which also consume NOISY_GRASS/HILL tiles."""
    tilemap = WorldTileMap(theme, seed)

    # 1. Generate a simplex noise field of the right size and parameters from the theme
    terrain_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width + 2, tilemap.height + 2), seed, theme['starting_frequency'],
        1.0, derive_octaves(theme['starting_frequency']), NOISE_LACUNARITY,
        NOISE_GAIN)
    terrain_noise_map = simplex_noise.normalize_noise_map(terrain_noise_map)
    # Move noise map so it's topleft is (-1, -1)
    new_terrain_noise_map = {}
    for pos, value in terrain_noise_map.items():
        new_terrain_noise_map[(pos[0] - 1, pos[1] - 1)] = value
    terrain_noise_map = new_terrain_noise_map

    # Modify elevation
    new_terrain_noise_map = {}
    for pos, value in terrain_noise_map.items():
        new_terrain_noise_map[pos] = utils.clamp(value + theme['elevation'], 0, 1)
    terrain_noise_map = new_terrain_noise_map

    # Set Water Border
    if theme['water_border']:
        new_terrain_noise_map = {}
        for pos, value in terrain_noise_map.items():
            distance_from_center_x = abs(tilemap.width/2 - pos[0])/(tilemap.width/2)
            distance_from_center_y = abs(tilemap.height/2 - pos[1])/(tilemap.height/2)
            total_distance_from_center = math.sqrt(distance_from_center_x**2 + distance_from_center_y**2)
            if total_distance_from_center < 0.9:
                total_distance_from_center = 0
            new_value = value * utils.clamp(1 - total_distance_from_center, 0, 1)
            new_terrain_noise_map[pos] = new_value
        terrain_noise_map = new_terrain_noise_map

    # 1.5 Fill any sinks with the lowest average of the adjacent tiles
    new_terrain_noise_map = {}
    for pos, value in terrain_noise_map.items():
        adjacent_positions = [adj for adj in direction.get_cardinal_positions(pos) if adj in terrain_noise_map]
        lowest_average = min(terrain_noise_map[adj] for adj in adjacent_positions)
        if value < lowest_average:
            new_terrain_noise_map[pos] = lowest_average
        else:
            new_terrain_noise_map[pos] = value
    terrain_noise_map = new_terrain_noise_map

    # 2. Assign terrain based on the simplex noise field: SEA / SAND / land (NOISY_GRASS)
    sea_threshold, high_elevation_threshold = tilemap.generate_terrain_grid_from_noise(terrain_noise_map)

    # 2.5 Hills and mountains as bands of their own noise fields, decoupled from elevation,
    # so ranges snake across land instead of tracking the elevation blob.
    hill_frequency = theme['hill_frequency']
    hill_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width, tilemap.height), seed + HILL_SEED_OFFSET, hill_frequency,
        1.0, derive_octaves(hill_frequency), NOISE_LACUNARITY, NOISE_GAIN)
    hill_noise_map = simplex_noise.normalize_noise_map(hill_noise_map)

    pass_frequency = hill_frequency * PASS_FREQUENCY_MULTIPLIER
    pass_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width, tilemap.height), seed + PASS_SEED_OFFSET, pass_frequency,
        1.0, derive_octaves(pass_frequency), NOISE_LACUNARITY, NOISE_GAIN)
    pass_noise_map = simplex_noise.normalize_noise_map(pass_noise_map)

    tilemap.generate_bands_from_noise(hill_noise_map, pass_noise_map)

    return tilemap, terrain_noise_map, sea_threshold, high_elevation_threshold

def _generate_terrain_process(theme: Dict[NID, Any], seed: int) -> Optional[WorldTileMap]:
    tilemap, terrain_noise_map, sea_threshold, high_elevation_threshold = generate_topology(theme, seed)

    # 3. Figure out where rivers go
    tilemap.generate_rivers_from_noise(terrain_noise_map, high_elevation_threshold, sea_threshold)

    # 4. Figure out where cliffs go
    tilemap.generate_cliffs_from_noise(terrain_noise_map)

    # 5. Figure out where forests go
    forest_noise_map: Dict[Pos, float] = simplex_noise.gen_noise_map(
        (tilemap.width, tilemap.height), seed, theme['forest_starting_frequency'],
        1.0, derive_octaves(theme['forest_starting_frequency']), NOISE_LACUNARITY,
        NOISE_GAIN)
    forest_noise_map = simplex_noise.normalize_noise_map(forest_noise_map)
    tilemap.generate_forests_from_noise(forest_noise_map)

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

    def generate_terrain_grid_from_noise(self, noise_map: Dict[Pos, float]) -> Tuple[float, float]:
        # Cumulative percentile thresholds, computed on the final (post-elevation,
        # post-water-border, post-sink-fill) field, so ratios are exact for every seed.
        # This field now decides only SEA / SAND / land -- hills and mountains are
        # classified separately in generate_bands_from_noise, from the hill field.
        sea_percent = self.theme['sea_percent'] * 100
        sand_percent = self.theme['sand_percent'] * 100

        sea_threshold = get_threshold_from_percent(noise_map, sea_percent, self.width, self.height)
        sand_threshold = get_threshold_from_percent(noise_map, sea_percent + sand_percent, self.width, self.height)

        for x in range(self.width):
            for y in range(self.height):
                value: float = noise_map[(x, y)]
                if value < sea_threshold:
                    terrain = Terrain.SEA
                elif value < sand_threshold:
                    terrain = Terrain.SAND
                else:
                    terrain = Terrain.NOISY_GRASS
                self.terrain_grid[(x, y)] = terrain

        # Stand-in "high ground" bound for the river logic, which still reads the
        # elevation field for now (Phase 3 replaces river source selection entirely).
        high_elevation_threshold = get_threshold_from_percent(
            noise_map, 100 - self.theme['highland_percent'] * 100, self.width, self.height)

        return sea_threshold, high_elevation_threshold

    def generate_bands_from_noise(self, hill_noise_map: Dict[Pos, float], pass_noise_map: Dict[Pos, float]):
        # Hills/mountains form as percentile *bands* of the hill field (a level set of a
        # continuous field is an elongated ridge, not a blob) rather than being thresholded
        # directly -- this is what produces mountain ranges instead of scattered clumps.
        land_positions = [(x, y) for x in range(self.width) for y in range(self.height)
                           if self.get_terrain((x, y)) == Terrain.NOISY_GRASS]
        if not land_positions:
            return

        highland_percent = self.theme['highland_percent'] * 100
        half_width = highland_percent / 4  # two bands, each with two edges

        # Percentile rank of each land tile within the hill field; the bands and the
        # spines inside them are both defined in this space. Centrality is 0 on a
        # band's center line (the ridge crest) and 1 at its edge; tiles outside both
        # bands stay NOISY_GRASS.
        sorted_values = sorted(hill_noise_map[pos] for pos in land_positions)
        total = len(sorted_values)
        centrality: Dict[Pos, float] = {}
        for pos in land_positions:
            percentile = bisect.bisect_left(sorted_values, hill_noise_map[pos]) / total * 100
            for center in (25, 75):
                band_position = abs(percentile - center) / half_width
                if band_position < 1:
                    centrality[pos] = band_position
                    break
        if not centrality:
            return

        # Mountains are the most-central slice of each band, so every range is a
        # mountain spine flanked by hill skirts. The pass field scales spine width
        # along the ridge: where it nears zero the score diverges and the spine
        # pinches off entirely, leaving an all-hill gap -- a mountain pass.
        # Thresholding the score at a percentile over highland tiles keeps mountain
        # coverage at exactly peak_percent regardless of the pass field's distribution.
        score_map = {pos: value / max(pass_noise_map[pos], 1e-9) ** PASS_STRENGTH
                     for pos, value in centrality.items()}
        highland_positions = list(centrality)
        peak_percent = self.theme['peak_percent'] * 100
        peak_threshold = get_threshold_from_percent(score_map, peak_percent, self.width, self.height, highland_positions)

        for pos in highland_positions:
            if score_map[pos] <= peak_threshold:
                self.terrain_grid[pos] = Terrain.MOUNTAIN
            else:
                self.terrain_grid[pos] = Terrain.HILL

    def generate_cliffs_from_noise(self, noise_map: Dict[Pos, float]):
        # Use Sobel Edge Detection to find areas of discontinuity
        gx = [-1, 0, 1,
              -2, 0, 2,
              -1, 0, 1]
        gy = [1, 2, 1,
              0, 0, 0,
              -1, -2, -1]

        def convolve(values: List[float], kernel: List[int]) -> float:
            assert len(values) == len(kernel)
            return sum([(value * k) for value, k in zip(values, kernel)]) ** 2

        def non_max_suppression(gradient_magnitude: List[float], gradient_orientation: List[float]) -> List[float]:
            output = [0] * len(gradient_magnitude)

            # Ignore the border pixels
            for x in range(1, self.width - 1):
                for y in range(1, self.height - 1):
                    # Will be between -pi and pi
                    magnitude: float = gradient_magnitude[y + self.height * x]
                    direction: float = gradient_orientation[y + self.height * x] 
                    direction += math.pi  # Move to be between 0 and 2*pi

                    if (0 <= direction < math.pi / 8) or (15 * math.pi / 8 <= direction <= 2 * math.pi):
                        before_pixel = gradient_magnitude[y + self.height * (x - 1)]
                        after_pixel = gradient_magnitude[y + self.height * (x + 1)]

                    elif (math.pi / 8 <= direction < 3 * math.pi / 8) or (9 * math.pi / 8 <= direction < 11 * math.pi):
                        before_pixel = gradient_magnitude[(y + 1) + self.height * (x - 1)]
                        after_pixel = gradient_magnitude[(y - 1) + self.height * (x + 1)]

                    elif (3 * math.pi / 8 <= direction < 5 * math.pi / 8) or (11 * math.pi / 8 <= direction < 13 * math.pi):
                        before_pixel = gradient_magnitude[(y - 1) + self.height * x]
                        after_pixel = gradient_magnitude[(y + 1) + self.height * x]

                    else:
                        before_pixel = gradient_magnitude[(y - 1) + self.height * (x - 1)]
                        after_pixel = gradient_magnitude[(y + 1) + self.height * (x + 1)]

                    if magnitude >= before_pixel and magnitude >= after_pixel:
                        output[y + self.height * x] = magnitude
            return output

        x_image, y_image = [], []
        # Do the convolution
        for x in range(self.width):
            for y in range(self.height):
                values = [noise_map[(x - 1, y - 1)], noise_map[(x, y - 1)], noise_map[(x + 1, y - 1)],
                          noise_map[(x - 1, y)], noise_map[(x, y)], noise_map[(x + 1, y)],
                          noise_map[(x - 1, y + 1)], noise_map[(x, y + 1)], noise_map[(x + 1, y + 1)]]
                x_image.append(convolve(values, gx))
                y_image.append(convolve(values, gy))
        
        # Now generate a single magnitude for each point
        gradient_magnitude = [math.sqrt(x**2 + y**2) for (x, y) in zip(x_image, y_image)]
        gradient_orientation = [math.atan2(y, x) for (x, y) in zip(x_image, y_image)]
        max_magnitude = max(gradient_magnitude)
        if max_magnitude > 0:
            gradient_magnitude = [_ / max_magnitude for _ in gradient_magnitude]  # Now between 0 and 1
        else:
            gradient_magnitude = [0 for _ in gradient_magnitude]

        for x in range(self.width):
            for y in range(self.height):
                value: float = gradient_magnitude[y + self.height * x]
                if self.get_terrain((x, y)) != Terrain.NOISY_GRASS:
                    continue  # Don't bother if not grass
                
                if value >= (1 - self.theme['cliff_threshold']):
                    self.terrain_grid[(x, y)] = Terrain.CLIFF         

    def generate_forests_from_noise(self, noise_map: Dict[Pos, float]):
        for x in range(self.width):
            for y in range(self.height):
                value: float = noise_map[(x, y)]
                if self.get_terrain((x, y)) != Terrain.NOISY_GRASS:
                    continue  # Don't bother if not grass
                # Clamped noise (normalize_noise_map) can land exactly on value == 1.0,
                # so a bare `>= (1 - 0)` threshold would still fire at 0% chance.
                thick_forest_threshold = (1 - self.theme['thick_forest_threshold'])
                if self.theme['thick_forest_threshold'] > 0 and value >= thick_forest_threshold:
                    self.terrain_grid[(x, y)] = Terrain.THICKET
                elif self.theme['forest_threshold'] > 0 and thick_forest_threshold > value >= (1 - self.theme['forest_threshold']):
                    self.terrain_grid[(x, y)] = Terrain.FOREST

    def generate_rivers_from_noise(self, noise_map: Dict[Pos, float],
                                    high_elevation_threshold: float, sea_threshold: float):
        # Locate all locations near mountains, (high terrain noise)
        # Locate all locations near seas (low terrain noise)
        # based on a river incidence rate, draw connections between high noise tiles and low noise tiles, generally preferring low noise tile movement draw connections between the two
        # Then remove any rivers which cross each other (use order or something), and remove any rivers which overlap a mountain after leaving a mountain

        def get_start_and_end_candidates(high_limit: float, low_limit: float) -> Tuple[List[Pos], List[Pos]]:
            high_noise_locations: List[Pos] = []
            low_noise_locations: List[Pos] = []
            for x in range(self.width):
                for y in range(self.height):
                    value: float = noise_map[(x, y)]
                    if value >= high_limit:
                        high_noise_locations.append((x, y))
                    elif value < low_limit:
                        low_noise_locations.append((x, y))
            return high_noise_locations, low_noise_locations

        # Figure out which positions should be used as start and end positions
        high_limit = high_elevation_threshold
        low_limit = sea_threshold
        high_noise_locations, low_noise_locations = \
            get_start_and_end_candidates(high_limit, low_limit)
        while not high_noise_locations or not low_noise_locations:
            high_limit -= 0.05
            low_limit += 0.05
            high_noise_locations, low_noise_locations = \
                get_start_and_end_candidates(high_limit, low_limit)

        number_of_rivers = self.theme['river_incidence'] * self.width * self.height 
        rivers: List[List[Pos]] = []
        while len(utils.flatten_list(rivers)) < number_of_rivers and high_noise_locations:
            starting_point = self.random.choice(high_noise_locations)
            # Remove the starting point from the high noise locations
            high_noise_locations.remove(starting_point)

            river: List[Pos] = [starting_point]
            current_point = starting_point

            # Build out river!
            directions = []
            while True:
                adjacent_points = direction.get_cardinal_positions(current_point)
                # Make sure we don't go backwards
                adjacent_points = [pos for pos in adjacent_points if pos not in river]
                # Make sure we don't go in the same direction four times in row
                adjacent_points = [pos for pos in adjacent_points if len(river) < 4 
                                   or direction.Direction.determine(current_point, pos) != direction.Direction.determine(river[-2], river[-1])
                                   or direction.Direction.determine(current_point, pos) != direction.Direction.determine(river[-3], river[-2])
                                   or direction.Direction.determine(current_point, pos) != direction.Direction.determine(river[-4], river[-3])
                                   ]
                # Make sure we only go downhill
                adjacent_points = [pos for pos in adjacent_points if (noise_map[pos] if self.check_bounds(pos) else 0.2) <= noise_map[river[-1]]]

                if not adjacent_points:
                    # This is not a valid river, ignore it
                    river = []
                    break

                noise_values = [noise_map[pos] if self.check_bounds(pos) else 0.2 for pos in adjacent_points]
                min_index = noise_values.index(min(noise_values))
                directions.append(direction.Direction.determine(current_point, adjacent_points[min_index]))
                current_point = adjacent_points[min_index]
                # If reach sea, we are done
                # If reach the edge of the map, we are done
                # If reach another river, we are done
                if noise_map[current_point] < sea_threshold \
                        or not self.check_bounds(current_point) \
                        or current_point in utils.flatten_list(rivers):  
                    break
                else:
                    river.append(current_point)
            river = [pos for pos in river if self.get_terrain(pos) in (Terrain.HILL, Terrain.NOISY_GRASS, Terrain.SAND)]
            rivers.append(river)

        # Check that rivers don't cross each other -- Later
        # for river in rivers:

        # Convert terrain
        for river in rivers:
            for pos in river:
                current_terrain = self.get_terrain(pos)
                if current_terrain in (Terrain.HILL, Terrain.NOISY_GRASS, Terrain.SAND):
                    self.terrain_grid[pos] = Terrain.RIVER
