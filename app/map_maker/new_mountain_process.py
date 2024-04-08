from __future__ import annotations

from typing import Dict, Tuple, Set, List, Optional, Iterable
from app.utilities.typing import Pos

from dataclasses import dataclass, field

from app.map_maker.utilities import random_choice, WeightedRandomizer
from app.utilities.utils import calculate_distance

class IncompatibleConnectionException(Exception):
    pass

class MissingRepresentationForPatternException(Exception):
    pass

MOUNTAIN_HEIGHT = 2.25

peak_start_end_pairs = {
    (2, 9): 8,
    (6, 8): 5,
    (2, 4): 5,
    (2, 8): 15,
    (1, 8): 8,
    (1, 9): 1,
    (2, 3): 4,
    (1, 3): 1,
}

valley_start_end_pairs = {
    (1, 9): 10,
    (3, 8): 3,
    (2, 9): 1,
    (3, 9): 6,
    (3, 7): 2,
}

@dataclass
class Line:
    segments: List[LineSegment] = field(default_factory=list)

    def append(self, segment: LineSegment):
        self.segments.append(segment)

    def __len__(self):
        return len(self.segments)

    def __iter__(self):
        return iter(self.segments)

    def __contains__(self, pos: Pos) -> bool:
        return pos in (ls.position for ls in self.segments)

    def near(self, pos: Pos) -> bool:
        # 1 is removed from the distance to account for the fact that
        # the line has to be placed somewhere
        target_distance = MOUNTAIN_HEIGHT * 2 - 1
        for line_pos in (ls.position for ls in self.segments):
            if calculate_distance(pos, line_pos) <= target_distance:
                return True
        return False 

    def average_x(self) -> float:
        return sum(ls.position[0] for ls in self) / len(self)

@dataclass
class LineSegment:
    """
    The pattern refer to where on the tile the line points to
    1 2 3
    4   6
    7 8 9  Like a telephone
    """
    position: Pos
    pattern: Tuple[int]  # Always a 2-tuple

    def get_printed_form(self):
        match self.pattern:
            case (1, 9):
                return r"\\"
            case (3, 8):
                return r" /"
            case (2, 9):
                return " \\"
            case (3, 9):
                return r" |"
            case (3, 7):
                return r"//"
            case (6, 8):
                return r" ,"
            case (2, 4):
                return r"' "
            case (2, 8):
                return r"||"
            case (1, 8):
                return r"\ "
            case (2, 3):
                return r" ^"
            case (1, 3):
                return r"^^"
            case _:
                raise MissingRepresentationForPatternException("Missing representation for the pattern: %s" % (self.pattern))

def _tile_on_outside_of_group(tile: Pos, group: List[Pos]) -> bool:
    adj_positions = ((-1, 0), (1, 0))  # Don't need to check north or south positions
    for adj in adj_positions:
        if (tile[0] + adj[0], tile[1] + adj[1]) not in group:
            return True
    return False

def _tile_near_outside_of_group(tile: Pos, group: List[Pos]) -> bool:
    adj_positions = ((-1, 0), (1, 0))  # Don't need to check north or south positions
    for adj in adj_positions:
        adj_tile = (tile[0] + adj[0], tile[1] + adj[1])
        if _tile_on_outside_of_group(adj_tile, group):
            return True
    return False

def _tile_on_line(tile: Pos, lines: List[Line]) -> bool:
    for line in lines:
        for ls in line:
            if tile == ls.position:
                return True
    return False

def _tile_near_line(tile: Pos, lines: List[Line]) -> bool:
    adj_positions = ((-1, 0), (0, -1), (1, 0), (0, 1))
    for adj in adj_positions:
        adj_tile = (tile[0] + adj[0], tile[1] + adj[1])
        if _tile_on_line(adj_tile, lines):
            return True
    return False

def _get_random_tile(group: List[Pos]) -> Optional[Pos]:
    weights = {}
    for tile in group:
        if _tile_on_outside_of_group(tile, group):
            continue
        elif _tile_near_outside_of_group(tile, group):
            weights[tile] = 0.01
        else:
            weights[tile] = 1
    if not weights:  # No tiles meet the requirements
        return None

    randomizer = WeightedRandomizer(weights, offset=len(group))
    return randomizer.random()

def _get_ridge_line(group: List[Pos], starting_tile: Pos, lines: List[Line], pattern_weights: Dict[Tuple[int, int], int]) -> Line:
    # Draw lines to the north and south randomly, favoring verticality
    # Stay away from other lines nearby
    # Repeat until you reach the ends of the group
    base_offset = starting_tile[0] * 1024**2 + starting_tile[1] * 1024
    line = Line()
    counter = 0
    randomizer = WeightedRandomizer(pattern_weights, base_offset + counter)

    pattern = randomizer.random()
    starting_ls = LineSegment(starting_tile, pattern) 
    line.append(starting_ls)

    def compatible(south: int, north: int) -> bool:
        return (
            (south == 9 and (north == 3 or north == 1 or north == 7))
            or (south == 8 and north == 2)
            or (south == 7 and (north == 1 or north == 3 or north == 9))
            or (south == 6 and north == 4)
            or (south == 4 and north == 6)
            or (south == 3 and (north == 7 or north == 9 or north == 1))
            or (south == 2 and north == 8)
            or (south == 1 and (north == 9 or north == 7 or north == 3))
        )

    def get_next_tile(ls: LineSegment, pattern: Tuple[int, int], north: bool) -> Pos:
        if north:
            other_connection = pattern[1]
            main_connection = ls.pattern[0]
        else:
            main_connection = ls.pattern[1]
            other_connection = pattern[0]
        x, y = ls.position
        connection = main_connection, other_connection
        match connection:
            case (9, 1):
                next_tile = x + 1, y + 1
            case (9, 3):
                next_tile = x, y + 1
            case (9, 7):
                next_tile = x + 1, y
            case (8, 2):
                next_tile = x, y + 1
            case (7, 1):
                next_tile = x, y + 1
            case (7, 3):
                next_tile = x - 1, y + 1
            case (7, 9):
                next_tile = x - 1, y
            case (6, 4):
                next_tile = x + 1, y
            case (4, 6):
                next_tile = x - 1, y
            case (3, 7):
                next_tile = x + 1, y - 1
            case (3, 9):
                next_tile = x, y - 1
            case (3, 1):
                next_tile = x + 1, y
            case (2, 8):
                next_tile = x, y - 1
            case (1, 7):
                next_tile = x, y - 1
            case (1, 9):
                next_tile = x - 1, y - 1
            case (1, 3):
                next_tile = x - 1, y
            case _:
                raise IncompatibleConnectionException("Main: %d and Other: %d do not make a compatible connection." % (main_connection, other_connection))
        return next_tile

    def determine_weight(starting_weight: float, 
                         ls: LineSegment, 
                         pattern: Tuple[int, int], 
                         north: bool) -> float:
        def modify_weight(next_tile):
            if _tile_on_outside_of_group(next_tile, group):
                weight_mod = 0.0001
            elif _tile_on_line(next_tile, lines):
                weight_mod = 0.0001
            elif _tile_near_outside_of_group(next_tile, group):
                weight_mod = 0.05
            elif _tile_near_line(next_tile, lines):
                weight_mod = 0.1
            else:
                weight_mod = 1
            return weight_mod

        # First figure out the value for the next tile....
        next_tile = get_next_tile(ls, pattern, north=north)
        starting_weight *= modify_weight(next_tile)
        
        # Then we must consider whether all subsequent tiles are ALSO bad
        # Find all next next tiles, essentially a lookahead of 1
        possible_next_next_tiles: Set[Pos] = set()
        # Check the patterns that are possible from my current tile
        # And figure out all possible next next tiles from those patterns
        for next_pattern in pattern_weights.keys():
            if north:
                if compatible(next_pattern[1], pattern[0]):
                    next_next_tile = get_next_tile(LineSegment(next_tile, pattern), next_pattern, north=north)
                    possible_next_next_tiles.add(next_next_tile)
            else:
                if compatible(pattern[1], next_pattern[0]):
                    next_next_tile = get_next_tile(LineSegment(next_tile, pattern), next_pattern, north=north)
                    possible_next_next_tiles.add(next_next_tile)
        
        # If all those possible next next tiles are also bad, we probably don't want to use this pattern
        if all(modify_weight(next_next_tile) < 1 for next_next_tile in possible_next_next_tiles):
            print("All possible next next tiles are bad for pattern (%s, %s)" % (pattern))
            starting_weight *= 0.001

        return starting_weight

    def get_south_matching_weights(ls: LineSegment) -> Dict[Tuple[int, int], int]:
        south_connection: int = ls.pattern[1]
        matching_weights = {
            pattern: determine_weight(weight, ls, pattern, north=False) 
            for pattern, weight in pattern_weights.items() 
            if compatible(south_connection, pattern[0])
        }
        return matching_weights

    def get_north_matching_weights(ls: LineSegment) -> Dict[Tuple[int, int], int]:
        north_connection: int = ls.pattern[0]
        matching_weights = {
            pattern: determine_weight(weight, ls, pattern, north=True)
            for pattern, weight in pattern_weights.items()
            if compatible(pattern[1], north_connection)
        }
        return matching_weights

    # Go south first
    current_tile = starting_tile
    current_ls = starting_ls
    while True:
        matching_weights = get_south_matching_weights(current_ls)
        counter += 1
        randomizer = WeightedRandomizer(matching_weights, base_offset + counter)
        pattern = randomizer.random()
        current_tile = get_next_tile(current_ls, pattern, north=False)
        print("South", current_ls.position, current_tile, pattern, matching_weights)
        if current_tile in group:
            current_ls = LineSegment(current_tile, pattern)
            line.append(current_ls)
        else:
            break

    # Then go north
    current_tile = starting_tile
    current_ls = starting_ls
    while True:
        matching_weights = get_north_matching_weights(current_ls)
        counter += 1
        randomizer = WeightedRandomizer(matching_weights, base_offset + counter)
        pattern = randomizer.random()
        current_tile = get_next_tile(current_ls, pattern, north=True)
        print("North", current_ls.position, current_tile, pattern, matching_weights)
        if current_tile in group:
            current_ls = LineSegment(current_tile, pattern)
            line.append(current_ls)
        else:
            break

    return line

def _position_is_between(pos: Pos, left_line: Line, right_line: Line) -> bool:
    """
    Determines if the position is between the two lines
    """
    left_boundary, right_boundary = None, None

    for line_segment in left_line:
        if line_segment.position[1] == pos[1]:
            left_boundary = line_segment.position[0]
            break
    for line_segment in right_line:
        if line_segment.position[1] == pos[1]:
            right_boundary = line_segment.position[0]
            break

    if not left_boundary:
        left_boundary = left_line.average_x()
    if not right_boundary:
        right_boundary = right_line.average_x()

    # We found the boundaries, now we determine whether we are between
    if left_boundary < pos[0] < right_boundary:
        return True
    else:
        return False

def generate_ridge_lines(group: Set[Pos]) -> Optional[Tuple[List[Line], List[Line]]]:
    """
    Returns peak lines followed by valley lines
    Returns empty, empty if group is not the right shape for ridge lines
    """
    group: List[Pos] = sorted(group)  # Sorted to preserve consistency of random seed
    peak_lines: List[Line] = []
    valley_lines: List[Line] = []

    leftmost_tile_x = min(g[0] for g in group)
    group_width = max(g[0] for g in group) - leftmost_tile_x + 1
    target_num_peak_lines = max(int(round(group_width / (MOUNTAIN_HEIGHT * 2))), 1)

    # Get starting tiles for peaks
    peak_starting_tiles: List[Pos] = []
    for i in range(target_num_peak_lines):
        # Pick the correct x
        x = round(group_width * ((i + 0.5) / target_num_peak_lines)) + leftmost_tile_x
        # Then pick a random y that's in the group
        column = [pos for pos in group if pos[0] == x]
        starting_tile = random_choice(column, (x, 0))
        peak_starting_tiles.append(starting_tile)

    # Start with peaks for finding ridge lines
    for i in range(target_num_peak_lines):
        starting_tile = peak_starting_tiles[i]
        print(starting_tile)

        line = _get_ridge_line(group, starting_tile, peak_lines, peak_start_end_pairs)
        peak_lines.append(line)
        print_grid(group, peak_lines)
        input("> ")

    # Need to sort the lines
    peak_lines = list(sorted(peak_lines, key=lambda line: line.average_x()))

    for i in range(len(peak_lines) - 1):
        # Find the group of valid tiles that make up the valley
        left_line = peak_lines[i]
        right_line = peak_lines[i + 1]
        valley_group = [pos for pos in group if _position_is_between(pos, left_line, right_line)]
        # Pick a random tile in the group, favoring tiles away from the edges
        starting_tile = _get_random_tile(valley_group)
        if not starting_tile:
            print("Could not find starting tile for valley_group: %s" % (valley_group))
            return [], []

        line = _get_ridge_line(valley_group, starting_tile, peak_lines, valley_start_end_pairs)
        valley_lines.append(line)

    return (peak_lines, valley_lines)

def print_grid(group: Iterable[Pos], lines: List[Line]):
    max_x = max(g[0] for g in group)
    max_y = max(g[1] for g in group)

    all_segments = {}
    for line in lines:
        all_segments.update({segment.position: segment for segment in line})

    # Print the column coordinates
    print("    ", end='')
    for x in range(0, max_x + 5):
        print("%02d" % (x % 10), end='')
    print("\n", end='')

    for y in range(0, max_y + 5):
        print("%02d: " % y, end='')  # Print the row coordinates
        for x in range(0, max_x + 5):
            if (x, y) not in group:
                print("0X", end='')
            elif (x, y) in all_segments:
                segment = all_segments[(x, y)]
                print(segment.get_printed_form(), end='')
            else:
                print("  ", end='')
        print("\n", end='')

if __name__ == '__main__':
    mountain_group = {(x, y) for x in range(7, 27) for y in range(4, 15)}
    peak_lines, valley_lines = generate_ridge_lines(mountain_group)
    print_grid(mountain_group, peak_lines)
    print_grid(mountain_group, peak_lines + valley_lines)
