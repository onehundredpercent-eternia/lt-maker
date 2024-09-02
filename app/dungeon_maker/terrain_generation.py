"""
# References:
https://pokemon-dungeoneer.vercel.app/
https://github.com/EpicYoshiMaster/dungeon-mystery
https://www.youtube.com/watch?v=fudOO713qYo

Types of terrain:
Walls
Upper floor
Lower floor
Stairs
Pillars/Forest

Generation algorithm:
1. Create a big old field of walls
2. Divide walls into grid (3x3, 2x3, 5x2, etc.)
3. In each subgrid, create a room, hallway anchor, or blank
    3.2. Randomly determine size (XxY) if room
    3.3. Randomly determine position in subgrid if room or hallway anchor
    3.4. N% chance to merge adjacent rooms together
    3.5. M% chance to carve sections of the room off or add a section to it
4. Connect rooms together with hallways
    4.1 Adjacent grids with rooms, randomly select a hallway size (1, 2, or 3)
    4.2 Select an anchor point on each wall randomly
    4.3 If not perfect, on grid line is able to turn to match up
5. (Optional) Generate extra hallways
6. (Optional) Repeat with lower floor of rooms
7. Randomly generate starting point in room, put staircase up there.
8. Randomly generate ending point in room, put staircase down there.

Encounter generation:
1. For each room, choose an encounter from the encounter list
2. Place appropriate enemies in each room
"""

# Figure out how to make hallways the right size for the room
# Figure out where the draw the stairways and sections

from __future__ import annotations
from enum import Enum
import random
from typing import Dict, List, Optional, Set, Tuple

from app.utilities import utils
from app.utilities.typing import Pos
from app.utilities.direction import Direction, get_cardinal_positions, get_diagonal_positions
from app.dungeon_maker.utilities import set_random_seed, flood_fill
from app.dungeon_maker.themes import Theme, themes
from app.dungeon_maker.terrain import Terrain

class FloorLevel(Enum):
    LOWER = 1
    UPPER = 2

def generate_terrain(theme: str, seed=-1) -> DungeonTileMap:
    random.seed(seed)
    set_random_seed(seed)
    theme = themes.get(theme)  # Convert str to Theme

    while True:
        result = _generate_terrain_process(theme)
        if result:
            break

    return result

def _generate_terrain_process(theme: Theme) -> Optional[DungeonTileMap]:
    tilemap = DungeonTileMap(theme)
    tilemap.reset_grid(Terrain.WALL_TOP)

    num_rooms = tilemap.generate_rooms()
    if num_rooms < 2:  # Need at least 2 rooms
        return
    tilemap.print_sections()
    tilemap.connect_rooms()

    tilemap.coerce_terrain()
    # All floor tiles must be reachable
    if not tilemap.is_fully_connected():
        return

    tilemap.make_walls_two_high()

    if theme.use_forest:
        tilemap.add_forest()
    else:
        tilemap.add_pillars()

    tilemap.generate_start_and_end()

    tilemap.wrap_in_walls()
    tilemap.fill_in_crevices()
    tilemap.split_walls()
    tilemap.crop_void()
    # All floor tiles must be reachable
    if not tilemap.is_fully_connected():
        return

    tilemap.print_terrain_grid()

    return tilemap

class DungeonTileMap:
    def __init__(self, theme: Theme):
        self.theme = theme
        self.width, self.height = theme.size
        self.terrain_grid: Dict[Pos, Terrain] = {}
        self.start: Pos = None
        self.end: Pos = None
        self.grid_size: Tuple[int, int] = theme.section_grid
        self.sections: Dict[Pos, DungeonSection] = {}
        self.set_sections()

    def get_terrain(self, pos: Pos) -> Optional[Terrain]:
        return self.terrain_grid.get(pos, None)

    def swap_terrain(self, terrain1: Terrain, terrain2: Terrain):
        """
        Converts all tiles with terrain of type terrain1 to 
        terrain of type terrain2
        """
        swap_to = set()
        for pos, terrain in self.terrain_grid.items():
            if terrain == terrain1:
                swap_to.add(pos)
        for pos in swap_to:
            self.terrain_grid[pos] = terrain2

    def check_bounds(self, pos: Pos) -> bool:
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def reset_grid(self, terrain: Terrain):
        for x in range(self.width):
            for y in range(self.height):
                self.terrain_grid[(x, y)] = terrain

    def is_fully_connected(self) -> bool:
        floor_terrain = Terrain.floor_terrain()
        floor_tiles = {pos for pos, terrain in self.terrain_grid.items() 
                       if terrain in floor_terrain}
        test_pos = floor_tiles.pop()
        can_reach = flood_fill(self, test_pos, match=floor_terrain)
        floor_tiles -= can_reach
        if floor_tiles:
            self.print_terrain_grid()
            # There are some tiles that haven't been reached
            print("Could not find these tiles:", sorted(floor_tiles))
            print(sorted(can_reach))
            return False
        return True

    def set_sections(self):
        x, y = self.grid_size
        xwidth = self.width / x
        ywidth = self.height / y 
        for xi in range(x):
            for yi in range(y):
                offset = (int(xi * xwidth), int(yi * ywidth))
                self.sections[(xi, yi)] = \
                    DungeonSection((int(xwidth), int(ywidth)), offset, self)

    def generate_rooms(self) -> int:
        """
        Returns the number of rooms generated
        """
        full_rooms_generated = 0
        for section in self.sections.values():
            val = random.random()
            if val < self.theme.room_chance:
                section.generate_room()
                full_rooms_generated += 1
            elif val < self.theme.room_chance + self.theme.hallway_chance:
                section.generate_hallway_node()
            else:
                pass
        return full_rooms_generated

    def connect_rooms(self):
        complete: Set[Tuple[Pos, Pos]] = set()
        coords = sorted(self.sections.keys())
        for coord in coords:
            section = self.sections.get(coord)
            if not section.room:
                # Skip empty rooms
                continue
            x, y = coord
            # Only need to support these two directions
            directions = [
                # ((x - 1, y), Direction.WEST), 
                ((x + 1, y), Direction.EAST),
                # ((x, y - 1), Direction.NORTH),
                ((x, y + 1), Direction.SOUTH),
            ]
            for adj, direction in directions:
                # Don't do it twice
                if (coord, adj) in complete or (adj, coord) in complete:
                    continue
                adj_section = self.sections.get(adj)
                if adj_section and adj_section.room:
                    section.connect(adj_section, direction)
                    complete.add((coord, adj))
                    self.print_sections()

    def generate_start_and_end(self):
        available_sections = [
            (pos, section.room) for pos, section in self.sections.items() 
            if section.has_big_room()
        ]
        start_pos, start_room = random.choice(available_sections)
        furthest_away_section = \
            list(sorted(available_sections, 
                        key=lambda section: utils.calculate_distance(start_pos, section[0])
                        )
                 )[-1]
        end_pos, end_room = furthest_away_section
        # Choose a random position in the room
        valid_start_positions = [pos for pos in start_room.get_true_inner_positions() 
                                 if self.terrain_grid.get(pos) in (Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER)]
        valid_end_positions = [pos for pos in end_room.get_true_inner_positions() 
                               if self.terrain_grid.get(pos) in (Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER)]
        self.start = random.choice(valid_start_positions)
        self.end = random.choice(valid_end_positions)

        # Set the terrain for the start and end
        if self.start:
            self.terrain_grid[self.start] = Terrain.START
        if self.end:
            self.terrain_grid[self.end] = Terrain.END

    def coerce_terrain(self):
        for section_pos, section in self.sections.items():
            # Fill all rooms
            if section.room:
                # If the room should be upper
                # Only time this would work is if the room is not a full room (just a hallway node)
                # AND none of it's adjacent rooms are UPPER rooms
                if section.room.floor_level == FloorLevel.UPPER \
                        and (section.has_full_room() 
                             or any(adj.room.floor_level == FloorLevel.UPPER for adj in self._get_adj_sections(section_pos))):
                    terrain = Terrain.FLOOR_UPPER  
                else:
                    terrain = Terrain.FLOOR_LOWER
                for pos in section.room.get_true_positions():
                    self.terrain_grid[pos] = terrain
            # Fill all hallways
            for direction, hallway in section.hallways.items():
                other_section = self._get_section_in_direction(section_pos, direction)
                if section.room.floor_level == FloorLevel.UPPER and other_section \
                        and other_section.room and other_section.room.floor_level == FloorLevel.UPPER:
                    terrain = Terrain.FLOOR_UPPER
                else:
                    terrain = Terrain.FLOOR_LOWER
                for pos in hallway:
                    self.terrain_grid[pos] = terrain

        # Make sure stairs won't go straight into a wall
        while True:
            walls = (Terrain.WALL_TOP, Terrain.WALL_BOTTOM)
            to_fix = set()
            for pos, terrain in self.terrain_grid.items():
                if terrain != Terrain.FLOOR_LOWER:
                    continue
                north, east, south, west = self.get_cardinal_terrain(pos)
                ne, se, sw, nw = self.get_diagonal_terrain(pos)
                if east == Terrain.FLOOR_UPPER and west in walls:
                    to_fix.add(pos)
                elif west == Terrain.FLOOR_UPPER and east in walls:
                    to_fix.add(pos)
                elif north == Terrain.FLOOR_UPPER and south in walls:
                    to_fix.add(pos)
                elif south == Terrain.FLOOR_UPPER and north in walls:
                    to_fix.add(pos)
                # Prevent building a wall above stairs that would result in a hallway being blocked
                elif west == Terrain.FLOOR_UPPER and east == Terrain.FLOOR_LOWER \
                        and north == Terrain.FLOOR_LOWER and ne in walls and nw in walls:
                    to_fix.add(pos)
                elif east == Terrain.FLOOR_UPPER and west == Terrain.FLOOR_LOWER \
                        and north == Terrain.FLOOR_LOWER and ne in walls and nw in walls:
                    to_fix.add(pos)
            for pos in to_fix:
                self.terrain_grid[pos] = Terrain.FLOOR_UPPER
            if not to_fix:
                break
            to_fix.clear()

        # Flood fill to find small areas of floor surrounded by areas of other kind and switch them
        floor_tiles = {pos for pos, terrain in self.terrain_grid.items() 
                       if terrain in (Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER)}
        while floor_tiles:
            test_pos = floor_tiles.pop()
            swap_to = Terrain.FLOOR_LOWER if self.terrain_grid.get(test_pos) == Terrain.FLOOR_UPPER else Terrain.FLOOR_UPPER
            friends = flood_fill(self, test_pos)
            if len(friends) <= self.theme.small_floor_section_size:  # Very conservative
                # Section is too small, swap to other side
                for pos in friends:
                    self.terrain_grid[pos] = swap_to
            floor_tiles -= friends

        # Create stairs
        for pos, terrain in self.terrain_grid.items():
            if terrain != Terrain.FLOOR_LOWER:
                continue
            east_pos = (pos[0] + 1, pos[1])
            west_pos = (pos[0] - 1, pos[1])
            north_pos = (pos[0], pos[1] - 1)
            south_pos = (pos[0], pos[1] + 1)
            if self.terrain_grid.get(east_pos) == Terrain.FLOOR_UPPER:
                self.terrain_grid[pos] = Terrain.STAIRS_RIGHT
            elif self.terrain_grid.get(west_pos) == Terrain.FLOOR_UPPER:
                self.terrain_grid[pos] = Terrain.STAIRS_LEFT
            elif self.terrain_grid.get(north_pos) == Terrain.FLOOR_UPPER:
                self.terrain_grid[pos] = Terrain.STAIRS_UP
            elif self.terrain_grid.get(south_pos) == Terrain.FLOOR_UPPER:
                self.terrain_grid[pos] = Terrain.STAIRS_DOWN

        def set_to_wall_by_stairs(new_pos: Pos, check_terrain: Terrain, 
                                  direction: Direction, stair_terrains: Tuple[Terrain]):
            while check_terrain in stair_terrains:
                new_pos = Direction.next(direction, new_pos)
                check_terrain = self.terrain_grid.get(new_pos)
            if check_terrain:
                self.terrain_grid[new_pos] = Terrain.WALL_TOP

        # Make sure stairs have a wall above them
        for pos, terrain in self.terrain_grid.items():
            stair_terrains = (Terrain.STAIRS_RIGHT, Terrain.STAIRS_LEFT)
            if terrain in stair_terrains:
                set_to_wall_by_stairs(pos, terrain, Direction.NORTH, stair_terrains)
                set_to_wall_by_stairs(pos, terrain, Direction.SOUTH, stair_terrains)

            stair_terrains = (Terrain.STAIRS_UP, Terrain.STAIRS_DOWN)
            if terrain in stair_terrains:
                set_to_wall_by_stairs(pos, terrain, Direction.EAST, stair_terrains)
                set_to_wall_by_stairs(pos, terrain, Direction.WEST, stair_terrains)

    def generate_void(self):
        convert_to_void: Set[Pos] = set()
        for pos, terrain in self.terrain_grid.items():
            if terrain != Terrain.WALL:
                continue
            adj_positions = get_cardinal_positions(pos) + get_diagonal_positions(pos)
            adj_positions = [adj for adj in adj_positions if self.check_bounds(adj)]
            if all(self.terrain_grid[adj] == Terrain.WALL for adj in adj_positions):
                convert_to_void.add(pos)

        for pos in convert_to_void:
            self.terrain_grid[pos] = Terrain.VOID

    def get_cardinal_terrain(self, pos: Pos) -> List[Optional[Terrain]]:
        return [self.get_terrain(adj) for adj in get_cardinal_positions(pos)]

    def get_diagonal_terrain(self, pos: Pos) -> List[Optional[Terrain]]:
        return [self.get_terrain(adj) for adj in get_diagonal_positions(pos)]

    def _get_section(self, pos: Pos) -> Optional[DungeonSection]:
        for section in self.sections.values():
            if pos in section.get_true_positions():
                return section
        return None

    def _get_section_in_direction(self, pos: Pos, direction: Direction) -> Optional[DungeonSection]:
        """
        Uses Section positions, not true positions
        """
        section_pos = Direction.next(direction, pos)
        return self.sections.get(section_pos)

    def _get_adj_sections(self, pos: Pos) -> List[DungeonSection]:
        """
        Uses section positions, not true positions
        """
        x, y = pos
        directions = [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
            ]
        adj_sections = [self.sections.get(adj) for adj in directions]
        adj_sections = [_ for _ in adj_sections if _]
        return adj_sections

    def _is_low_floor(self, terrain: Terrain) -> bool:
        return terrain in (
            Terrain.FLOOR_LOWER, 
            Terrain.STAIRS_DOWN, 
            Terrain.STAIRS_UP,
            )

    def _is_high_floor(self, terrain: Terrain) -> bool:
        return terrain in (
            Terrain.FLOOR_UPPER, 
            Terrain.STAIRS_LEFT, 
            Terrain.STAIRS_RIGHT,
            )

    def _determine_floor_level(self, pos: Pos) -> FloorLevel:
        """
        Returns whether this is on floor level 1 (low) or 2 (high)
        Nothing else should use this, since the user of this painter should never
        have to care
        """
        while self.terrain_grid.get(pos):
            terrain = self.terrain_grid.get(pos)
            if self._is_high_floor(terrain):
                return FloorLevel.UPPER
            elif self._is_low_floor(terrain):
                return FloorLevel.LOWER
            pos = (pos[0], pos[1] + 1)
        return FloorLevel.LOWER

    def make_walls_two_high(self):
        """
        Any walls that are adjacent on the bottom side of their group
        to a LOWER_FLOOR must be at least 2 tiles high
        """

        # Figure out which spots should be swapped
        turn_into_walls = set()
    
        # Locate walls that are only 1 tile tall above FLOOR_LOWER
        bad_walls: Set[Pos] = set()
        for pos, val in self.terrain_grid.items():
            north, _, south, _ = self.get_cardinal_terrain(pos)
            if val == Terrain.WALL_TOP and north and south \
                    and north != Terrain.WALL_TOP \
                    and south != Terrain.WALL_TOP \
                    and south != Terrain.FLOOR_UPPER \
                    and south != Terrain.STAIRS_LEFT \
                    and south != Terrain.STAIRS_RIGHT:
                bad_walls.add(pos)

        # Handle each of these walls in groups
        while bad_walls:
            test_pos = next(iter(bad_walls))
            wall_group = flood_fill(self, test_pos, match_only_these_positions=bad_walls)
            # Figure out which side (top or bottom) handles a wall addition better
            # If all of the positions south 2 tiles are exist and are not wall
            # Easy fix to make it lower by 1
            if all(self.terrain_grid.get((pos[0], pos[1] + 2), Terrain.WALL_TOP) != Terrain.WALL_TOP for pos in wall_group):
                for pos in wall_group:
                    turn_into_walls.add((pos[0], pos[1] + 1))
            # If all of the positions north 2 tiles are exist and are not wall
            # Easy fix to make it higher by 1
            elif all(self.terrain_grid.get((pos[0], pos[1] - 2), Terrain.WALL_TOP) != Terrain.WALL_TOP for pos in wall_group):
                for pos in wall_group:
                    turn_into_walls.add((pos[0], pos[1] - 1))
            # Fallback option is turn the south into a wall
            else:
                for pos in wall_group:
                    turn_into_walls.add((pos[0], pos[1] + 1))
            bad_walls -= wall_group

        # Actually swap them
        for pos in turn_into_walls:
            self.terrain_grid[pos] = Terrain.WALL_TOP

    def add_pillars(self):
        """
        For each room, determines what pillar arrangement should exist
        """
        final_pillar_positions = set()
        final_column_positions = set()
        for section_grid_pos, section in self.sections.items():
            if not section.has_full_room():
                continue
            ox, oy = section.room.get_true_offset()
            # Whether the room is taller than it is wide
            is_vertical = section.room.height >= section.room.width
            # Determine whether the smaller width of the room is even or odd
            if is_vertical:
                is_odd = section.room.width % 2 == 1
            else:
                is_odd = section.room.height % 2 == 1
            if is_odd:
                arrs = self.theme.pillar_arrangements + self.theme.odd_only_pillar_arrangements
            else:
                arrs = self.theme.pillar_arrangements + self.theme.even_only_pillar_arragements
            arr = random.choice(arrs)
            pillar_positions = set()
            if arr == "NoPillars":
                continue  # No need to do anything at all
            elif arr == "OnEdge":
                if is_vertical:
                    # Find positions on height
                    pillar_positions |= {(ox, oy + y) for y in range(1, section.room.height, 3)}
                    pillar_positions |= {(ox + section.room.width - 1, oy + y) for y in range(1, section.room.height, 3)}
                else:
                    pillar_positions |= {(ox + x, oy) for x in range(1, section.room.width, 3)}
                    pillar_positions |= {(ox + x, oy + section.room.height - 1) for x in range(1, section.room.width, 3)}
            elif arr == "NearEdge":
                if is_vertical:
                    # Find positions on height
                    pillar_positions |= {(ox + 1, oy + y) for y in range(1, section.room.height - 1, 3)}
                    pillar_positions |= {(ox + section.room.width - 2, oy + y) for y in range(1, section.room.height - 1, 3)}
                else:
                    pillar_positions |= {(ox + x, oy + 1) for x in range(1, section.room.width - 1, 3)}
                    pillar_positions |= {(ox + x, oy + section.room.height - 2) for x in range(1, section.room.width - 1, 3)}
            elif arr == "Middle":
                if is_vertical:
                    # Find positions on height
                    pillar_positions |= {(ox + section.room.width // 2, oy + y) for y in range(1, section.room.height, 3)}
                else:
                    pillar_positions |= {(ox + x, oy + section.room.height // 2) for x in range(1, section.room.width, 3)}
            elif arr == "FourCorners":
                inner_positions = section.room.get_true_inner_positions()
                topleft = sorted(inner_positions)[0]
                bottomright = sorted(inner_positions, reverse=True)[0]
                topright = sorted(inner_positions, key=lambda pos: (-pos[0], pos[1]))[0]
                bottomleft = sorted(inner_positions, key=lambda pos: (pos[0], -pos[1]))[0]
                pillar_positions |= {topleft, topright, bottomright, bottomleft}

            # Decide whether these should be pillars or columns
            # Columns only for certain arrangements with a big enough room
            if arr in {"FourCorners"} \
                    and section.room.width >= 5 and section.room.height >= 5 \
                    and section.room.floor_level == FloorLevel.LOWER:
                sorted_positions = sorted(pillar_positions, key=lambda pos: pos[1])
                top_positions = set(sorted_positions[:2])
                bottom_positions = set(sorted_positions[2:])

                column_positions = set()
                column_positions |= top_positions
                # Make the bottom columns point up instead of taking up space below them
                column_positions |= {(pos[0], pos[1] - 1) for pos in bottom_positions}
                # If we are near the top, point the columns up more
                if section_grid_pos[1] < self.grid_size[1] - 1:
                    column_positions |= {(pos[0], pos[1] - 1) for pos in column_positions}
                else:
                    column_positions |= {(pos[0], pos[1] + 1) for pos in column_positions}
                final_column_positions |= column_positions
            else:
                final_pillar_positions |= pillar_positions

        for pos in final_pillar_positions:
            self.terrain_grid[pos] = Terrain.PILLAR
        for pos in final_column_positions:
            self.terrain_grid[pos] = Terrain.WALL_TOP

    def add_forest(self):
        """
        For each room on the lower floor, randomly choose positions for forests
        """
        to_swap = set()
        for pos, terrain in self.terrain_grid.items():
            if terrain == Terrain.FLOOR_LOWER:
                if random.random() < self.theme.sparse_forest_chance:
                    to_swap.add(pos)
        for pos in to_swap:
            self.terrain_grid[pos] = Terrain.SPARSE_FOREST
                
    def wrap_in_walls(self):
        """
        Takes the entire map and wraps it in 2 layers of walls to make sure there
        are no paths to outside the map
        """
        # Enlarge the terrain_grid
        # Move the grid 1 to the right and 2 the bottom
        new_terrain_grid = {}
        for pos, val in self.terrain_grid.items():
            new_terrain_grid[(pos[0] + 1, pos[1] + 2)] = val

        # Now add the surrounding walls
        for x in [0, self.width + 1]:
            for y in range(self.height + 4):
                new_terrain_grid[(x, y)] = Terrain.WALL_TOP
        for y in [0, 1, self.height + 2, self.height + 3]:
            for x in range(self.width + 2):
                new_terrain_grid[(x, y)] = Terrain.WALL_TOP

        self.terrain_grid = new_terrain_grid
        self.width += 2
        self.height += 4

    def fill_in_crevices(self):
        """
        Finds "crevices" and fills them in as walls
        If # is walls and _ is floor
        # # _
        # _ _
        # # _
        the middle tile would be a crevice
        """
        to_fix = set()
        for pos, terrain in self.terrain_grid.items():
            if terrain == Terrain.WALL_TOP:
                continue
            north, east, south, west = self.get_cardinal_terrain(pos)
            if sum(t == Terrain.WALL_TOP for t in [north, east, south, west]) >= 3:
                to_fix.add(pos)
        for pos in to_fix:
            self.terrain_grid[pos] = Terrain.WALL_TOP

    def split_walls(self):
        """
        Converts walls from ALL WALL_TOP, and determines which should become WALL_BOTTOM and/or VOID
        whether we need a TOP wall or a BOTTOM wall for this sprite
        """
        all_walls = {pos for pos, terrain in self.terrain_grid.items() if terrain == Terrain.WALL_TOP}

        def is_wall(terrain: Terrain) -> bool:
            return terrain == Terrain.WALL_TOP or terrain == Terrain.WALL_BOTTOM

        # First, build standalone columns
        for pos in all_walls.copy():
            north, east, south, west = self.get_cardinal_terrain(pos)
            if not is_wall(east) and not is_wall(west) and not is_wall(south):
                if self._determine_floor_level(pos) == FloorLevel.LOWER \
                        and north == Terrain.WALL_TOP:
                    self.terrain_grid[pos] = Terrain.WALL_BOTTOM
                all_walls.remove(pos)

        for pos in all_walls.copy():
            south_pos = (pos[0], pos[1] + 1)
            if is_wall(self.terrain_grid.get(south_pos)) or not self.check_bounds(south_pos):
                all_walls.remove(pos)

        for pos in all_walls.copy():
            south_pos = (pos[0], pos[1] + 1)
            north_pos = (pos[0], pos[1] - 1)
            north, _, south, _ = self.get_cardinal_terrain(pos)
            if (is_wall(north) or not self.check_bounds(north_pos)) \
                    and not is_wall(south) \
                    and (self._determine_floor_level(pos) == FloorLevel.LOWER
                         or self._determine_floor_level(south_pos) == FloorLevel.LOWER):
                self.terrain_grid[pos] = Terrain.WALL_BOTTOM
                all_walls.remove(pos)

        # Convert pieces that are surrounded to void
        convert_to_void: Set[Pos] = set()
        for pos in self.terrain_grid.keys():
            if self.terrain_grid.get(pos) == Terrain.WALL_TOP \
                    and all(terrain == Terrain.WALL_TOP or not self.check_bounds(adj) for terrain, adj in 
                            zip(self.get_cardinal_terrain(pos) + self.get_diagonal_terrain(pos),
                                get_cardinal_positions(pos) + get_diagonal_positions(pos))):
                convert_to_void.add(pos)

        for pos in convert_to_void:
            self.terrain_grid[pos] = Terrain.VOID

    def crop_void(self):
        # Now crop out areas of just void
        # Left Columns
        while all(self.terrain_grid[(0, y)] == Terrain.VOID for y in range(self.height)):
            for y in range(self.height):
                del self.terrain_grid[(0, y)]
            new_terrain_grid = {}
            for pos, val in self.terrain_grid.items():
                new_terrain_grid[(pos[0] - 1, pos[1])] = val
            self.terrain_grid = new_terrain_grid
            self.width -= 1
        # Right Columns
        while all(self.terrain_grid[(self.width - 1, y)] == Terrain.VOID for y in range(self.height)):
            for y in range(self.height):
                del self.terrain_grid[(self.width - 1, y)]
            self.width -= 1
        # Top Rows
        while all(self.terrain_grid[(x, 0)] == Terrain.VOID for x in range(self.width)):
            for x in range(self.width):
                del self.terrain_grid[(x, 0)]
            new_terrain_grid = {}
            for pos, val in self.terrain_grid.items():
                new_terrain_grid[(pos[0], pos[1] - 1)] = val
            self.terrain_grid = new_terrain_grid
            self.height -= 1
        # Right Columns
        while all(self.terrain_grid[(x, self.height - 1)] == Terrain.VOID for x in range(self.width)):
            for x in range(self.width):
                del self.terrain_grid[(x, self.height - 1)]
            self.height -= 1

    def print_terrain_grid(self):
        print("   ", end='')
        for x in range(self.width):
            print("%1d" % (x % 10), end='')
        print("\n", end='')
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                terrain = self.terrain_grid[(x, y)]
                if terrain == Terrain.FLOOR_UPPER \
                        or terrain == Terrain.FLOOR_LOWER \
                        or terrain == Terrain.GRASS \
                        or terrain == Terrain.RUINS:
                    print("_", end='')
                elif terrain == Terrain.WALL_TOP:
                    print("#", end='')
                elif terrain == Terrain.WALL_BOTTOM:
                    print("|", end='')
                elif terrain == Terrain.VOID:
                    print(" ", end='')
                elif terrain == Terrain.PILLAR or terrain == Terrain.SPARSE_FOREST:
                    print("%", end='')
                elif terrain == Terrain.STAIRS_UP:
                    print("^", end='')
                elif terrain == Terrain.STAIRS_DOWN:
                    print("v", end='')
                elif terrain == Terrain.STAIRS_LEFT:
                    print("<", end='')
                elif terrain == Terrain.STAIRS_RIGHT:
                    print(">", end='')
                elif terrain == Terrain.START:
                    print("S", end='')
                elif terrain == Terrain.END:
                    print("E", end='')
                else:
                    print("?", end='')
            print("\n", end='')

    def print_sections(self):
        all_hallways = utils.flatten_list([list(section.hallways.values()) for section in self.sections.values()])
        print("   ", end='')
        for x in range(self.width):
            print("%1d" % (x % 10), end='')
        print("\n", end='')
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                section = self._get_section((x, y))
                if (x, y) in all_hallways:
                    print("X", end='')
                elif section and section.room and (x, y) in section.room.get_true_positions():
                    if section.room.floor_level == FloorLevel.UPPER:
                        print("+", end='')
                    else:
                        print("-", end='')
                else:
                    print(" ", end='')
            print("\n", end='')

class DungeonSection:
    def __init__(self, size: Pos, offset: Pos, tilemap: DungeonTileMap):
        self.width, self.height = size
        self.offset = offset
        self.tilemap = tilemap
        self.room: Optional[DungeonRoom] = None
        self.hallways: Dict[Direction, List[Pos]] = {}  # True positions

    def get_true_positions(self) -> List[Pos]:
        positions = []
        for x in range(self.width):
            for y in range(self.height):
                positions.append((self.offset[0] + x, self.offset[1] + y))
        return positions

    def has_full_room(self) -> bool:
        return self.room and self.room.width > 1 and self.room.height > 1

    def has_big_room(self) -> bool:
        return self.room and self.room.width >= 3 and self.room.height >= 3

    def generate_room(self):
        width = random.randint(self.tilemap.theme.room_size_min_x, self.width - 1)
        height = random.randint(self.tilemap.theme.room_size_min_y, self.height - 1)
        offset_x = random.randint(0, self.width - width - 1)
        offset_y = random.randint(0, self.height - height - 1)
        floor_level = FloorLevel.LOWER if random.random() < self.tilemap.theme.floor_lower_chance else FloorLevel.UPPER

        self.room = DungeonRoom((width, height), (offset_x, offset_y), self, self.tilemap, floor_level)

    def generate_hallway_node(self):
        offset_x = random.randint(1, self.width - 1)
        offset_y = random.randint(1, self.height - 1)
        floor_level = FloorLevel.LOWER if random.random() < self.tilemap.theme.floor_lower_chance else FloorLevel.UPPER

        self.room = DungeonRoom((1, 1), (offset_x, offset_y), self, self.tilemap, floor_level)

    def connect(self, other: DungeonSection, direction: Direction):
        hallway_width = 2 if random.random() < self.tilemap.theme.wide_hallway_chance else 1
        hallway = []

        if direction == Direction.EAST:
            # Find where to start on the right wall of me and the left wall of them
            start_on_wall = random.randrange(self.room.height) + self.offset[1] + self.room.offset[1]
            other_start_on_wall = random.randrange(other.room.height) + other.offset[1] + other.room.offset[1]
            # Find x starting point
            start: int = self.offset[0] + self.room.offset[0] + self.room.width
            end: int = other.offset[0] + other.room.offset[0]
            midpoint: int = other.offset[0]
            begin_side = random.choice([-1, 1])
            middle_side = random.choice([-1, 1])
            end_side = random.choice([-1, 1])

            for x in range(start, midpoint):
                hallway.append((x, start_on_wall))
                # Make the hallway wider if possible
                if hallway_width == 2 and self.room.height > 1:
                    hallway.append((x, start_on_wall + begin_side))
            if start_on_wall < other_start_on_wall:
                for y in range(start_on_wall, other_start_on_wall + 1):
                    hallway.append((midpoint, y))
                    if hallway_width == 2:
                        hallway.append((midpoint + middle_side, y))
            else:
                for y in range(other_start_on_wall, start_on_wall + 1):
                    hallway.append((midpoint, y))
                    if hallway_width == 2:
                        hallway.append((midpoint + middle_side, y))
            for x in range(midpoint, end):
                hallway.append((x, other_start_on_wall))
                # Make the hallway wider if possible
                if hallway_width == 2 and other.room.height > 1:
                    hallway.append((x, other_start_on_wall + end_side))

        elif direction == Direction.SOUTH:
            # Find where to start on the bottom wall of me and the top wall of them
            start_on_wall = random.randrange(self.room.width) + self.offset[0] + self.room.offset[0]
            other_start_on_wall = random.randrange(other.room.width) + other.offset[0] + other.room.offset[0]
            # Find y starting point
            start: int = self.offset[1] + self.room.offset[1] + self.room.height
            end: int = other.offset[1] + other.room.offset[1]
            midpoint: int = other.offset[1]
            begin_side = random.choice([-1, 1])
            middle_side = random.choice([-1, 1])
            end_side = random.choice([-1, 1])

            for y in range(start, midpoint):
                hallway.append((start_on_wall, y))
                # make the hallway wider if possible
                if hallway_width == 2 and self.room.width > 1:
                    hallway.append((start_on_wall + begin_side, y))
            if start_on_wall < other_start_on_wall:
                for x in range(start_on_wall, other_start_on_wall + 1):
                    hallway.append((x, midpoint))
                    if hallway_width == 2:
                        hallway.append((x, midpoint + middle_side))
            else:
                for x in range(other_start_on_wall, start_on_wall + 1):
                    hallway.append((x, midpoint))
                    if hallway_width == 2:
                        hallway.append((x, midpoint + middle_side))
            for y in range(midpoint, end):
                hallway.append((other_start_on_wall, y))
                # make the hallway wider if possible
                if hallway_width == 2 and other.room.width > 1:
                    hallway.append((other_start_on_wall + end_side, y))

        self.hallways[direction] = hallway
                
class DungeonRoom:
    def __init__(self, size: Pos, offset: Pos, section: DungeonSection, 
                 tilemap: DungeonTileMap, floor_level: FloorLevel):
        self.width, self.height = size
        self.offset = offset
        self.section = section
        self.tilemap = tilemap
        self.floor_level = floor_level
        self.positions: List[Pos] = \
            [(x + self.offset[0], y + self.offset[1]) for x in range(self.width) for y in range(self.height)]

    def get_true_offset(self) -> Pos:
        """
        Returns the true top left position of the room
        """
        ox, oy = self.section.offset
        x, y = self.offset
        return (ox + x, oy + y)

    def get_true_positions(self) -> List[Pos]:
        ox, oy = self.section.offset
        return [(x + ox, y + oy) for (x, y) in self.positions]

    def get_true_inner_positions(self) -> List[Pos]:
        ox, oy = self.section.offset
        pos = [(x + ox, y + oy) for (x, y) in self.positions 
               if x > self.offset[0] 
               and y > self.offset[1]
               and x - self.offset[0] < self.width - 1
               and y - self.offset[1] < self.height - 1]
        return pos

# python -m app.dungeon_maker.terrain_generation
if __name__ == '__main__':
    from app.dungeon_maker.themes import DefaultTheme
    generate_terrain(DefaultTheme)
