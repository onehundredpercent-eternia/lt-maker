"""
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

from enum import Enum
import random
from typing import Dict, Optional, Tuple

class Terrain(Enum):
    VOID = 0
    WALL = 1
    FLOOR_UPPER = 2
    FLOOR_LOWER = 3
    WATER = 4
    STAIR = 5
    PILLAR = 6
    FOREST = 7

Pos = Tuple[int, int]

# Magic numbers

def generate_terrain(theme: str, size: Pos, seed=-1):
    random.seed(seed)

    while True:
        result = _generate_terrain_process(theme, size)
        if result:
            break

    return result

def _generate_terrain_process(theme: str, size: Pos):
    width, height = size

    tilemap = DungeonTileMap(width, height)
    tilemap.reset_grid(Terrain.WALL)

    tilemap.set_sections(5, 2)

    tilemap.generate_rooms()
    tilemap.connect_rooms()
    tilemap.generate_start_and_end()

    tilemap.coerce_terrain()

    return tilemap

class DungeonTileMap:
    room_chance = 0.6
    hallway_node_chance = 0.3

    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.terrain_grid: Dict[Pos, Terrain] = {}
        self.start: Pos = None
        self.end: Pos = None
        self.sections: Dict[Pos, DungeonSection] = {}

    def reset_grid(self, terrain: Terrain):
        for x in range(self.width):
            for y in range(self.height):
                self.terrain_grid[(x, y)] = terrain

    def set_sections(self, x: int, y: int):
        xwidth = self.width // x
        ywidth = self.height // y 
        for xi in range(x):
            for yi in range(y):
                offset = (xi * xwidth, yi * ywidth)
                self.sections[(xi, yi)] = DungeonSection((xwidth, ywidth), offset, self)

    def generate_rooms(self):
        for section in self.sections.values():
            val = random.random()
            if val < self.room_chance:
                section.generate_room()
            elif val < self.room_chance + self.hallway_node_chance:
                section.generate_hallway_node()
            # else generate nothing is blank

class DungeonSection:
    min_room_x = 3
    min_room_y = 3

    def __init__(self, size: Pos, offset: Pos, tilemap: DungeonTileMap):
        self.width, self.height = size
        self.offset = offset
        self.tilemap = tilemap
        self.room: Optional[DungeonRoom] = None

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

class DungeonRoom:
    def __init__(self, size: Pos, offset: Pos, section: DungeonSection, tilemap: DungeonTileMap):
        self.width, self.height = size
        self.offet = offset
        self.section = section
        self.tilemap = tilemap


if __name__ == '__main__':
    generate_terrain('normal', (30, 18))
