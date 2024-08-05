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
from app.dungeon_maker.utilities import set_random_seed

class Terrain(Enum):
    VOID = 0
    WALL_TOP = 1
    WALL_BOTTOM = 2
    FLOOR_UPPER = 3
    FLOOR_LOWER = 4
    WATER = 5
    STAIRS_UP = 6
    STAIRS_RIGHT = 7
    STAIRS_DOWN = 8
    STAIRS_LEFT = 9
    PILLAR = 10
    FOREST = 11
    START = 12
    END = 13

class FloorLevel(Enum):
    LOWER = 1
    UPPER = 2

def generate_terrain(theme: str, size: Pos, seed=-1) -> DungeonTileMap:
    random.seed(seed)
    set_random_seed(seed)

    while True:
        result = _generate_terrain_process(theme, size)
        if result:
            break

    return result

def _generate_terrain_process(theme: str, size: Pos) -> Optional[DungeonTileMap]:
    width, height = size

    tilemap = DungeonTileMap(width, height)
    tilemap.reset_grid(Terrain.WALL_TOP)

    tilemap.set_sections(4, 2)

    num_rooms = tilemap.generate_rooms()
    if num_rooms < 2:  # Need at least 2 rooms
        return
    tilemap.connect_rooms()
    tilemap.generate_start_and_end()

    tilemap.coerce_terrain()

    tilemap.make_walls_two_high()
    tilemap.wrap_in_walls()
    tilemap.split_walls()
    tilemap.crop_void()

    tilemap.print_grid()

    return tilemap

class DungeonTileMap:
    room_chance = 0.6

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.terrain_grid: Dict[Pos, Terrain] = {}
        self.start: Pos = None
        self.end: Pos = None
        self.grid_size: Tuple[int, int] = None
        self.sections: Dict[Pos, DungeonSection] = {}

    def get_terrain(self, pos: Pos) -> Optional[Terrain]:
        return self.terrain_grid.get(pos, None)

    def check_bounds(self, pos: Pos) -> bool:
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def reset_grid(self, terrain: Terrain):
        for x in range(self.width):
            for y in range(self.height):
                self.terrain_grid[(x, y)] = terrain

    def set_sections(self, x: int, y: int):
        self.grid_size = (x, y)
        xwidth = self.width // x
        ywidth = self.height // y 
        for xi in range(x):
            for yi in range(y):
                offset = (xi * xwidth, yi * ywidth)
                self.sections[(xi, yi)] = DungeonSection((xwidth, ywidth), offset, self)

    def generate_rooms(self) -> int:
        """
        Returns the number of rooms generated
        """
        full_rooms_generated = 0
        for section in self.sections.values():
            val = random.random()
            if val < self.room_chance:
                section.generate_room()
                full_rooms_generated += 1
            else:
                section.generate_hallway_node()
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

    def generate_start_and_end(self):
        available_sections = [
            (pos, section.room) for pos, section in self.sections.items() 
            if section.room 
            and section.room.width > 1 
            and section.room.height > 1
        ]
        start_pos, start_room = random.choice(available_sections)
        furthest_away_section = \
            list(sorted(available_sections, 
                        key=lambda section: utils.calculate_distance(start_pos, section[0])
                        )
                 )[-1]
        end_pos, end_room = furthest_away_section
        # Choose a random position in the room
        self.start = random.choice(start_room.get_true_positions())
        self.end = random.choice(end_room.get_true_positions())

    def coerce_terrain(self):
        for section in self.sections.values():
            # Fill all rooms
            if section.room:
                if section.room.floor_level == FloorLevel.UPPER:
                    terrain = Terrain.FLOOR_UPPER  
                else:
                    terrain = Terrain.FLOOR_LOWER
                for pos in section.room.get_true_positions():
                    self.terrain_grid[pos] = terrain
            # Fill all hallways
            for hallway in section.hallways:
                for pos in hallway:
                    self.terrain_grid[pos] = Terrain.FLOOR_LOWER

        if self.start:
            self.terrain_grid[self.start] = Terrain.START
        if self.end:
            self.terrain_grid[self.end] = Terrain.END

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

    def _determine_floor_level(self, pos: Pos) -> int:
        """
        Returns whether this is on floor level 1 (low) or 2 (high)
        Nothing else should use this, since the user of this painter should never
        have to care
        """
        section = self._get_section(pos)
        if section and section.room:
            return section.room.floor_level
        return FloorLevel.LOWER

    def make_walls_two_high(self):
        """
        Any walls that are adjacent on the bottom side of their group
        to a LOWER_FLOOR must be at least 2 tiles high
        """

        # Figure out which spots should be swapped
        swap_these = set()
        for pos, val in self.terrain_grid.items():
            if val == Terrain.FLOOR_LOWER:
                north_terrain = self.terrain_grid.get((pos[0], pos[1] - 1))
                north_north_terrain = self.terrain_grid.get((pos[0], pos[1] - 2))
                # If I have wall above me, but the one above that is not a wall
                if north_terrain == Terrain.WALL_TOP and north_north_terrain \
                        and north_north_terrain != Terrain.WALL_TOP:
                    south_terrain = self.terrain_grid.get((pos[0], pos[1] - 1))
                    n3_terrain = self.terrain_grid.get((pos[0], pos[1] - 3))
                    # If I have a floor below me, I am safe to turn myself into wall
                    if south_terrain == Terrain.FLOOR_LOWER:
                        swap_these.add(pos)
                    # If I have a floor above me, I am safe to turn the one above me into wall
                    elif n3_terrain in (Terrain.FLOOR_LOWER, Terrain.FLOOR_UPPER):
                        swap_these.add((pos[0], pos[1] - 2))
                    # Else fall back on self
                    else:
                        swap_these.add(pos)

        # Actually swap them
        for pos in swap_these:
            self.terrain_grid[pos] = Terrain.WALL_TOP

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

    def print_grid(self):
        print("   ", end='')
        for x in range(self.width):
            print("%1d" % (x % 10), end='')
        print("\n", end='')
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                terrain = self.terrain_grid[(x, y)]
                if terrain == Terrain.FLOOR_UPPER or terrain == Terrain.FLOOR_LOWER:
                    print("_", end='')
                elif terrain == Terrain.WALL_TOP:
                    print("#", end='')
                elif terrain == Terrain.WALL_BOTTOM:
                    print("|", end='')
                elif terrain == Terrain.VOID:
                    print(" ", end='')
                elif terrain == Terrain.PILLAR or terrain == Terrain.FOREST:
                    print("%", end='')
                elif terrain == Terrain.STAIRS_UP or terrain == Terrain.STAIRS_DOWN:
                    print("^", end='')
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

class DungeonSection:
    min_room_x = 3
    min_room_y = 3

    def __init__(self, size: Pos, offset: Pos, tilemap: DungeonTileMap):
        self.width, self.height = size
        self.offset = offset
        self.tilemap = tilemap
        self.room: Optional[DungeonRoom] = None
        self.hallways: List[List[Pos]] = []  # True positions

    def get_true_positions(self) -> List[Pos]:
        positions = []
        for x in range(self.width):
            for y in range(self.height):
                positions.append((self.offset[0] + x, self.offset[1] + y))
        return positions

    def generate_room(self):
        width = random.randint(self.min_room_x, self.width - 1)
        height = random.randint(self.min_room_y, self.height - 1)
        offset_x = random.randint(0, self.width - width - 1)
        offset_y = random.randint(0, self.height - height - 1)
        floor_level = random.choice((FloorLevel.LOWER, FloorLevel.UPPER))

        self.room = DungeonRoom((width, height), (offset_x, offset_y), self, self.tilemap, floor_level)

    def generate_hallway_node(self):
        offset_x = random.randint(1, self.width - 1)
        offset_y = random.randint(1, self.height - 1)
        floor_level = random.choice((FloorLevel.LOWER, FloorLevel.UPPER))

        self.room = DungeonRoom((1, 1), (offset_x, offset_y), self, self.tilemap, floor_level)

    def connect(self, other: DungeonSection, direction: Direction):
        hallway_width = random.choice([1, 2])
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
                if hallway_width == 2:
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
                if hallway_width == 2:
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
                if hallway_width == 2:
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
                if hallway_width == 2:
                    hallway.append((other_start_on_wall + end_side, y))

        self.hallways.append(hallway)
                
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

    def get_true_positions(self) -> List[Pos]:
        ox, oy = self.section.offset
        return [(x + ox, y + oy) for (x, y) in self.positions]

# python -m app.dungeon_maker.terrain_generation
if __name__ == '__main__':
    generate_terrain('normal', (30, 18))
