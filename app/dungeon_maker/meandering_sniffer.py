from typing import Tuple

from app.utilities.direction import Direction
from app.utilities import static_random

class MeanderingPathSniffer:
    # Order of directions is N, E, S, W

    def __init__(self, start_pos: Tuple[int, int], goal_pos: Tuple[int, int],
                 bounds: Tuple[int, int, int, int], path_girth: int = 3,
                 seed: int = 0):
        self.rn = static_random.LCG(seed)
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.bounds = bounds
        self.path_girth = path_girth

        self.keep_out = set()
        self.path = []

        self.reset()

    def reset(self):
        self.current_position = self.start_pos
        self.current_direction = None
        self.keep_out.clear()
        self.path.clear()

    def add_to_keep_out(self, pos):
        self.keep_out.add(pos)

    def get_adj_positions(self, pos: Tuple[int, int]):
        x, y = pos
        return [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]

    def process(self):
        while self.current_position != self.goal_pos:
            adj_positions = self.get_adj_positions(self.current_position)
            utilities = [self.get_utility(adj_pos) for adj_pos in adj_positions]
            assert all(u >= 0 for u in utilities)
            idx = static_random.weighted_choice(utilities, self.rn)
            next_position = adj_positions[idx]
            # Now update to new loc
            self.current_direction = Direction.determine(self.current_position, next_position)
            self.current_position = next_position

    def get_utility(self, pos: Tuple[int, int]) -> float:
        # X points for continuing in the same direction
        # Always 0 points for going off the map or crossing over your own path or a keep out area
        # -X points for heading towards the goal_pos
        # -X points for heading towards your own path or a keep out area
        return 1
