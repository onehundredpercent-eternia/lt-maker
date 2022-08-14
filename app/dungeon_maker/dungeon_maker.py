import math
import random
import itertools
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple

from app.utilities import utils

class DungeonTileMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.terrain_grid: Dict[Tuple[int, int], str] = {}
        self.tile_grid = {}
        self.layer_grid: Dict[Tuple[int, int], int] = {}

    def get_terrain(self, pos: Tuple[int, int]) -> str:
        return self.terrain_grid.get(pos, None)

    def get_true_terrain_grid(self) -> Dict[Tuple[int, int], str]:
        conversion_dict = \
            {'Floor2': 'Floor',
             'StairsUpDown': 'Stairs',
             'StairsLeft': 'Stairs',
             'StairsRight': 'Stairs',
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
                elif terrain == 'Pillar':
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
    x: float = 0
    y: float = 0
    width: int = 0  # Width of Floor
    height: int = 0  # Height of Floor

def random_point_in_circle(radius: float) -> tuple:
    t = 2 * math.pi * random.random()
    u = random.random() + random.random()
    r = 2 - u if u > 1 else u
    return radius * r * math.cos(t), radius * r * math.sin(t)

def get_rooms(avg_size=4.5, num_rooms=20, offset=None) -> list:
    offset = offset or (10, 10)
    radius = 1
    rooms = []
    for _ in range(num_rooms):
        # Random size
        rwidth = random.normalvariate(mu=avg_size, sigma=1)
        # Generally square
        rheight = random.normalvariate(mu=rwidth, sigma=0.75)
        if rwidth <= 0 or rheight <= 0:
            continue
        # choose a random point to place the room
        x, y = random_point_in_circle(radius)
        rooms.append(RoomPrefab(x + rwidth//2 + offset[0], y + rheight//2 + offset[1], round(rwidth), round(rheight)))
    return rooms

def room_overlaps(a: RoomPrefab, b: RoomPrefab) -> bool:
    dx = a.x - b.x
    px = (a.width/2 + b.width/2) - abs(dx)
    if px <= 0:
        return False

    dy = a.y - b.y
    py = (a.height/2 + b.height/2) - abs(dy)
    if py <= 0:
        return False
    return True

def separation_steering(rooms: List[RoomPrefab]) -> List[RoomPrefab]:
    overlap = True
    counter = 0
    while overlap and counter < 10000:
        counter += 1
        overlap = False
        velocities = {room: [0, 0] for room in rooms}
        for room in rooms:
            neighbor_count = 0
            # Find overlapping rooms
            for other_room in rooms:
                if room is other_room:
                    continue
                if room_overlaps(room, other_room):
                    velocities[room][0] += other_room.x - room.x
                    velocities[room][1] += other_room.y - room.y
                    neighbor_count += 1
            if neighbor_count > 0:
                # Negate to move away
                velocities[room][0] *= -1
                velocities[room][1] *= -1
                # Mark that we are still overlapping
                overlap = True
        # Actually move
        for room in rooms:
            x_vel, y_vel = utils.normalize(velocities[room])
            room.x += x_vel * 0.25
            room.y += y_vel * 0.25
    return rooms

def get_room_tiles(tilemap: DungeonTileMap, rooms: List[RoomPrefab]) -> Set[tuple]:
    # Now put rooms on grid
    room_tiles = set()
    for room in rooms:
        left_width = room.width//2
        right_width = room.width - left_width
        top_height = room.height//2
        bottom_height = room.height - top_height
        for i in range(int(room.x) - left_width, int(room.x) + right_width):
            for j in range(int(room.y) - top_height, int(room.y) + bottom_height):
                room_tiles.add((i, j))
    room_tiles = {tile for tile in room_tiles if tilemap.check_bounds(*tile)}
    return room_tiles

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

@dataclass(eq=False)
class Room:
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

    def get_center_tiles(self) -> List[tuple]:
        center_tiles = []
        for tile in self.tiles:
            if all(adj in self.tiles for adj in utils.get_cardinal_positions(tile)):
                center_tiles.append(tile)
        return center_tiles
    
def find_new_rooms(tilemap: DungeonTileMap, room_tiles: Set[Tuple]) -> List[Room]:
    rooms = []
    while room_tiles:
        tile = next(iter(room_tiles))
        extant_tiles = flood_fill(tilemap.check_bounds, room_tiles, tile)
        if extant_tiles:
            room = Room(extant_tiles)
            rooms.append(room)
            for tile in extant_tiles:
                room_tiles.remove(tile)
    return rooms

def combine_rooms(tilemap: DungeonTileMap, rooms: List[Room], all_room_tiles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    # Find walls between rooms
    new_floors = set()
    all_checked_walls = set()
    for room, other_room in itertools.combinations(rooms, 2):
        for tile in room.tiles:
            for direction in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                next_tile = tile[0] + direction[0], tile[1] + direction[1]
                next2_tile = tile[0] + direction[0] * 2, tile[1] + direction[1] * 2
                if tilemap.check_bounds(*next_tile) and tilemap.check_bounds(*next2_tile) and \
                        next_tile not in all_room_tiles and next2_tile in other_room.tiles and \
                        next_tile not in all_checked_walls:
                    wall = [next_tile]
                    # Find rest of wall
                    if abs(direction[0]) == 1:
                        # Go up 
                        while True:
                            next_tile = next_tile[0], next_tile[1] - 1
                            left_tile = next_tile[0] - 1, next_tile[1]
                            right_tile = next_tile[0] + 1, next_tile[1]
                            if next_tile not in all_room_tiles and left_tile in all_room_tiles and right_tile in all_room_tiles:
                                wall.append(next_tile)
                            else:
                                break                                    
                        # Go down
                        while True:
                            next_tile = next_tile[0], next_tile[1] + 1
                            left_tile = next_tile[0] - 1, next_tile[1]
                            right_tile = next_tile[0] + 1, next_tile[1]
                            if next_tile not in all_room_tiles and left_tile in all_room_tiles and right_tile in all_room_tiles:
                                wall.append(next_tile)
                            else:
                                break
                    else:
                        # Go left 
                        while True:
                            next_tile = next_tile[0] - 1, next_tile[1]
                            up_tile = next_tile[0], next_tile[1] - 1
                            down_tile = next_tile[0], next_tile[1] + 1
                            if next_tile not in all_room_tiles and up_tile in all_room_tiles and down_tile in all_room_tiles:
                                wall.append(next_tile)
                            else:
                                break                                    
                        # Go right
                        while True:
                            next_tile = next_tile[0] + 1, next_tile[1]
                            up_tile = next_tile[0], next_tile[1] - 1
                            down_tile = next_tile[0], next_tile[1] + 1
                            if next_tile not in all_room_tiles and up_tile in all_room_tiles and down_tile in all_room_tiles:
                                wall.append(next_tile)
                            else:
                                break                                    
                    # Cut opening in middle of wall
                    wall = sorted(list(set(wall)))
                    if len(wall) % 2:  # Odd
                        # If wall is odd, place opening between them
                        cut = wall[len(wall)//2]
                        new_floors.add(cut)
                    else:  # Even
                        # If wall is even, place two-opening between them
                        cut1 = wall[len(wall)//2 - 1]
                        cut2 = wall[len(wall)//2]
                        new_floors.add(cut1)
                        new_floors.add(cut2)
                    all_checked_walls |= set(wall)
    return new_floors

def get_floor_positions(tilemap: DungeonTileMap) -> List[Tuple]:
    valid_positions = [(x, y) for x in range(tilemap.width) for y in range(tilemap.height)]
    return sorted([pos for pos in valid_positions if tilemap.get_terrain(pos) in ('Floor', 'Pillar', 'StairsUpDown', 'StairsLeft', 'StairsRight')])

def find_all_rooms(positions: List[Tuple]) -> List[Room]:
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

    return [Room(tiles) for tiles in rooms]

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
            elif east != west:
                print(east, west)
                if west > east:
                    tilemap.terrain_grid[connection] = 'StairsLeft'
                elif east > west:
                    tilemap.terrain_grid[connection] = 'StairsRight'
            else:
                print("Could not determine which direction the stairs should face %s" % connection)
        else:
            print("No nearby floor tiles? %s" % connection)

def place_pillar(tilemap: DungeonTileMap, room: Room, pos: Tuple[int, int], reverse_x: bool = False, reverse_y: bool = False) -> None:
    min_x = min(tile[0] for tile in room.tiles)
    max_x = max(tile[0] for tile in room.tiles)
    min_y = min(tile[1] for tile in room.tiles)
    max_y = max(tile[1] for tile in room.tiles)
    offset_x = max_x - pos[0] if reverse_x else min_x + pos[0]
    offset_y = max_y - pos[1] if reverse_y else min_y + pos[1]
    terrain = tilemap.get_terrain((offset_x, offset_y))
    south_terrain = tilemap.get_terrain((offset_x, offset_y + 1))
    if terrain == 'Floor' and south_terrain in ('Floor', None):
        tilemap.set_terrain(offset_x, offset_y, 'Pillar')

def generate_dungeon(theme: str, size: Tuple[int, int], seed=-1):
    print("Theme: %s" % theme)
    random.seed(seed)
    width, height = size
    while True:
        print("Start Process!")
        tilemap = DungeonTileMap(width, height)
        tilemap.reset_grid('Wall')
        num_rooms = int(width * height / 20)
        rooms: List[RoomPrefab] = get_rooms(num_rooms=num_rooms, offset=(width/2, height/2))
        rooms: List[RoomPrefab] = separation_steering(rooms)
        room_tiles: Set[Tuple[int, int]] = get_room_tiles(tilemap, rooms)
        new_rooms: List[Room] = find_new_rooms(tilemap, room_tiles.copy())
        print("Initial Rooms")
        print_rooms(new_rooms)

        # Big areas of blankness get filled
        tilemap_tiles = {(x, y) for x in range(tilemap.width) for y in range(tilemap.height)}
        empty_tiles: Set[Tuple] = tilemap_tiles - room_tiles
        thin_empty_tiles = {tile for tile in empty_tiles if sum(adj in empty_tiles for adj in utils.get_cardinal_positions(tile)) <= 2}
        empty_tiles -= thin_empty_tiles
        empty_rooms: List[Room] = find_new_rooms(tilemap, empty_tiles.copy())
        for room in empty_rooms:
            if room.size >= 11:
                center_tiles: List[Tuple[int, int]] = room.get_center_tiles()
                new_room = Room(center_tiles)
                new_rooms.append(new_room)
                for tile in new_room.tiles:
                    room_tiles.add(tile)
        print("Final Rooms")
        print_rooms(new_rooms)

        # Assign each room a random layer (1 or 2)
        room_to_layer = {}
        for idx, room in enumerate(new_rooms):
            layer = idx % 2 + 1
            # layer = 1
            room_to_layer[room] = layer
            for tile in room.tiles:
                tilemap.set_layer(*tile, layer)

        # Need to recalculate what tiles actually belong in the room after making room for 2-tall walls
        # Combine Rooms
        connections: Set[Tuple[int, int]] = combine_rooms(tilemap, new_rooms, room_tiles)        

        # Place rooms onto grid
        for room in new_rooms:
            for tile in room.tiles:
                tilemap.terrain_grid[tile] = 'Floor'

        # Place connections onto grid
        place_connections_onto_grid(tilemap, connections)
        print("Tilemap Grid")
        tilemap.print_grid()

        # Make sure there's room for 2-tile tall walls in layer 1 rooms
        for pos in tilemap.terrain_grid.keys():
            layer = tilemap.get_layer(pos)
            if layer == 1:
                # Remove the top tiles of the room
                north = tilemap.get_terrain((pos[0], pos[1] - 1))
                north2 = tilemap.get_terrain((pos[0], pos[1] - 2))
                if north == 'Wall' and north2 != 'Wall':
                    tilemap.set_terrain(*pos, 'Wall')

        # Fill in alcoves
        for pos in tilemap.terrain_grid.keys():
            north, east, south, west = tilemap.get_cardinal_terrain(pos)
            if sum([north == 'Wall', east == 'Wall', south == 'Wall', west == 'Wall']) >= 3:
                tilemap.set_terrain(*pos, 'Wall')

        # Check number of rooms
        floor_tiles = get_floor_positions(tilemap)
        print(len(floor_tiles))
        rooms: List[Room] = find_new_rooms(tilemap, floor_tiles.copy())
        print("Number of Rooms", len(rooms))
        if len(rooms) != 1:
            continue
        print_rooms(rooms)

        final_rooms: List[Room] = find_all_rooms(floor_tiles)
        print_rooms(final_rooms)

        # Add Pillars where appropriate
        for room in final_rooms:
            # Wider
            if room.width > room.height:
                if room.height == 3 or room.height == 5:
                    for x in range(1, room.width//2, 3):
                        place_pillar(tilemap, room, (x, room.height//2))
                        place_pillar(tilemap, room, (x, room.height//2), reverse_x=True)
                elif room.height >= 6:
                    for x in range(1, room.width//2, 3):
                        place_pillar(tilemap, room, (x, 1))
                        place_pillar(tilemap, room, (x, 1), reverse_x=True)
                    for x in range(1, room.width//2, 3):
                        place_pillar(tilemap, room, (x, 1), reverse_y=True)
                        place_pillar(tilemap, room, (x, 1), reverse_x=True, reverse_y=True)
            # Taller 
            elif room.height >= room.width:
                if room.width == 3 or room.width == 5:
                    for y in range(1, room.height//2, 3):
                        place_pillar(tilemap, room, (room.width//2, y))
                        place_pillar(tilemap, room, (room.width//2, y), reverse_y=True)
                elif room.width >= 6:
                    for y in range(1, room.height//2, 3):
                        place_pillar(tilemap, room, (1, y))
                        place_pillar(tilemap, room, (1, y), reverse_y=True)
                    for y in range(1, room.height//2, 3):
                        place_pillar(tilemap, room, (1, y), reverse_x=True)
                        place_pillar(tilemap, room, (1, y), reverse_x=True, reverse_y=True)

        # Convert any floors on layer 2 to floor2
        for pos in tilemap.terrain_grid.keys():
            if tilemap.get_terrain(pos) == 'Floor' and tilemap.get_layer(pos) == 2:
                tilemap.set_terrain(*pos, 'Floor2')

        tilemap.print_grid()

        # Done!
        break

    return tilemap, final_rooms

# to test
# python -m app.dungeon_maker.dungeon_maker
if __name__ == '__main__':
    tilemap, rooms = generate_dungeon('Soldier', (20, 20), 0)
    tilemap.print_grid()
