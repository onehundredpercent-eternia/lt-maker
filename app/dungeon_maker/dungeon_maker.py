import random
import itertools
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple

from app.utilities import utils


def flood_fill(check_bounds, room_tiles: set, pos: tuple) -> set:
    blob_positions = set()
    unexplored_stack = []

    def find_similar(starting_pos: tuple):
        unexplored_stack.append(starting_pos)

        counter = 0
        while unexplored_stack and counter < 99999:
            current_pos = unexplored_stack.pop()

            if current_pos in blob_positions:
                continue
            if not check_bounds(*current_pos):
                continue
            if current_pos not in room_tiles:
                continue
            blob_positions.add(current_pos)
            unexplored_stack.append((current_pos[0] + 1, current_pos[1]))
            unexplored_stack.append((current_pos[0] - 1, current_pos[1]))
            unexplored_stack.append((current_pos[0], current_pos[1] + 1))
            unexplored_stack.append((current_pos[0], current_pos[1] - 1))
            counter += 1
        if counter >= 99999:
            raise RuntimeError("Unexpected infinite loop in generic flood_fill")

    # Determine which coords should be flood-filled
    find_similar(pos)
    return blob_positions

class DungeonTileMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.terrain_grid: Dict[Tuple[int, int], str] = {}
        self.tile_grid = {}  # pos -> engine.Surface
        self.layer_grid: Dict[Tuple[int, int], int] = {}

    def get_terrain(self, pos: Tuple[int, int]) -> str:
        return self.terrain_grid.get(pos, None)

    def get_true_terrain_grid(self) -> Dict[Tuple[int, int], str]:
        conversion_dict = \
            {'Floor2': 'Floor',
             'StairsUpDown': 'Stairs',
             'StairsLeft': 'Stairs',
             'StairsRight': 'Stairs',
             'Pillar2': 'Pillar',
             }
        return {pos: conversion_dict.get(terrain, terrain) for pos, terrain in self.terrain_grid.items()}

    def set_terrain(self, x: int, y: int, terrain: str):
        self.terrain_grid[(x, y)] = terrain

    def get_layer(self, pos: Tuple[int, int]) -> int:
        return self.layer_grid.get(pos, None)

    def calc_layer(self, pos: Tuple[int, int]) -> int:
        def south(pos: Tuple):
            return pos[0], pos[1] + 1

        while pos[1] < self.height:
            if self.get_layer(pos):
                return self.get_layer(pos)
            pos = south(pos)
        return None
    
    def set_layer(self, x: int, y: int, layer: int):
        self.layer_grid[(x, y)] = layer

    def reset_grid(self, terrain: str):
        self.layer_grid.clear()
        for x in range(self.width):
            for y in range(self.height):
                self.terrain_grid[(x, y)] = terrain
                self.layer_grid[(x, y)] = 1      

    def print_grid(self):
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                terrain = self.get_terrain((x, y))
                if terrain == 'Floor' or terrain == 'Floor2':
                    print("_", end='')
                elif terrain == 'Wall':
                    print("#", end='')
                elif terrain == 'Void':
                    print(" ", end='')
                elif terrain == 'Pillar' or terrain == 'Pillar2':
                    print("%", end='')
                elif terrain == 'StairsUpDown':
                    print("^", end='')
                elif terrain == 'StairsLeft':
                    print("<", end='')
                elif terrain == 'StairsRight':
                    print(">", end='')
                else:
                    print("S", end='')
            print("\n", end='')

    def print_layer_grid(self):
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                layer = self.get_layer((x, y))
                print("%d" % layer, end='')
            print("\n", end='')

    def check_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cardinal_terrain(self, pos: tuple) -> tuple:
        return tuple([self.get_terrain(adj) for adj in utils.get_cardinal_positions(pos)])

    def get_diagonal_terrain(self, pos: tuple) -> tuple:
        return tuple([self.get_terrain(adj) for adj in utils.get_diagonal_positions(pos)])

    def get_cardinal_layers(self, pos: tuple) -> tuple:
        return tuple([self.get_layer(adj) for adj in utils.get_cardinal_positions(pos)])

@dataclass(eq=False)
class RoomPrefab:
    x: int = 0  # Topleft of Floor
    y: int = 0  # Topright of Floor
    width: int = 0  # Width of Floor
    height: int = 0  # Height of Floor

    def overlaps(self, other) -> bool:
        if self.x - 1 < other.x + other.width and \
                self.x + self.width + 1 > other.x and \
                self.y - 1 < other.y + other.height and \
                self.y + self.height + 1 > other.y:
            return True
        else:
            return False

@dataclass(eq=False)
class Room:
    tiles: Set[tuple] = None
    wall_tiles: Set[tuple] = None
    prefab: RoomPrefab = None

    @classmethod
    def from_prefab(cls, prefab, tilemap):
        new_room = Room(set(), set(), prefab)
        for x in range(prefab.x, prefab.x + prefab.width):
            for y in range(prefab.y, prefab.y + prefab.height):
                if tilemap.check_bounds(x, y):
                    new_room.tiles.add((x, y))
        new_room.wall_tiles = new_room.get_wall_tiles(tilemap)
        return new_room

    def get_wall_tiles(self, tilemap) -> Set[tuple]:
        wall_tiles = set()
        # Left wall
        for y in range(-1, self.prefab.height + 1):
            wall_tiles.add((self.prefab.x - 1, self.prefab.y + y))
        # Right wall
        for y in range(-1, self.prefab.height + 1):
            wall_tiles.add((self.prefab.x + self.prefab.width, self.prefab.y + y))
        # Top wall
        for x in range(-1, self.prefab.width + 1):
            wall_tiles.add((self.prefab.x + x, self.prefab.y - 1))
        # Bottom wall
        for x in range(-1, self.prefab.width + 1):
            wall_tiles.add((self.prefab.x + x, self.prefab.y + self.prefab.height))
        return {tile for tile in wall_tiles if tilemap.check_bounds(*tile)}

    def get_walls(self, tilemap) -> List[List[Tuple[int, int]]]:
        # Returns a list of the walls North, East, South, West
        # North wall
        north_wall = [(self.prefab.x + x, self.prefab.y - 1) for x in range(0, self.prefab.width)]
        north_wall = [tile for tile in north_wall if tilemap.check_bounds(*tile)]
        # East wall
        east_wall = [(self.prefab.x + self.prefab.width, self.prefab.y + y) for y in range(0, self.prefab.height)]
        east_wall = [tile for tile in east_wall if tilemap.check_bounds(*tile)]
        # South wall
        south_wall = [(self.prefab.x + x, self.prefab.y + self.prefab.height) for x in range(0, self.prefab.width)]
        south_wall = [tile for tile in south_wall if tilemap.check_bounds(*tile)]
        # West wall
        west_wall = [(self.prefab.x - 1, self.prefab.y + y) for y in range(0, self.prefab.height)]
        west_wall = [tile for tile in west_wall if tilemap.check_bounds(*tile)]

        return [north_wall, east_wall, south_wall, west_wall]

    @property
    def width(self):
        return self.prefab.width

    @property
    def height(self):
        return self.prefab.height

@dataclass(eq=False)
class Area:
    tiles: Set[tuple] = None

    @property
    def x(self) -> float:
        # returns the center of the room in the x direction
        return sum(tile[0] for tile in self.tiles) / len(self.tiles)

    @property
    def y(self) -> float:
        # returns the center of the room in the y direction
        return sum(tile[1] for tile in self.tiles) / len(self.tiles)

    @property
    def size(self):
        return len(self.tiles)

    @property
    def width(self):
        return max(tile[0] for tile in self.tiles) - min(tile[0] for tile in self.tiles) + 1

    @property
    def height(self):
        return max(tile[1] for tile in self.tiles) - min(tile[1] for tile in self.tiles) + 1
    
def print_rooms(rooms: List[Room]):
    # Print rooms
    all_positions = {}
    for idx, room in enumerate(rooms):
        all_positions.update({pos: idx for pos in room.tiles})
    width = max(pos[0] for pos in all_positions.keys()) + 1
    height = max(pos[1] for pos in all_positions.keys()) + 1
    for y in range(height):
        print("%02d " % y, end='')
        for x in range(width):
            if (x, y) in all_positions:
                print("%d" % (all_positions[(x, y)] % 10), end='')
            else:
                print(" ", end='')
        print("\n", end='')

def print_room_prefabs(rooms, width, height):
    for y in range(height):
        print("%02d " % y, end='')
        for x in range(width):
            for idx, room in enumerate(rooms[:10]):
                if (int(room.x - room.width/2) == x and room.y - room.height/2 <= y <= room.y + room.height/2) or \
                   (int(room.x + room.width/2) == x and room.y - room.height/2 <= y <= room.y + room.height/2) or \
                   (int(room.y - room.height/2) == y and room.x - room.width/2 <= x <= room.x + room.width/2) or \
                   (int(room.y + room.height/2) == y and room.x - room.width/2 <= x <= room.x + room.width/2):
                    print("%1d" % idx, end='')
                    break
            else:
                print(" ", end='')
        print("\n", end='')

def create_room(avg_size: float, map_width: int, map_height: int):
    while True:
        # Random size
        rwidth = int(round(random.normalvariate(mu=avg_size, sigma=1)))
        # Generally square
        rheight = int(round(random.normalvariate(mu=rwidth, sigma=0.75)))
        if rwidth <= 0 or rheight <= 0:
            continue
        # choose a random point to place the room
        center = random.randrange(0, map_width * map_height)
        x, y = center % map_width, center // map_height
        x -= rwidth//2
        y -= rheight//2
        new_room = RoomPrefab(x, y, rwidth, rheight)
        return new_room

def find_adjacency_connections(tilemap: DungeonTileMap, rooms: List[Room], all_room_tiles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    print("Find connections")
    # Find walls between rooms
    new_floors = set()
    all_checked_walls = set()
    for room in rooms:
        print(room)
        for wall in room.get_walls(tilemap):
            # Remove any walls that have already been processed
            wall = sorted(tile for tile in wall if tile not in all_checked_walls)
            
            if len(wall) == 0:
                # No wall, just skip
                pass
            elif len(wall) % 2:  # odd
                # Remove center of wall
                idx = len(wall) // 2
                new_floors.add(wall[idx])
            else:  # even
                # Remove center of wall
                idx = len(wall) // 2
                new_floors.add(wall[idx - 1])
                new_floors.add(wall[idx])
            all_checked_walls |= set(wall)
    return new_floors

def place_connections_onto_grid(tilemap: DungeonTileMap, connections: Set[Tuple[int, int]]):
    for connection in connections:
        # Check layers of nearby positions
        north, east, south, west = tilemap.get_cardinal_layers(connection)
        layers = {north, east, south, west}
        layers.discard(None)
        # Place regular floors
        if len(layers) == 1:
            tilemap.terrain_grid[connection] = 'Floor'
            # Set the layer of this one
            tilemap.layer_grid[connection] = list(layers)[0]
        # Place stairs
        elif len(layers) == 2:
            # Determine direction
            if north != south:
                tilemap.terrain_grid[connection] = 'StairsUpDown'
            elif east != west and east and west:
                print(east, west)
                if west > east:
                    tilemap.terrain_grid[connection] = 'StairsLeft'
                elif east > west:
                    tilemap.terrain_grid[connection] = 'StairsRight'
            else:
                print("Could not determine which direction the stairs should face (%s, %s)" % connection)
        else:
            print("No nearby floor tiles? (%s, %s)" % connection)

def fill_in_one_way_alcoves(tilemap: DungeonTileMap) -> None:
    for pos in tilemap.terrain_grid.keys():
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        if sum([north == 'Wall', east == 'Wall', south == 'Wall', west == 'Wall']) >= 3:
            tilemap.set_terrain(*pos, 'Wall')

def get_floor_positions(tilemap: DungeonTileMap) -> List[Tuple[int, int]]:
    valid_positions = [(x, y) for x in range(tilemap.width) for y in range(tilemap.height)]
    return sorted([pos for pos in valid_positions if tilemap.get_terrain(pos) in ('Floor', 'Pillar', 'StairsUpDown', 'StairsLeft', 'StairsRight')])

def find_new_areas(tilemap: DungeonTileMap, room_tiles: Set[Tuple]) -> List[Area]:
    rooms = []
    while room_tiles:
        tile = next(iter(room_tiles))
        extant_tiles = flood_fill(tilemap.check_bounds, room_tiles, tile)
        if extant_tiles:
            room = Area(extant_tiles)
            rooms.append(room)
            for tile in extant_tiles:
                room_tiles.remove(tile)
    return rooms

def find_all_areas(positions: List[Tuple]) -> List[Area]:
    rooms = []
    floors = set(positions)

    @dataclass
    class Shape:
        shape: Dict = None
        remove: List = None

        def rotate(self, how_much=0):
            if how_much == 0:
                return Shape(self.shape, self.remove)
            elif how_much == 1:  # 90 degrees
                return Shape({(-y, x): floor for (x, y), floor in self.shape.items()},
                             [(-y, x) for (x, y) in self.remove])
            elif how_much == 2:  # 180 degrees
                return Shape({(-x, -y): floor for (x, y), floor in self.shape.items()},
                             [(-x, -y) for (x, y) in self.remove])
            elif how_much == 3:  # 270 degrees
                return Shape({(y, -x): floor for (x, y), floor in self.shape.items()},
                             [(y, -x) for (x, y) in self.remove])

        def flip_vert(self):
            return Shape({(x, -y): floor for (x, y), floor in self.shape.items()},
                         [(x, -y) for (x, y) in self.remove])

        def flip_horiz(self):
            return Shape({(-x, y): floor for (x, y), floor in self.shape.items()},
                         [(-x, y) for (x, y) in self.remove])

        def match(self, main_pos: Tuple, positions: List[Tuple]) -> bool:
            for pos, floor in self.shape.items():
                cpos = utils.tuple_add(pos, main_pos)
                if floor and cpos not in positions:
                    return False
                elif not floor and cpos in positions:
                    return False
            return True

    single_hallway = Shape(
        {(0, 0): 1, (-1, 0): 1, (1, 0): 1, (0, -1): 0, (0, 1): 0},
        [(0, 0)],
    )
    double_hallway = Shape(
        {(0, 0): 1, (1, 0): 1, (0, -1): 1, (0, 1): 1, (-1, 0): 0, (2, 0): 0},
        [(0, 0), (1, 0)],
    )
    merged_single = Shape(
        {(0, 0): 1, (1, 0): 1, (1, 1): 0, (0, -1): 0, (0, 1): 1, (1, -1): 1},
        [(0, 0), (1, 0)])
    merged_double = Shape(
        {(0, 0): 1, (1, 0): 1, (0, 1): 1, (1, 1): 1, (-1, 0): 0, (2, 1): 0},
        [(0, 0), (1, 1)])

    bad_shapes = [
        single_hallway, single_hallway.rotate(1),
        double_hallway, double_hallway.rotate(1),
        double_hallway.rotate(2), double_hallway.rotate(3),
        merged_single, merged_single.rotate(1),
        merged_single.flip_horiz(), merged_single.flip_horiz().rotate(1),
        merged_double, merged_double.rotate(1),
        merged_double.flip_horiz(), merged_double.flip_horiz().rotate(1),
    ]

    # Basically, find areas where you never have to pass through 
    # a 2 or 1 tile wide hallway to reach the rest of the area
    for pos in floors:
        for shape in bad_shapes:
            if shape.match(pos, floors):
                for remove_me in shape.remove:
                    actual_pos = utils.tuple_add(pos, remove_me)
                    if actual_pos in positions:
                        positions.remove(actual_pos)

    # Flood fill
    room_positions = positions.copy()
    while positions:
        pos = positions.pop()
        room = sorted(list(flood_fill(lambda x, y: True, room_positions, pos)))
        if len(room) > 2:
            rooms.append(room)
            for pos in room:
                if pos in positions:
                    positions.remove(pos)

    return [Area(tiles) for tiles in rooms]

def place_pillar(tilemap: DungeonTileMap, area: Area, pos: Tuple[int, int], reverse_x: bool = False, reverse_y: bool = False) -> None:
    min_x = min(tile[0] for tile in area.tiles)
    max_x = max(tile[0] for tile in area.tiles)
    min_y = min(tile[1] for tile in area.tiles)
    max_y = max(tile[1] for tile in area.tiles)
    offset_x = max_x - pos[0] if reverse_x else min_x + pos[0]
    offset_y = max_y - pos[1] if reverse_y else min_y + pos[1]
    terrain = tilemap.get_terrain((offset_x, offset_y))
    south_terrain = tilemap.get_terrain((offset_x, offset_y + 1))
    if terrain == 'Floor' and south_terrain in ('Floor', None):
        tilemap.set_terrain(offset_x, offset_y, 'Pillar')

def add_pillars(tilemap: DungeonTileMap, final_areas: List[Area]):
    for area in final_areas:
        # Wider
        if area.width > area.height:
            if area.height == 3 or area.height == 5:
                for x in range(1, area.width//2, 3):
                    place_pillar(tilemap, area, (x, area.height//2))
                    place_pillar(tilemap, area, (x, area.height//2), reverse_x=True)
            elif area.height >= 6:
                for x in range(1, area.width//2, 3):
                    place_pillar(tilemap, area, (x, 1))
                    place_pillar(tilemap, area, (x, 1), reverse_x=True)
                for x in range(1, area.width//2, 3):
                    place_pillar(tilemap, area, (x, 1), reverse_y=True)
                    place_pillar(tilemap, area, (x, 1), reverse_x=True, reverse_y=True)
        # Taller 
        elif area.height >= area.width:
            if area.width == 3 or area.width == 5:
                for y in range(1, area.height//2, 3):
                    place_pillar(tilemap, area, (area.width//2, y))
                    place_pillar(tilemap, area, (area.width//2, y), reverse_y=True)
            elif area.width >= 6:
                for y in range(1, area.height//2, 3):
                    place_pillar(tilemap, area, (1, y))
                    place_pillar(tilemap, area, (1, y), reverse_y=True)
                for y in range(1, area.height//2, 3):
                    place_pillar(tilemap, area, (1, y), reverse_x=True)
                    place_pillar(tilemap, area, (1, y), reverse_x=True, reverse_y=True)

def convert_to_floor_2(tilemap: DungeonTileMap) -> None:
    for pos in tilemap.terrain_grid.keys():
        if tilemap.get_layer(pos) == 2:
            if tilemap.get_terrain(pos) == 'Floor':
                tilemap.set_terrain(*pos, 'Floor2')
            if tilemap.get_terrain(pos) == 'Pillar':
                tilemap.set_terrain(*pos, 'Pillar2')

def generate_dungeon(theme: str, size: Tuple[int, int], seed=-1):
    print("Theme: %s" % theme)
    random.seed(seed)
    width, height = size

    # Set up magic numbers
    avg_size = 4.5

    # Keep trying until we get a good one
    while True:
        print("Start Process!")
        tilemap = DungeonTileMap(width, height)
        tilemap.reset_grid('Floor')
        
        # Create several rooms and place them in the map
        # Some of them will be level 1 and some level 2
        # A room needs to have walls and a floor
        room_prefabs: List[RoomPrefab] = []
        rooms: List[Room] = []
        while len(rooms) < 4:
            new_room_prefab: RoomPrefab = create_room(avg_size, width, height)
            if not any(room_prefab.overlaps(new_room_prefab) for room_prefab in room_prefabs):
                room_prefabs.append(new_room_prefab)
                new_room = Room.from_prefab(new_room_prefab, tilemap)
                rooms.append(new_room)
                idx = len(rooms) - 1
                # layer = idx % 2 + 1
                layer = 2
                for tile in new_room.tiles:
                    tilemap.set_layer(*tile, layer)
                if layer == 2:
                    for tile in new_room.wall_tiles:
                        tilemap.set_layer(*tile, layer)
            else:
                continue  # Overlaps, so ignore this

        # Place walls and floors on the tilemap
        for room in rooms:
            for tile in room.tiles:
                tilemap.terrain_grid[tile] = 'Floor'
            for tile in room.wall_tiles:
                tilemap.terrain_grid[tile] = 'Wall'
        tilemap.print_grid()
        tilemap.print_layer_grid()

        # Find connections
        floor_tiles = get_floor_positions(tilemap)
        new_floors = find_adjacency_connections(tilemap, rooms, set(floor_tiles))
        # Place connections onto grid
        place_connections_onto_grid(tilemap, new_floors)

        print("Tilemap Grid")
        tilemap.print_grid()

        print("2 tile walls")
        # Make sure there's room for 2-tile tall walls in layer 1 rooms
        for pos in tilemap.terrain_grid.keys():
            layer = tilemap.get_layer(pos)
            if layer == 1:
                # Remove the top tiles of the room
                north = tilemap.get_terrain((pos[0], pos[1] - 1))
                north2 = tilemap.get_terrain((pos[0], pos[1] - 2))
                if north == 'Wall' and north2 != 'Wall':
                    tilemap.set_terrain(*pos, 'Wall')

        tilemap.print_grid()
        print("remove 1 way alcoves")
        fill_in_one_way_alcoves(tilemap)
        tilemap.print_grid()

        # Check number of rooms
        floor_tiles = get_floor_positions(tilemap)
        print(len(floor_tiles))
        areas: List[Area] = find_new_areas(tilemap, floor_tiles.copy())
        print("Number of Areas", len(areas))
        print_rooms(areas)
        if len(areas) != 1:
            continue

        final_areas: List[Area] = find_all_areas(floor_tiles)
        print_rooms(final_areas)

        # Add Pillars where appropriate
        add_pillars(tilemap, final_areas)

        convert_to_floor_2(tilemap)

        tilemap.print_grid()

        # Done!
        break

    return tilemap
