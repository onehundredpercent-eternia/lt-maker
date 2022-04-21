import itertools
import time

from PyQt5.QtCore import QThread, pyqtSignal

from app.map_maker.utilities import get_random_seed, random_choice
from app.map_maker import rain_algorithm_x

class ArtistPatternThread(QThread):
    waiting = pyqtSignal()
    peak_height = 2

    def __init__(self, tilemap, mountain_data, group, gui_processing=True, parent=None):
        super().__init__(parent)
        # Sort from top left to bottom right
        # Break ties starting from the left
        self.tilemap = tilemap
        self.mountain_data = mountain_data  # List of patterns
        self.orig_group = group
        self.gui_processing = gui_processing

        self.organization_offset = {}
        self.organization = {}
        self.locked_values = {}
        self.order = []

        self.did_complete = False
        self.broke_out = False

        self.min_x = min(pos[0] for pos in group)
        self.max_x = max(pos[0] for pos in group)
        self.min_y = min(pos[0] for pos in group)
        self.max_y = max(pos[0] for pos in group)
        self.width = self.max_x - self.min_x + 1
        self.height = self.max_y - self.min_y + 1

        self.group = [(pos[0] - self.min_x, pos[1] - self.min_y) for pos in group]  # Offset group; (0, 0) is topright

        self.calc_width = self.width
        self.calc_height = self.height
        if self.min_x == 0:
            self.calc_width += self.width
        if self.max_x == self.tilemap.width - 1:
            self.calc_width += self.width
        if self.min_y == 0:
            self.calc_height += self.height
        if self.max_y == self.tilemap.height - 1:
            self.calc_height += self.height

    def stop(self):
        self.broke_out = True

    def clear(self):
        self.organization.clear()
        self.locked_values.clear()
        self.order.clear()

    def run(self):
        counter = 0
        while counter < 10000 and not self.broke_out:
            counter += 1
            self.clear()
            time.sleep(0.01)
            success = self.place_ridges(counter)
            if not success or self.broke_out:
                continue
            success = self.place_valleys(counter)
            if not success or self.broke_out:
                continue
            success = self.process_group()
            if not success or self.broke_out:
                continue

    def place_ridges(self, offset=0):
        self.num_ridges = self.calc_width // ((self.peak_height + 1)  * 3)
        self.num_valleys = self.num_ridges - 1
        self.num_folds = self.num_ridges + self.num_valleys
        self.ridges = []
        for i in range(self.num_folds)
            if i % 2 == 1:
                continue  # This is a valley, so skip

            x_pos = random_choice(list(range(self.calc_width)), (0, 0), offset=offset)
            y_pos = random_choice(list(range(self.calc_height)), (0, 1), offset=offset)
            starting_ridge_pos = (x_pos, y_pos)

            # while the ridge has not reached the limit of height or width in either direction
            # keep filling it up
            ridge = self.fill_fold(starting_ridge_pos, MountainCategory.RIDGE)
            if ridge:
                self.ridges.append(ridge)
            else:
                return False

        # Assert that all ridges don't overlap and don't crisscross and are never adjacent to one another
        for ridge in self.ridges:
            for other_ridge in self.ridges:
                if ridge is other_ridge:
                    continue
                if any(utils.calculate_distance(pos, other_pos) <= 1 for (pos, other_pos) in itertools.product(ridge.keys(), other_ridge.keys())):
                    return False
        return True

    def find_edge_patterns(self, pos) -> list:
        if pos in self.tilemap.tile_dict:
            north, east, south, west = self.tilemap.get_cardinal_terrain(pos)
            # Whether there is a border to the north
            north_edge = bool(north and north != 'Mountain')
            south_edge = bool(south and south != 'Mountain')
            east_edge = bool(east and east != 'Mountain')
            west_edge = bool(west and west != 'Mountain')
            valid_patterns = [pattern for pattern in self.mountain_data if pattern.edge_match(north_edge, east_edge, south_edge, west_edge)]
            return valid_patterns
        else:
            valid_patterns = [pattern for pattern in self.mountain_data if pattern.edge_match(False, False, False, False)]
            return valid_patterns

    def fill_fold(self, pos, category) -> dict:
        """
        Returns dictionary of position: pattern
        """
        fold = {}
        true_pos = (pos[0] + self.min_x, pos[1] + self.min_y)
        valid_patterns = self.find_edge_patterns(true_pos)
        curent_pattern = random_choice([pattern for pattern in valid_patterns if pattern.category == category], pos)
        fold[pos] = curent_pattern
        return fold

    def place_valleys(self, offset=0):
        self.valleys = []
        for i in range(self.num_folds)
            if i % 2 == 0:
                continue  # This is a ridge, so skip

            x_pos = random_choice(list(range(self.calc_width)), (0, 0), offset=offset)
            y_pos = random_choice(list(range(self.calc_height)), (0, 1), offset=offset)
            starting_valley_pos = (x_pos, y_pos)

            # while the valley has not reached the limit of height or width in either direction
            # keep filling it up
            valley = self.fill_fold(starting_valley_pos, MountainCategory.VALLEY)
            if valley:
                self.valleys.append(valley)
            else:
                return False

        # Assert that all valleys don't overlap and don't crisscross and are never adjacent to one another
        for valley in self.valleys:
            for other_valley in self.valleys:
                if valley is other_valley:
                    continue
                if any(utils.calculate_distance(pos, other_pos) <= 1 for (pos, other_pos) in itertools.product(valley.keys(), other_valley.keys()):
                    return False

        # place ridges and valleys
        proto_organization = {}
        for ridge in self.ridges:
            for pos, pattern in ridge.items():
                proto_organization[pos] = pattern
        for valley in self.valleys:
            for pos, pattern in valley.items():
                proto_organization[pos] = pattern

        # Assert that for each row in the bounding box, it goes ridge, valley, ridge, valley, ridge, etc.
        for row in range(self.calc_width):
            ridge_count = 0
            for col in range(self.calc_height):
                if (row, col) in proto_organization:
                    pattern = proto_organization[(row, col)]
                    if pattern.category == MountainCategory.RIDGE:
                        ridge_count += 1
                        if ridge_count > 1:
                            return False
                    elif pattern.category == MountainCategory.VALLEY:
                        ridge_count -= 1
                        if ridge_count < 0:
                            return False

        if self.min_x == 0:
            proto_organization = {(pos[0] - self.width, pos[1]): pattern for pos, pattern in proto_organization.values() if pos[0] >= self.width}
        if self.max_x == self.tilemap.width - 1:
            proto_organization = {pos: pattern for pos, pattern in proto_organization.values() if pos[0] < self.width}
        if self.min_y == 0:
            proto_organization = {(pos[0], pos[1] - self.height): pattern for pos, pattern in proto_organization.values() if pos[1] >= self.height}
        if self.max_y == self.tilemap.height - 1:
            proto_organization = {pos: pattern for pos, pattern in self.organization.values() if pos[1] < self.height}
        self.organization = {(pos[0] + self.min_x, pos[1] + self.min_y): pattern for pos, pattern in proto_organization.items()}
        return True

    def process_group(self):
        missing = self.group - self.organization.keys()
        self.to_process = sorted(missing, key=lambda x: (x[0] + x[1], x[0]))
        def process(seq, exact=True):
            pos = seq[0]
            did_work = self.find_valid_pattern(self.tilemap, pos)
            if did_work:
                try:
                    self.to_process.remove(pos)
                except ValueError:
                    pass
                self.order.append(pos)
            self.to_process = sorted(self.to_process, key=lambda x: (x[0] + x[1], x[0]))

        counter = 0
        max_counter = int(1e7)
        step_size = 500
        while self.to_process and counter < max_counter:
            counter += 1
            process(self.to_process)
            if counter % step_size == 0 and self.gui_processing:
                print("Processing %s %d..." % (id(self), counter//step_size))
                self.waiting.emit()
                time.sleep(0.01)
        # Just throw shit at the wall
        if self.to_process:
            print("Inexact solution found")
            while self.to_process:
                process(self.to_process, exact=False)
        else:
            print("Unable to find solution. Try again")
            return False
        
        if not self.broke_out:
            self.did_complete = True
            return True

    def find_valid_pattern(self, tilemap, pos, exact=True) -> bool:
        valid_patterns = self.find_edge_patterns(pos)
        orig_valid_patterns = valid_patterns[:]

        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        southwest_pos = (pos[0] - 1, pos[1] + 1)

        # print("*Valid Coord", pos, self.order)
        # print(sorted(valid_patterns))
        # Remove locked patterns
        if pos in self.locked_values and exact:
            # print("Locked", sorted(self.locked_values[pos]))
            valid_patterns = [pattern for pattern in valid_patterns if pattern not in self.locked_values[pos]]
        if not north_edge and north_pos in self.organization:
            chosen_pattern = self.organization[north_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (0, 1))]
        if not south_edge and south_pos in self.organization:
            chosen_pattern = self.organization[south_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (0, -1))]
        if not east_edge and east_pos in self.organization:
            chosen_pattern = self.organization[east_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (-1, 0))]
        if not west_edge and west_pos in self.organization:
            chosen_pattern = self.organization[west_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (1, 0))]
        # If there's already a position filled to the southwest, check that we can find a reasonable
        # choice for the 
        if southwest_pos in self.organization and south and south == 'Mountain':
            chosen_pattern = self.organization[southwest_pos]
            valid_right_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (1, 0))]
            # For the remaining valid patterns for this coordinate
            # check if any of that coordinate's southward connections match with the rightward coordinates
            # of the southwesst position
            valid_patterns = [pattern for pattern in valid_patterns if any(pattern.matches(p, (0, 1)) for p in valid_right_patterns)]

        # print(sorted(valid_patterns))
        if not valid_pattern and not exact:
            valid_patterns = orig_valid_patterns
        if not valid_patterns:
            # print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False

        valid_pattern = random_choice(valid_patterns, pos)
        # print("Final", valid_pattern)
        self.organization[pos] = valid_pattern
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            self.to_process.clear()
            return False

        pos = self.order.pop()
        pattern = self.organization[pos]
        del self.organization[pos]
        self.to_process.insert(0, pos)
        if pos not in self.locked_values:
            self.locked_values[pos] = set()
        self.locked_values[pos].add(pattern)
        # print("Locking ", pattern, "for ", pos)

class PatternBacktrackingThread(QThread):
    waiting = pyqtSignal()

    def __init__(self, tilemap, mountain_data, group, gui_processing=True, parent=None):
        super().__init__(parent)
        # Sort from top left to bottom right
        # Break ties starting from the left
        self.tilemap = tilemap
        self.mountain_data = mountain_data  # List of patterns
        self.group = group
        self.gui_processing = gui_processing

        self.to_process = sorted(self.group, key=lambda x: (x[0] + x[1], x[0]))
        self.organization = {}
        self.locked_values = {}
        self.order = []

        self.did_complete = False
        self.broke_out = False

    def stop(self):
        self.to_process.clear()
        self.broke_out = True

    def run(self):
        self.process_group()

    def process_group(self):
        print("--- Process Group ---", id(self))
        # Determine coord 
        self.organization.clear()
        self.locked_values.clear()
        self.order.clear()
        
        def process(seq, exact=True):
            pos = seq[0]
            did_work = self.find_valid_coord(self.tilemap, pos)
            if did_work:
                try:
                    self.to_process.remove(pos)
                except ValueError:
                    pass
                self.order.append(pos)
            self.to_process = sorted(self.to_process, key=lambda x: (x[0] + x[1], x[0]))

        counter = 0
        max_counter = int(1e7)
        step_size = 500
        while self.to_process and counter < max_counter:
            counter += 1
            process(self.to_process)
            if counter % step_size == 0 and self.gui_processing:
                print("Processing %s %d..." % (id(self), counter//step_size))
                self.waiting.emit()
                time.sleep(0.1)
        # Just throw shit at the wall
        if self.to_process:
            print("Inexact solution found")
            while self.to_process:
                process(self.to_process, exact=False)
        
        if not self.broke_out:
            self.did_complete = True

    def find_valid_coord(self, tilemap, pos, exact=True) -> bool:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        # Whether there is a border to the north
        north_edge = bool(north and north != 'Mountain')
        south_edge = bool(south and south != 'Mountain')
        east_edge = bool(east and east != 'Mountain')
        west_edge = bool(west and west != 'Mountain')
        valid_patterns = [pattern for pattern in self.mountain_data if pattern.edge_match(north_edge, east_edge, south_edge, west_edge)]
        orig_valid_patterns = valid_patterns[:]

        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        southwest_pos = (pos[0] - 1, pos[1] + 1)

        # print("*Valid Coord", pos, self.order)
        # print(sorted(valid_patterns))
        # Remove locked patterns
        if pos in self.locked_values and exact:
            # print("Locked", sorted(self.locked_values[pos]))
            valid_patterns = [pattern for pattern in valid_patterns if pattern not in self.locked_values[pos]]
        if not north_edge and north_pos in self.organization:
            chosen_pattern = self.organization[north_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (0, 1))]
        if not south_edge and south_pos in self.organization:
            chosen_pattern = self.organization[south_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (0, -1))]
        if not east_edge and east_pos in self.organization:
            chosen_pattern = self.organization[east_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (-1, 0))]
        if not west_edge and west_pos in self.organization:
            chosen_pattern = self.organization[west_pos]
            valid_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (1, 0))]
        # If there's already a position filled to the southwest, check that we can find a reasonable
        # choice for the 
        if southwest_pos in self.organization and south and south == 'Mountain':
            chosen_pattern = self.organization[southwest_pos]
            valid_right_patterns = [pattern for pattern in valid_patterns if chosen_pattern.matches(pattern, (1, 0))]
            # For the remaining valid patterns for this coordinate
            # check if any of that coordinate's southward connections match with the rightward coordinates
            # of the southwesst position
            valid_patterns = [pattern for pattern in valid_patterns if any(pattern.matches(p, (0, 1)) for p in valid_right_patterns)]

        # print(sorted(valid_patterns))
        if not valid_pattern and not exact:
            valid_patterns = orig_valid_patterns
        if not valid_patterns:
            # print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False

        valid_pattern = random_choice(valid_patterns, pos)
        # print("Final", valid_pattern)
        self.organization[pos] = valid_pattern
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            self.to_process.clear()
            return False

        pos = self.order.pop()
        pattern = self.organization[pos]
        del self.organization[pos]
        self.to_process.insert(0, pos)
        if pos not in self.locked_values:
            self.locked_values[pos] = set()
        self.locked_values[pos].add(pattern)
        # print("Locking ", pattern, "for ", pos)

class NaiveBacktrackingThread(QThread):
    waiting = pyqtSignal()

    def __init__(self, tilemap, mountain_data, noneless_rules, group, gui_processing=True, parent=None):
        super().__init__(parent)
        # Sort from top left to bottom right
        # Break ties starting from the left
        self.tilemap = tilemap
        self.mountain_data = mountain_data
        self.noneless_rules = noneless_rules
        self.group = group
        self.gui_processing = gui_processing

        self.to_process = sorted(self.group, key=lambda x: (x[0] + x[1], x[0]))
        self.organization = {}
        self.locked_values = {}
        self.order = []

        self.did_complete = False
        self.broke_out = False

    def stop(self):
        self.to_process.clear()
        self.broke_out = True

    def run(self):
        self.process_group()

    def process_group(self):
        print("--- Process Group ---", id(self))
        # Determine coord 
        self.organization.clear()
        self.locked_values.clear()
        self.order.clear()
        
        def process(seq, exact=True):
            pos = seq[0]
            did_work = self.find_valid_coord(self.tilemap, pos)
            if did_work:
                try:
                    self.to_process.remove(pos)
                except ValueError:
                    pass
                self.order.append(pos)
            self.to_process = sorted(self.to_process, key=lambda x: (x[0] + x[1], x[0]))

        counter = 0
        max_counter = int(1e7)
        step_size = 500
        while self.to_process and counter < max_counter:
            counter += 1
            process(self.to_process)
            if counter % step_size == 0 and self.gui_processing:
                print("Processing %s %d..." % (id(self), counter//step_size))
                self.waiting.emit()
                time.sleep(0.1)
        # Just throw shit at the wall
        if self.to_process:
            print("Inexact solution found")
            while self.to_process:
                process(self.to_process, exact=False)
        
        if not self.broke_out:
            self.did_complete = True

    def find_valid_coord(self, tilemap, pos, exact=True) -> bool:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        # Whether there is a border to the north
        north_edge = bool(north and north != 'Mountain')
        south_edge = bool(south and south != 'Mountain')
        east_edge = bool(east and east != 'Mountain')
        west_edge = bool(west and west != 'Mountain')
        valid_coords = \
            [coord for coord, mountain_group in self.mountain_data.items() if
             ((north_edge and None in mountain_group.rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in mountain_group.rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in mountain_group.rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in mountain_group.rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        orig_valid_coords = valid_coords[:]
        # If in the middle, don't include objects with index 15
        if not north_edge and not south_edge and not east_edge and not west_edge:
            valid_coords = \
                [coord for coord in valid_coords if 
                 None not in self.mountain_data[coord].rules['up'] and 
                 None not in self.mountain_data[coord].rules['down'] and 
                 None not in self.mountain_data[coord].rules['left'] and 
                 None not in self.mountain_data[coord].rules['right']]
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        southwest_pos = (pos[0] - 1, pos[1] + 1)
        # print("*Valid Coord", pos, self.order)
        # print(sorted(valid_coords))
        # Remove locked coords
        if pos in self.locked_values and exact:
            # print("Locked", sorted(self.locked_values[pos]))
            valid_coords = [coord for coord in valid_coords if coord not in self.locked_values[pos]]
        if not north_edge and north_pos in self.organization:
            chosen_coord = self.organization[north_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord].rules['down']]
        if not south_edge and south_pos in self.organization:
            chosen_coord = self.organization[south_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord].rules['up']]
        if not east_edge and east_pos in self.organization:
            chosen_coord = self.organization[east_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord].rules['left']]
        if not west_edge and west_pos in self.organization:
            chosen_coord = self.organization[west_pos]
            valid_coords = [coord for coord in valid_coords if coord in self.mountain_data[chosen_coord].rules['right']]
        # If there's already a position filled to the southwest, check that we can find a reasonable
        # choice for the 
        if southwest_pos in self.organization and south and south == 'Mountain':
            chosen_coord = self.organization[southwest_pos]
            valid_right_coords = self.noneless_rules[chosen_coord]['right']
            # For the remaining valid coords for this coordinate
            # check if any of that coordinate's southward connections match with the rightward coordinates
            # of the southwesst position
            valid_coords = [coord for coord in valid_coords if any(c in valid_right_coords for c in self.noneless_rules[coord]['down'])]

        # print(sorted(valid_coords))
        if not valid_coords and not exact:
            valid_coords = orig_valid_coords
        if not valid_coords:
            # print("Reverting Order...")
            if pos in self.locked_values:
                del self.locked_values[pos]
            self.revert_order()
            # valid_coords = self.index_dict[15]
            return False

        # Weight the valid coord list by the likelihood that it's partners use it
        valid_coord_list = []
        for valid_coord in valid_coords:
            if west_pos in self.organization:
                west_coord = self.organization[west_pos]
                partners = self.mountain_data[west_coord].rules['right']
                if valid_coord in partners:
                    count = partners[valid_coord]
                    valid_coord_list += [valid_coord] * count
            if north_pos in self.organization:
                north_coord = self.organization[north_pos]
                partners = self.mountain_data[north_coord].rules['down']
                if valid_coord in partners:
                    count = partners[valid_coord]
                    valid_coord_list += [valid_coord] * count
            if south and south == 'Mountain':
                count = sum(self.noneless_rules[valid_coord]['down'].values())
                valid_coord_list += [valid_coord] * count
            if east and east == 'Mountain':
                count = sum(self.noneless_rules[valid_coord]['right'].values())
                valid_coord_list += [valid_coord] * count
        if not valid_coord_list:
            valid_coord_list = valid_coords
        valid_coord = random_choice(valid_coord_list, pos)
        # print("Final", valid_coord)
        self.organization[pos] = valid_coord
        return True

    def revert_order(self):
        if not self.order:
            print("Major loop error! No valid solution")
            self.to_process.clear()
            return False

        pos = self.order.pop()
        coord = self.organization[pos]
        del self.organization[pos]
        self.to_process.insert(0, pos)
        if pos not in self.locked_values:
            self.locked_values[pos] = set()
        self.locked_values[pos].add(coord)
        # print("Locking ", coord, "for ", pos)

class AlgorithmXThread(QThread):
    waiting = pyqtSignal()

    def __init__(self, tilemap, mountain_data, noneless_rules, group, gui_processing=True, parent=None):
        super().__init__(parent)
        # Sort from top left to bottom right
        # Break ties starting from the left
        self.tilemap = tilemap
        self.mountain_data = mountain_data
        self.noneless_rules = noneless_rules
        self.group = group
        self.gui_processing = gui_processing

        self.to_process = sorted(self.group, key=lambda x: (x[0] + x[1], x[0]))
        self.organization = {}

        self.did_complete = False
        self.broke_out = False

    def stop(self):
        self.to_process.clear()
        self.broke_out = True

    def run(self):
        self.process_group()

    def process_group(self):
        if not self.to_process:
            print("No positions to process!")
            return

        columns = [(pos, True) for pos in self.to_process]
        # valid_coords = [self.find_valid_coords(pos) for pos in self.to_process]
        valid_coords_dict = {pos: self.find_valid_coords(pos) for pos in self.to_process}

        time.sleep(0.001)
        if self.broke_out:
            return

        rows = []
        row_names = []
        column_names = [pos for pos in self.to_process]

        for idx, pos in enumerate(self.to_process):
            time.sleep(0.001)
            if self.broke_out:
                return
            right = (pos[0] + 1, pos[1])
            down = (pos[0], pos[1] + 1)
            for valid_coord in valid_coords_dict[pos]:
                row = [idx]
                rows.append(row)
                row_names.append((pos, valid_coord))

                # Right
                if right in valid_coords_dict:
                    invalid_coords_right = {coord for coord in valid_coords_dict[right] if coord not in self.mountain_data[valid_coord].rules['right']}
                    if invalid_coords_right:
                        identifier = (pos, right, valid_coord, invalid_coords_right)
                        column_names.append(identifier)
                        columns.append((identifier, False))
                        row.append(len(columns) - 1)

                # Down
                if down in valid_coords_dict:
                    invalid_coords_down = {coord for coord in valid_coords_dict[down] if coord not in self.mountain_data[valid_coord].rules['down']}
                    if invalid_coords_down:
                        identifier = (pos, down, valid_coord, invalid_coords_down)
                        column_names.append(identifier)
                        columns.append((identifier, False))
                        row.append(len(columns) - 1)

        time.sleep(0.001)
        if self.broke_out:
            return

        # Now we have each column and row, the primary columns are completely filled
        # the secondary columns are halfway filled. They need their other sections to 
        # be filled to completion
        assert len(row_names) == len(rows)
        column_idxs_to_be_filled = range(len(self.to_process), len(columns))
        for cidx in column_idxs_to_be_filled:
            pos, partner_pos, valid_coord, invalid_coords = column_names[cidx]
            for ridx, row_name in enumerate(row_names):
                # Find the rows that apply to this partner pos and are in the set of invalid coords
                if partner_pos == row_name[0] and row_name[1] in invalid_coords:
                    # Add a 1 here
                    rows[ridx].append(cidx)

        time.sleep(0.001)
        if self.broke_out:
            return

        print("Setup 1 complete", id(self), len(rows), len(columns))
        solver = rain_algorithm_x.RainAlgorithmX(columns, row_names, rows, self.to_process[0], get_random_seed())
        print("Setup 2 complete", id(self))

        time.sleep(0.001)
        if self.broke_out:
            return

        # Now solve
        counter = 0
        limit = int(1e6)
        while counter < limit:
            time.sleep(0)
            if counter % 10000 == 0:
                print("Still Processing", id(self), counter)
            if self.broke_out:
                return
            counter += 1
            output = solver.subsolve()
            if output is True:
                for pos, coord in solver.get_solution():
                    self.organization[pos] = coord
                if not self.broke_out:
                    self.did_complete = True
                return True
            elif output is False:
                print("No valid solution!")
                return False  # No valid solutions
        if counter >= limit:
            print("Infinite Loop detected!")
        return True

    def find_valid_coords(self, pos) -> list:
        north, east, south, west = self.get_cardinal_terrain(pos)
        north_edge = not north
        south_edge = not south
        east_edge = not east
        west_edge = not west
        valid_coords = \
            [coord for coord, mountain_group in self.mountain_data.items() if
             ((north_edge and None in mountain_group.rules['up']) or (not north_edge and self.noneless_rules[coord]['up'])) and
             ((south_edge and None in mountain_group.rules['down']) or (not south_edge and self.noneless_rules[coord]['down'])) and
             ((east_edge and None in mountain_group.rules['right']) or (not east_edge and self.noneless_rules[coord]['right'])) and
             ((west_edge and None in mountain_group.rules['left']) or (not west_edge and self.noneless_rules[coord]['left']))]
        # If in the middle, don't include objects with index 15
        orig_valid_coords = valid_coords[:]
        if not north_edge and not south_edge and not east_edge and not west_edge:
            valid_coords = \
                [coord for coord in valid_coords if 
                 None not in self.mountain_data[coord].rules['up'] and 
                 None not in self.mountain_data[coord].rules['down'] and 
                 None not in self.mountain_data[coord].rules['left'] and 
                 None not in self.mountain_data[coord].rules['right']]
        if not valid_coords:
            valid_coords = orig_valid_coords
        return valid_coords

    def get_cardinal_terrain(self, pos: tuple) -> tuple:
        north = pos[1] == 0 or self.get_terrain((pos[0], pos[1] - 1))
        east = pos[0] + 1 == self.tilemap.width or self.get_terrain((pos[0] + 1, pos[1]))
        south = pos[1] + 1 == self.tilemap.height or self.get_terrain((pos[0], pos[1] + 1))
        west = pos[0] == 0 or self.get_terrain((pos[0] - 1, pos[1]))
        return north, east, south, west

    def get_terrain(self, pos: tuple) -> bool:
        return pos in self.to_process
