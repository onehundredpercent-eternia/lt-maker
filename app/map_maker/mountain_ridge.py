from typing import List, Dict, Tuple, Set

from app.map_maker.mountain_patterns import MountainCategory

class MountainGroup():
    peak_height = 2

    def __init__(self, positions, mountain_patterns):
        offset_x = min(pos[0] for pos in self.tiles)
        offset_y = min(pos[1] for pos in self.tiles)
        self.tiles: Set[Tuple] = set((pos[0] - offset_x, pos[1] - offset_y) for pos in positions)
        # Now the tiles are set so (0, 0) is the topleft of the bounding box
        self.width = max(pos[0] for pos in self.tiles) + 1
        self.height = max(pos[1] for pos in self.tiles) + 1

        self.mountain_patterns = mountain_patterns

        self.ridges: List[Ridge] = []
        self.valleys: List[Valley] = [] 

        self.top_edges: Set[Tuple] = set()
        self.bottom_edges: Set[Tuple] = set()
        self.left_edges: Set[Tuple] = set()
        self.right_edges: Set[Tuple] = set()

        self.edge_pairs_v = []
        self.edge_pairs_h = []

        self.find_edges()
        self.pair_edges()

        self.place_ridges()

    def find_edges(self):
        for pos in self.tiles:
            if (pos[0] - 1, pos[1]) not in self.tiles:
                self.left_edges.add(pos)
            if (pos[0] + 1, pos[1]) not in self.tiles:
                self.right_edges.add(pos)
            if (pos[0], pos[1] - 1) not in self.tiles:
                self.top_edges.add(pos)
            if (pos[0], pos[1] + 1) not in self.tiles:
                self.bottom_edges.add(pos)

    def pair_edges(self):
        # Top to bottom first
        for top_pos in self.top_edges:
            # Find the closest bottom edge along the same column
            valid_positions = [bottom_pos for bottom_pos in self.bottom_edges if bottom_pos[0] == top_pos[0] and bottom_pos[1] >= top_pos[1]]
            bottom_pos = list(sorted(valid_positions))[0]
            self.edge_pairs_v.append((top_pos, bottom_pos))
        # Now left to right
        for left_pos in self.left_edges:
            # Find the closest right edge along the same row
            valid_positions = [right_pos for right_pos in self.right_edges if right_pos[1] == left_pos[1] and right_pos[0] >= left_pos[0]]
            right_pos = list(sorted(valid_positions))[0]
            self.edge_pairs_h.append((left_pos, right_pos))

    def place_ridges(self):
        num_ridges = max(1, int(self.width / (self.peak_height * 2)))
        num_valleys = num_ridges - 1
        num_creases = num_ridges + num_valleys
        avg_peak_height = self.width / (num_creases + 1)

        ridge_start_positions = [i * avg_peak_height + (i - 1) * avg_peak_height for i in range(1, num_ridges + 1)]
        valley_start_positions = [i * avg_peak_height * 2 for i in range(1, num_valleys + 1)]

        # Keep trying until we get one right
        counter = 0
        while counter < 10000:

            # Place ridge chains
            ridge_chains: List[Ridge] = []
            for ridge_start in ridge_start_positions:
                ridge = Ridge()
                pos = (int(ridge_start), 0)
                # Pick a valid pattern for this position
                pattern = self.get_valid_starting_pattern(pos, mountain_category.RIDGE)
                # Place it in the ridge
                ridge.add(pos, pattern)
                # Repeat until we reach the bottom of the bounding box
                while pos[1] < self.height - 1:
                    current_pos = ridge.chain[-1]
                    current_pattern = ridge.placement[current_pos]
                    pos, pattern = self.get_next_pattern(current_pos, current_pattern, mountain_category.RIDGE)
                    ridge.add(pos, pattern)
                ridge_chains.append(ridge)


            valley_chains: List[Valley] = []
            for valley_start in valley_start_positions:
                valley = Valley()
                pos = (int(valley_start), 0)
                # Pick a valid pattern for this position
                pattern = self.get_valid_starting_pattern(pos, mountain_category.VALLEY)
                # Place it in the valley
                valley.add(pos, pattern)
                # Repeat until we reach the bottom of the bounding box
                while pos[1] < self.height - 1:
                    current_pos = valley.chain[-1]
                    current_pattern = valley.placement[current_pos]
                    pos, pattern = self.get_next_pattern(current_pos, current_pattern, mountain_category.VALLEY)
                    valley.add(pos, pattern)
                valley_chains.append(valley)

            # Now check the results
            # Need to assert none of the tiles overlap or lines cross
            tile_frequency = Counter()
            for ridge in ridge_chains:
                for position in ridge,chain:
                    tile_frequency[position] += 1
            for valley in valley_chains:
                for position in valley.chain:
                    tile_frequency[position] += 1
            if any(count > 1 for pos, count in tile_frequency.items()):
                counter += 1
                break
            # Need to assert that where edges are concerned, there is a valid match (not necessary, done above?)
            # Ridges at least X/2 distance away from valleys (where X is self.peak_height?)
            # No tile is more than 1.5X distance away from ridge
            # If all these assertions are met, we have a valid match
            # Assign to self.ridges and self.valleys
            # Can now proceed to find correct coordinates for the non-crease tiles
            



class Ridge():
    def __init__(self):
        self.placement: Dict[Tuple, MountainPattern] = {}
        self.chain: List[Tuple] = []

    def add(self, pos, pattern):
        self.placement[pos] = pattern
        self.chain.append(pos)

class Valley(Ridge):
    pass

