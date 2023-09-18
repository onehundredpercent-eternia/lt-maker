import random
import itertools
from typing import Tuple, List

from app.utilities import utils

class MeanderingPathCreator:
    def __init__(self, start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                 bounds: Tuple[int, int, int, int], path_girth: int = 3,
                 seed: int = 0):
        self.rn = random.Random(seed)
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.bounds = bounds
        self.path_girth = path_girth
        self.num_positions = 6

        self.keep_out = set()
        self.path = []

    def add_to_keep_out(self, pos):
        self.keep_out.add(pos)

    def get_adj_positions(self, pos: Tuple[int, int]):
        x, y = pos
        return [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]

    def draw_line(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> List[Tuple[int, int]]:
        assert pos1[0] == pos2[0] or pos1[1] == pos2[1]
        if pos1[0] == pos2[0]:
            if pos1[1] < pos2[1]:
                return [(pos1[0], y) for y in range(pos1[1], pos2[1])]
            else:
                return [(pos1[0], y) for y in range(pos1[1], pos2[1], -1)]
        elif pos1[1] == pos2[1]:
            if pos1[0] < pos2[0]:
                return [(x, pos1[1]) for x in range(pos1[0], pos2[0])]
            else:
                return [(x, pos1[1]) for x in range(pos1[0], pos2[0], -1)]

    def process(self):
        # Choose X number of random positions that are more than 
        # path_girth from start_pos, goal_pos, existing positions, and keep_out zones
        positions = set()
        bad_positions = self.keep_out | {self.start_pos, self.goal_pos}
        width, height = self.bounds[2], self.bounds[3]
        while len(positions) < self.num_positions:
            valid_positions = [(x, y) for x in range(width) for y in range(height)]
            valid_positions = [pos for pos in valid_positions if all(utils.calculate_distance(pos, opos) > self.path_girth for opos in bad_positions)]
            pos = self.rn.choice(valid_positions)
            positions.add(pos)
        # Find the shorted path between all positions, traveling salesman style
        perms = [[self.start_pos] + list(perm) + [self.goal_pos] for perm in itertools.permutations(positions)]
        minimum_distance = 1000
        best_permutation = None
        for perm in perms:
            distance = 0
            for a, b in zip(perm[:-1], perm[1:]):
                distance += utils.calculate_distance(a, b)
            if distance < minimum_distance:
                minimum_distance = distance
                best_permutation = perm

        points = best_permutation
        path = []
        for a, b in zip(points[:-1], points[1:]):
            if a[0] == b[0]:
                path += self.draw_line(a, b)
            elif a[1] == b[1]:
                path += self.draw_line(a, b)
            else:
                corners = [(a[0], b[1]), (b[0], a[1])]
                corner = self.rn.choice(corners)
                line1 = self.draw_line(a, corner)
                line2 = self.draw_line(corner, b)

                # Try using the other corner to see if we don't overlap
                if set(line1) & set(path) or set(line2) & set(path):
                    other_corner = corners[0] if corner == corners[1] else corners[1]
                    line1 = self.draw_line(a, other_corner)
                    line2 = self.draw_line(other_corner, b)

                path += line1
                path += line2
        path.append(self.goal_pos)
        return path

# To test, run "python -m app.dungeon_maker.meandering_path_creator"
if __name__ == '__main__':
    width, height = 20, 20
    pathfinder = MeanderingPathCreator(
        (0, 0), (width - 1, height - 1), (0, 0, width, height))
    path = pathfinder.process()
    print(path)
    for y in range(height):
        print("%02d  " % y, end='')
        for x in range(width):
            if (x, y) in path:
                idx = path.index((x, y))
                print('%01d' % (idx % 10), end='')
            else:
                print(' ', end='')
        print('\n', end='')
