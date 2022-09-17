import math, random
from collections import Counter

from app.engine import engine

from typing import List, Dict, Tuple, Set, Callable

Point = Tuple[int, int]
Color3 = Tuple[int, int, int]
PatternHash = int

direction_offsets = [(0, -1), (1, 0), (0, 1), (-1, 0)]

class Contradiction(Exception):
    """Solver could not proceed."""
    pass

class TimedOut(Exception):
    """
    Solver ran out of attempts
    """
    pass

def shannon_entropy(weights: List[int]) -> float:
    """
    Returns the entropy of the given list of weights
    1 is highly entropic and random
    0 is a single settled possibility
    """
    assert(len(weights) > 0)
    n = sum(weights)
    assert(n > 0)
    probabilities = [weight / n for weight in weights]
    log_probabilities = [math.log2(_) for _ in probabilities]
    total = sum([a * b for a, b in zip(probabilities, log_probabilities)])
    constant = -1 / math.log2(n)
    h = constant * total
    assert(0 <= h <= 1)
    return h

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
            r, g, b, _ = image.get_at((x, y))
            tile_grid[(x, y)] = (r, g, b)
            code_list.append((r, g, b))

    unique_tiles = Counter()
    for color in code_list:
        unique_tiles[color] += 1
    
    return tile_grid, code_list, unique_tiles

def hash_pattern(pattern: List[Color3]) -> int:
    return hash(tuple(pattern))

def get_offsets(ksize: int) -> List[Point]:
    return [(x, y) for y in range(ksize) for x in range(ksize)]  

def make_pattern_catalog(tile_grid: Dict[Point, Color3], ksize: int, im_size: Tuple[int, int]) -> Tuple[Dict[PatternHash, List[Color3]], Dict[PatternHash, int]]:
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
        actual_pattern1: List[Color3] = patterns[pattern1]
        actual_pattern2: List[Color3] = patterns[pattern2]

        offsets = get_offsets(pattern_size)
        if adjacency_direction == (-1, 0):
            pattern_match1 = lambda offset: offset[0] != pattern_size - 1
            pattern_match2 = lambda offset: offset[0] != 0
        elif adjacency_direction == (1, 0):
            pattern_match1 = lambda offset: offset[0] != 0
            pattern_match2 = lambda offset: offset[0] != pattern_size - 1
        elif adjacency_direction == (0, -1):
            pattern_match1 = lambda offset: offset[1] != pattern_size - 1
            pattern_match2 = lambda offset: offset[1] != 0
        elif adjacency_direction == (0, 1):
            pattern_match1 = lambda offset: offset[1] != 0
            pattern_match2 = lambda offset: offset[1] != pattern_size - 1

        adjacent1 = [actual_pattern1[idx] for idx, offset in enumerate(offsets) if 
                     pattern_match1(offset)]
        assert len(adjacent1) == pattern_size**2 - pattern_size, "%d %d" % (len(adjacent1), pattern_size)
        # Make negative to account for opposite direction
        adjacent2 = [actual_pattern2[idx] for idx, offset in enumerate(offsets) if 
                     pattern_match2(offset)]
        assert len(adjacent2) == pattern_size**2 - pattern_size, "%d %d" % (len(adjacent1), pattern_size)
        for adj1, adj2 in zip(adjacent1, adjacent2):
            if adj1 != adj2:
                return False
        return True

    pattern_list = list(patterns.keys())
    legal = []
    for pattern1 in pattern_list:
        for pattern2 in pattern_list:
            for direction in direction_offsets:
                if is_valid_overlap(direction, pattern1, pattern2):
                    legal.append((direction, pattern1, pattern2))
    return legal

class Solver:
    def __init__(self, wave: Dict[Point, Set[PatternHash]], 
                 adj: Dict[Point, Dict[PatternHash, Set[PatternHash]]],
                 pattern_incidence: Dict[PatternHash, int],
                 render_intermediate: Callable):
        self.wave = wave
        self.adj = adj
        self.pattern_incidence = pattern_incidence
        self.render_intermediate = render_intermediate
        self.counter = 0

        self.coords = list(self.wave.keys())
        random.shuffle(self.coords)

    @property
    def is_solved(self) -> bool:
        return all(len(possibilities) == 1 for possibilities in self.wave.values())

    def solve_next(self) -> bool:
        if self.is_solved:
            return True
        # Only needs to be done once
        if self.counter == 0:
            self.propagate()
            self.render_intermediate(self.wave, self.counter); self.counter += 1

        try:
            pattern, i, j = self.observe()
            self.wave[(i, j)] = {pattern}
            # self.print_wave()
            # self.render_intermediate(self.wave, self.counter); self.counter += 1
            self.propagate()
            self.render_intermediate(self.wave, self.counter); self.counter += 1
            return False  # Assume there are remaining steps
        except Contradiction:
            raise

    def num_possibilities(self):
        return sum([len(possibilities) for possibilities in self.wave.values()])

    def print_wave(self):
        print([len(patterns) for coord, patterns in sorted(self.wave.items())])

    def propagate(self):
        """
        Completely propagate any newly collapsed waves to all areas
        """
        last_count = self.num_possibilities()
        print(last_count)

        while True:
            # self.print_wave()
            # self.render_intermediate(self.wave, self.counter)
            for coord, possibility_cell in self.wave.items():
                for direction in self.adj:
                    dx, dy = direction
                    other_coord = (coord[0] + dx), (coord[1] + dy)
                    other_cell = self.wave.get(other_coord)
                    if other_cell is None:  # Output does not wrap, so it's possible to run into bounds
                        continue
                    # a = other_cell.copy()
                    other_possibilities = set()
                    for possibility in possibility_cell:                            
                        valid_possibilities = self.adj[direction][possibility]
                        other_possibilities |= valid_possibilities
                    other_cell &= other_possibilities
                    # if len(a) != len(other_cell):
                    #     print(direction, coord, other_coord)
                    #     print(len(a), "$", len(other_cell), "$", a, "$", other_cell)

            if self.num_possibilities() == last_count:
                break # No changes since the last loop, changed waves have been full propagated
            last_count = self.num_possibilities()

        if any(len(patterns) == 0 for patterns in self.wave.values()):
            raise Contradiction("Wave is in a contradictory state and cannot be solved")

        # self.print_wave()

    def observe(self):
        i, j = self.location_heuristic()
        pattern = self.pattern_heuristic(i, j)
        return pattern, i, j

    def location_heuristic(self):
        """
        Returns the location with the minimum amount of entropy
        That has more than one valid choice
        """
        min_entropy = 1 + .01
        min_coord = None
       
        for coord in self.coords:
            possibilities = self.wave[coord]
            if len(possibilities) == 0:
                raise Contradiction("Wave is in a contradictory state and cannot be solved")
            elif len(possibilities) == 1:
                continue  # Only one valid choice
            incidence = [self.pattern_incidence[possibility] for possibility in possibilities]
            entropy = shannon_entropy(incidence)
            if entropy < min_entropy:
                min_entropy = entropy
                min_coord = coord
        assert(min_coord is not None)
        return min_coord

    def pattern_heuristic(self, i: int, j: int) -> PatternHash:
        patterns = list(self.wave[(i, j)])  # Order matters here
        weights = [self.pattern_incidence[pattern] for pattern in patterns]
        choice = random.choices(patterns, weights=weights)[0]
        # print("Chosen Pattern: %s" % choice)
        return choice

def run(wave, adj, pattern_incidence, render_intermediate):
    solver = Solver(wave, adj, pattern_incidence, render_intermediate)
    while not solver.solve_next():
        pass
    return solver.wave

def pattern_grid_to_tiles(solution: Dict[Point, Set[PatternHash]], patterns: Dict[PatternHash, List[Color3]], pattern_size: int) -> Dict[Point, Color3]:
    tile_grid: Dict[Point, Color3] = {}
    for coord, pattern_set in solution.items():
        pattern: List[Color3] = patterns[next(iter(pattern_set))]
        offsets = get_offsets(pattern_size)
        for idx, offset in enumerate(offsets):
            new_coord = (coord[0] + offset[0]), (coord[1] + offset[1])
            # This section is for testing
            if new_coord in tile_grid:
                current_pattern: Color3 = tile_grid[new_coord]
                if pattern[idx] != current_pattern:
                    print("Something's gone wrong with the pattern matching...", offset)
            # End testing
            tile_grid[new_coord] = pattern[idx]
    return tile_grid

def color_mean(colors: List[Color3]) -> Color3:
    num = len(colors)
    r = int(sum(color[0] for color in colors) / num)
    g = int(sum(color[1] for color in colors) / num)
    b = int(sum(color[2] for color in colors) / num)
    return (r, g, b)

def render_output(tile_grid: Dict[Point, Color3], output_fn: str, output_size: Tuple[int, int]) -> None:
    width, height = output_size
    im = engine.create_simple_surface(output_size)
    for x in range(width):
        for y in range(height):
            im.set_at((x, y), tile_grid[(x, y)])
    engine.save_surface(im, output_fn)

def get_render(patterns, pattern_size: int, 
               output_size: Tuple[int, int],
               output_magnification: int):
    def render_intermediate(wave, idx: int):
        print("Rendering: %d" % idx)
        tile_grid: Dict[Point, List[Color3]] = {}
        for coord, pattern_set in wave.items():
            if coord not in tile_grid:
                tile_grid[coord] = list()
            for pattern in pattern_set:
                color = patterns[pattern][0]
                tile_grid[coord].append(color)

        width, height = output_size
        im = engine.create_simple_surface(output_size)
        for x in range(width):
            for y in range(height):
                color = color_mean(tile_grid[(x, y)])
                im.set_at((x, y), color)
        scale = (output_magnification * width, output_magnification * height)
        im = engine.transform_scale(im, scale)
        engine.save_surface(im, 'app/dungeon_maker/intermediate%03d.png' % idx)

    return render_intermediate

def execute(image_fn: str, pattern_width: int = 2, 
            output_size: Tuple[int, int] = (10, 10), 
            attempt_limit: int = 10, seed=0, 
            render_intermediate=False,
            output_magnification=1) -> None:
    assert pattern_width >= 2
    random.seed(seed)
    image, image_size = read_image(image_fn)
    print(image_size)
    print(get_offsets(pattern_width))
    tile_grid, code_list, unique_tiles = make_tile_catalog(image, image_size)
    print(len(unique_tiles))
    patterns, pattern_incidence = make_pattern_catalog(tile_grid, pattern_width, image_size)
    print(pattern_incidence)
    adjacency_relations = adjacency_extraction(patterns, pattern_width)
    number_of_patterns = len(pattern_incidence)
    print("Number of Patterns: %d" % number_of_patterns)

    if True:
        for hs, pattern in patterns.items():
            print(hs)
            print(pattern)

    # Set up, for each direction, which patterns connect to which patterns
    adjacency_list: Dict[Point, Dict[PatternHash, Set[PatternHash]]] = {}
    for direction in direction_offsets:
        adjacency_list[direction] = {pattern: set() for pattern in pattern_incidence}
    for direction, pattern1, pattern2 in adjacency_relations:
        adjacency_list[direction][pattern1].add(pattern2)

    if False:
        for direction in adjacency_list:
            for pattern1 in adjacency_list[direction]:
                print(direction, patterns[pattern1])
                other_patterns = [patterns[pattern2] for pattern2 in adjacency_list[direction][pattern1]]
                print(len(other_patterns))
                print(other_patterns)

    if render_intermediate:
        render_intermediate = get_render(patterns, pattern_width, output_size, output_magnification)
    else:
        render_intermediate = lambda wave, idx: 0  # Pass

    attempts = 0
    while attempts < attempt_limit:
        attempts += 1
        try:
            wave: Dict[Point, Set[PatternHash]] = {(x, y): set(pattern_incidence.keys()) for x in range(output_size[0]) for y in range(output_size[1])}
            solution = run(wave, adjacency_list, pattern_incidence, render_intermediate)
            solution_tile_grid = pattern_grid_to_tiles(solution, patterns, pattern_width)
            output_fn = image_fn[:-4] + "_output.png"
            render_output(solution_tile_grid, output_fn, output_size)
            return
        except Contradiction:
            print("Contradiction on attempt %d of %d" % (attempts, attempt_limit))

    raise TimedOut("Attempt Limit Exceeded!")

if __name__ == '__main__':
    execute('app/dungeon_maker/wfc_input4.png', 3, (30, 30), 10, seed=0, render_intermediate=True, output_magnification=16)
