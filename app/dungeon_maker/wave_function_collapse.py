from collections import Counter

from app.engine import engine

from typing import List, Dict, Tuple

Point = Tuple[int, int]
Color3 = Tuple[int, int, int]
PatternHash = int

direction_offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]

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

def adjacency_extraction(patterns: Dict[PatternHash, List[Color3]], pattern_size: int) -> List[Tuple[Point, int, int]]:
    """
    Take a pattern grid and return a list of legal adjacencies found in it
    """

    def is_valid_overlap(adjacency_direction: Point, pattern1: int, pattern2: int) -> bool:
        return True

    pattern_list = list(patterns.keys())
    legal = []
    for pattern1 in pattern_list:
        for pattern2 in pattern_list:
            for direction in direction_offsets:
                if is_valid_overlap_xy(direction, pattern1, pattern2):
                    legal.append((direction, pattern1, pattern2))
    return legal


def execute(image_fn: str, pattern_width: int = 2, output_size: Tuple[int, int] = (20, 15), attempt_limit: int = 10):
    image, image_size = read_image_file(image_fn)
    tile_grid, code_list, unique_tiles = make_tile_catalog(image, image_size)
    patterns, pattern_incidence = make_pattern_catalog(tile_grid, pattern_width, image_size)
    adjacency_relations = adjacency_extraction(patterns, pattern_width)
    number_of_patterns = len(pattern_incidence)
    print("Number of Patterns: %d" % number_of_patterns)

    # Set up, for each direction, which patterns connect to which patterns
    adjacency_list: Dict[Point, Dict[PatternHash, Set[PatternHash]]] = {}
    for direction in direction_offsets:
        adjacency_list[direction] = {pattern: set() for pattern in pattern_incidence}
    for direction, pattern1, pattern2 in adjacency_relations:
        adjacency_list[direction][pattern1].add(pattern2)

    wave = make_wave(number_of_patterns, output_size[0], output_size[1])

    attempts = 0
    while attempts < attempt_limit:
        attempts += 1
        try:
            solution = run(wave.copy(), adjacency_list)
            solution_tile_grid = pattern_grid_to_tiles(solution, patterns)
            output_fn = image_fn[:-4] + "_output.png"
            render_output(solution_tile_grid, output_fn)
        except StopEarly:
            raise
        except Contradiction as exc:
            print("Contradiction on attempt %d of %d" % (attempts, attempt_limit))

    raise Timedout("Attempt Limit Exceeded!")

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
