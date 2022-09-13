from collections import Counter

from app.engine import engine

from typing import List, Dict, Tuple

Point = Tuple[int, int]
Color3 = Tuple[int, int, int]
PatternHash = int

def read_image(image_fn: str) -> Tuple[engine.Surface, Tuple[int, int]]:
    im = engine.image_load(image_fn)
    im_size = im.get_width(), im.get_height()
    return im, im_size

def make_tile_catalog(image: engine.Surface, image_size: Tuple[int, int]) -> Tuple[Dict[Point, Color3], List[Color3], Dict[Color3, int]]:
    """
    Takes an image and returns the following
    tile_grid is dictionary of the original image
    code_list is the original image in 1 dimension list
    unique_tiles is the set of tiles, plus the frequency of their occurence
    """
    width, height = image_size

    tile_grid = {}
    code_list = []
    for x in range(width):
        for y in range(height):
            r, g, b = image.get_color((x, y))
            tile_grid[(x, y)] = (r, g, b)
            code_list.append((r, g, b))

    unique_tiles = Counter()
    for pos, color in code_list:
        unique_tiles[color] += 1
    
    return tile_grid, code_list, unique_tiles

def hash_pattern(pattern: List[Color3]) -> int:
    return hash(tuple(pattern))

def get_offsets(ksize: int) -> List[Point]:
    return [(x, y) for x in range(ksize) for y in range(ksize)]  

def make_pattern_catalog(tile_grid: Dict[Point, Color], ksize: int, im_size: Tuple[int, int]) -> Tuple[Dict[PatternHash, List[Color3]], Dict[PatternHash, int]]:
    """
    Returns a pattern catalog (dictionary of pattern hashes to constituent tiles),
    pattern weights (dictionary of pattern hashes to incidence)
    """

    width, height = im_size
    patterns = {}
    pattern_incidence = Counter()
    for x in range(width):
        for y in range(height):
            pattern = []
            for kx, ky in get_offsets(ksize):
                point = (x + kx) % width, (y + ky) % height  # mod so it wraps
                pattern.append(tile_grid[point])
            pattern_hash = hash_pattern(pattern)
            patterns[pattern_hash] = pattern
            pattern_incidence[pattern_hash] += 1
    return patterns, pattern_incidence

def execute(image_fn, pattern_width=2):
    image, image_size = read_image_file(image_fn)
    tile_grid, code_list, unique_tiles = make_tile_catalog(image, image_size)
    patterns, pattern_incidence = make_pattern_catalog(tile_grid, pattern_width, image_size)

def solve(adjacencies, wave_matrix):
    contradiction = False
    while not contradiciton:
        wave_matrix = propagate(wave_matrix, adjacencies)
        if all_domains_collapsed:
            return wave_matrix
        wave_matrix = observe(wave_matrix)
    throw ValueError("Resource Generation Failed")

def observe(wave_matrix):
    """
    Finds the most constrained variable and picks a value to assign
    """
    # Find the minimum entropy cell in grid
    cell = find_minimum_entropy(wave_matrix)
    if all(cell.entropy == 0 for cell in wave_matrix):
        # We are done
        return wave_matrix
    cell.value = get_value(cell)
    propagation_stack.append(cell)

def propagate(wave_matrix, adjacencies):
    """
    Update the domain of variables at each grid location
    """
