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
    WALL = 1
    FLOOR_UPPER = 2
    FLOOR_LOWER = 3
    WATER = 4
    STAIRS_UP = 5
    STAIRS_RIGHT = 6
    STAIRS_DOWN = 7
    STAIRS_LEFT = 8
    PILLAR = 9
    FOREST = 10
    START = 11
    END = 12

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
    tilemap.reset_grid(Terrain.WALL)

    tilemap.set_sections(4, 2)

    num_rooms = tilemap.generate_rooms()
    if num_rooms < 2:  # Need at least 2 rooms
        return
    tilemap.connect_rooms()
    tilemap.generate_start_and_end()

    tilemap.coerce_terrain()
    tilemap.generate_void()

    tilemap.print_grid()

    return tilemap

class DungeonTileMap:
    room_chance = 0.6

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.terrain_grid: Dict[Pos, Terrain] = {}
        self.start: Pos = None
        self.end: Pos = None
        self.grid_size: Pos = None
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
                for pos in section.room.get_true_positions():
                    self.terrain_grid[pos] = Terrain.FLOOR_LOWER
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

    def determine_floor_level(self, pos: Pos) -> int:
        # TODO
        """
        Eventually will return whether this is on floor level 1 (low) or 2 (high)
        """
        return 1

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
                elif terrain == Terrain.WALL:
                    print("#", end='')
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

    def generate_room(self):
        width = random.randint(self.min_room_x, self.width - 1)
        height = random.randint(self.min_room_y, self.height - 1)
        offset_x = random.randint(0, self.width - width - 1)
        offset_y = random.randint(0, self.height - height - 1)

        self.room = DungeonRoom((width, height), (offset_x, offset_y), self, self.tilemap)

    def generate_hallway_node(self):
        offset_x = random.randint(1, self.width - 1)
        offset_y = random.randint(1, self.height - 1)

        self.room = DungeonRoom((1, 1), (offset_x, offset_y), self, self.tilemap)

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
    def __init__(self, size: Pos, offset: Pos, section: DungeonSection, tilemap: DungeonTileMap):
        self.width, self.height = size
        self.offset = offset
        self.section = section
        self.tilemap = tilemap
        self.positions: List[Pos] = \
            [(x + self.offset[0], y + self.offset[1]) for x in range(self.width) for y in range(self.height)]

    def get_true_positions(self) -> List[Pos]:
        ox, oy = self.section.offset
        return [(x + ox, y + oy) for (x, y) in self.positions]

# python -m app.dungeon_maker.terrain_generation
if __name__ == '__main__':
    generate_terrain('normal', (30, 18))
