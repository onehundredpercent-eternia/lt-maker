import math

from typing import List, Dict, Tuple, Set

from app.map_maker.mountain_patterns import MountainCategory, MountainPattern
from app.map_maker.utilities import random_weighted_choice

class MountainGroup():
    peak_height = 2

    def __init__(self, positions, mountain_patterns):
        offset_x = min(pos[0] for pos in self.tiles)
        offset_y = min(pos[1] for pos in self.tiles)
        self.tiles: Set[Tuple] = set((pos[0] - offset_x, pos[1] - offset_y) for pos in positions)
        # Now the tiles are set so (0, 0) is the topleft of the bounding box
        self.width = max(pos[0] for pos in self.tiles) + 1
        self.height = max(pos[1] for pos in self.tiles) + 1

        self.mountain_patterns: Dict[Tuple, MountainPattern] = mountain_patterns

        self.top_edges: Set[Tuple] = set()
        self.bottom_edges: Set[Tuple] = set()
        self.left_edges: Set[Tuple] = set()
        self.right_edges: Set[Tuple] = set()

        self.find_edges()
        self.edge_indices = {pos: MountainPattern.calculate_edge_index(left=pos in self.left_edges, right=pos in self.right_edges, top=pos in self.top_edges, bottom=pos in self.bottom_edges) for pos in self.tiles}

        output = False
        counter = 0
        while not output and counter < 10000:
            output = self.place_ridges_wavefunction_collapse()
            counter += 1
        # Now organization exists
        if counter >= 10000:
            print("Wow this broke, infinite loop")

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

    def shannon_entropy(self, possibilities) -> float:
        total = 0
        for possibility, chance in possibilities:
            total += chance * math.log2(1 / chance)
        return total

    def get_minimum_shannon(self, possibility_space):
        best_pos = None
        min_shannon = 9e99
        for pos, possibilities in possibility_space.items():
            if len(possibilities) < 2:
                continue  # Don't bother with single possibility
            entropy = self.shannon_entropy(possibilities)
            if entropy < min_shannon:
                min_shannon = entropy
                best_pos = pos
        return pos, possibility_space[pos]

    def place_ridges_wavefunction_collapse(self, random_offset=0):
        self.possibility_space = \
            {pos: set()} for pos in self.tiles}
        for pos in self.tiles:
            categories = [MountainCategory.LIGHT, MountainCategory.DARK, MountainCategory.RIDGE, MountainCategory.VALLEY]
            default_likelihood = [1, 1, 1 / (self.peak_height + 1), 1 / (self.peak_height + 1)]
            for category, likelihood in zip(categories, default_likelihood):
                if any(pattern.category == category and pattern.edge_index == self.edge_indices[pos] in self.mountain_patterns.values()):
                    self.possibility_space[pos].add((category, likelihood))

        assert all(len(v) >= 1 for v in self.possibility_space.values())

        while any(len(possibilities) > 1 for possibilities in self.possibility_space):
            current_pos, possibilities = self.get_minimum_shannon(self.possibility_space)
            # Choose from among the possibilities randomly
            choice = random_weighted_choice(possibilities, current_pos, offset=random_offset)
            self.possibility_space[current_pos] = {(choice, 1)}

            # Now remove other possibilities from the possibility space
            if choice == MountainCategory.LIGHT:
                # If Light, then 4-adjacent tiles can't be dark
                for pos in self.get_adjacent_4_tiles(current_pos):
                    self.possibility_space[pos].discard(MountainCategory.DARK)
            elif choice == MountainCategory.DARK:
                # if dark, then 4-adjacent tiles can't be light
                for pos in self.get_adjacent_4_tiles(current_pos):
                    self.possibility_space[pos].discard(MountainCategory.LIGHT)
            elif choice == MountainCategory.RIDGE:
                # if ridge, then 4-adjacent tiles can't be valley
                for pos in self.get_adjacent_4_tiles(current_pos):
                    self.possibility_space[pos].discard(MountainCategory.VALLEY)
                # left tile must be either ridge or light (ie, left tile cannot be dark)
                if (pos[0] - 1, pos[1]) in self.tiles:
                    self.possibility_space[pos].discard(MountainCategory.DARK)
                # right tile must be either ridge or dark (ie, right tile cannot be light)
                if (pos[0] + 1, pos[1]) in self.tiles:
                    self.possibility_space[pos].discard(MountainCategory.LIGHT)
                # If has top and bottom edge, then pass
                # If has top or bottom edge, must have at least 1 8-adjacent ridge
                # If has left or right edge or no edge at all, must have at least 2 8-adjacent ridges
            elif choice == MountainCategory.VALLEY:
                # if valley, then 4-adjacent tiles can't be right
                for pos in self.get_adjacent_4_tiles(current_pos):
                    self.possibility_space[pos].discard(MountainCategory.RIDGE)
                # left tile must be dark (ie, left tile cannot be light or valley)
                if (pos[0] - 1, pos[1]) in self.tiles:
                    self.possibility_space[pos].discard(MountainCategory.LIGHT)
                    self.possibility_space[pos].discard(MountainCategory.VALLEY)
                # right tile must be light (ie, right tile cannot be dark or valley)
                if (pos[0] + 1, pos[1]) in self.tiles:
                    self.possibility_space[pos].discard(MountainCategory.DARK)
                    self.possibility_space[pos].discard(MountainCategory.VALLEY)
                # If has top and bottom edge, then pass
                # If has top or bottom edge, must have at least 1 8-adjacent ridge
                # If has left or right edge or no edge at all, must have at least 2 8-adjacent ridges

            assert all(len(v) >= 1 for v in self.possibility_space.values())

        self.final_patterns = {pos: possibility[0] for pos, possibility in self.possibility_space.items()}
        # Now given all the pattern, assign a coordinate to each one

        self.organization = {}
        for pos, category in self.final_patterns.items():
            valid_patterns = [pattern for pattern in self.mountain_patterns.values() if pattern.category == category and pattern.edge_index == self.edge_indices[pos]]
            if category == MountainCategory.RIDGE:
                for adj_pos in self.find_adjacent(pos, MountainCategory.RIDGE):
                    if adj_pos in self.organization:
                        adj_coord = self.organization[adj_pos]
                        valid_patterns = [pattern for pattern in valid_patterns if pattern.can_match(self.mountain_patterns[adj_coord])]
            if category == MountainCategory.VALLEY:
                for adj_pos in self.find_adjacent(pos, MountainCategory.VALLEY):
                    if adj_pos in self.organization:
                        adj_coord = self.organization[adj_pos]
                        valid_patterns = [pattern for pattern in valid_patterns if pattern.can_match(self.mountain_patterns[adj_coord])]
            if valid_patterns:
                pattern = random_choice(valid_patterns, pos, offset=offset)
                self.organization[pos] = pattern.coord
            else:
                return False
        return True
