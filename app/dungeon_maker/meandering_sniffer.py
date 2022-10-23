from typing import Tuple

from app.utilities.direction import Direction
from app.utilities import static_random, utils

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
        self.path.append(self.current_position)

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
            self.path.append(self.current_position)
        return self.path

    def get_utility(self, pos: Tuple[int, int]) -> float:
        utility = 5
        # 5 points for continuing in the same direction
        direc = Direction.determine(self.current_position, pos)
        if direc == self.current_direction:
            utility += 10

        # Always 0 points for going off the map
        if 0 <= pos[0] < self.bounds[2] and 0 <= pos[1] < self.bounds[3]:
            pass
        else:
            return 0

        # 0 points for crossing over your own path or a keep out area
        if pos in self.path:
            return 0
        elif pos in self.keep_out:
            return 0
        
        # -X points for heading towards the goal_pos
        goal_distance = utils.calculate_distance(self.goal_pos, pos)
        utility -= abs(self.path_girth * 2 - goal_distance)
        # -X points for heading towards your own path or a keep out area
        closest_distance = 100
        for opos in self.path + self.keep_out:
            distance = utils.calculate_distance(opos, pos)
            if distance < closest_distance:
                closest_distance = distance
        utility -= abs(self.path_girth - closest_distance)

        return max(0, utility)
