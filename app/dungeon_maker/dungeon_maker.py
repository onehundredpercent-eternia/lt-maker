import math
import random
import itertools
from enum import Enum
from dataclasses import dataclass

class TileType(Enum):
    FLOOR = 'Floor'
    WALL = 'Wall'
    PILLAR = 'Pillar'
    STAIR = 'Stair'

map_size = 20, 20
width, height = map_size
tilemap_grid = [TileType.FLOOR for _ in range(width * height)]
# tilemap_grid = [random.choice([TileType.FLOOR, TileType.WALL]) for _ in range(width * height)]

def set_grid(x: int, y: int, tiletype: TileType):
    tilemap_grid[y * width + x] = tiletype

def reset_grid(tiletype=TileType.FLOOR):
    for idx, _ in enumerate(tilemap_grid):
        tilemap_grid[idx] = tiletype

def get_from_grid(x: int, y: int) -> TileType:
    return tilemap_grid[y * width + x]

def check_bounds(x: int, y: int) -> bool:
    return 0 <= x < width and 0 <= y < height

def place_rooms():
    room_percentage = 0.33
    avg_size = 4.5
    num_rooms = int(room_percentage * width * height / (avg_size * avg_size))
    rooms = []
    for _ in range(num_rooms):
        # Random size
        rwidth = random.normalvariate(mu=avg_size, sigma=1)
        # Generally square
        rheight = random.normalvariate(mu=rwidth, sigma=0.5)
        # choose a random point to place the room
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        rooms.append((x, y, int(rwidth), int(rheight)))

@dataclass(eq=False)
class Room:
    x: float = 0
    y: float = 0
    width: int = 0  # Width of Floor
    height: int = 0  # Height of Floor

def random_point_in_circle(radius: float) -> tuple:
    t = 2 * math.pi * random.random()
    u = random.random() + random.random()
    r = 2 - u if u > 1 else u
    return radius * r * math.cos(t), radius * r * math.sin(t)

def get_rooms() -> list:
    avg_size = 4.5
    num_rooms = 20
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
        rooms.append(Room(x + width//2, y + height//2, round(rwidth), round(rheight)))
    print(rooms)
    return rooms

def room_overlaps(a: Room, b: Room) -> bool:
    dx = a.x - b.x
    px = (a.width/2 + b.width/2) - abs(dx)
    if px <= 0:
        return False

    dy = a.y - b.y
    py = (a.height/2 + b.height/2) - abs(dy)
    if py <= 0:
        return False
    return True

def magnitude(vec) -> float:
    return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1])

def normalize(vec):
    if vec[0] != 0 or vec[1] != 0:
        mag = magnitude(vec)
        return vec[0] / mag, vec[1] / mag
    return vec[0], vec[1]

def separation_steering(rooms: list) -> list:
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
            x_vel, y_vel = normalize(velocities[room])
            room.x += x_vel * 0.25
            room.y += y_vel * 0.25
    return rooms

def get_room_tiles(rooms: list) -> set:
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
    room_tiles = {tile for tile in room_tiles if check_bounds(*tile)}
    return room_tiles

def flood_fill(room_tiles: set, pos: tuple) -> set:
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

def find_new_rooms(room_tiles: set) -> list:
    rooms = []
    while room_tiles:
        tile = next(iter(room_tiles))
        room = flood_fill(room_tiles, tile)
        if room:
            rooms.append(room)
            for tile in room:
                room_tiles.remove(tile)
    return rooms

def place_rooms_on_grid(rooms: list, tiletype=TileType.FLOOR):
    for room in rooms:
        for tile in room:
            set_grid(*tile, tiletype)

def get_character(x, y):
    e = get_from_grid(x, y)
    if e == TileType.FLOOR:
        return '_'
    elif e == TileType.WALL:
        return '#'
    elif e == TileType.PILLAR:
        return '$'
    elif e == TileType.STAIR:
        return 'S'

def print_grid():
    for y in range(height):
        for x in range(width):
            cell_char = get_character(x, y)
            print(cell_char, end="")
        print("\n", end="")

def combine_rooms(rooms, all_room_tiles):
    # Find walls between rooms
    new_floors = set()
    all_checked_walls = set()
    for room_tiles, other_room_tiles in itertools.combinations(rooms, 2):
        for tile in room_tiles:
            for direction in [(0, -1), (-1, 0), (1, 0), (0, 1)]:
                next_tile = tile[0] + direction[0], tile[1] + direction[1]
                next2_tile = tile[0] + direction[0] * 2, tile[1] + direction[1] * 2
                if check_bounds(*next_tile) and check_bounds(*next2_tile) and \
                        next_tile not in all_room_tiles and next2_tile in other_room_tiles and \
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

reset_grid(TileType.WALL)
rooms = get_rooms()
rooms = separation_steering(rooms)
room_tiles = get_room_tiles(rooms)
new_rooms = find_new_rooms(room_tiles.copy())
print(len(new_rooms))
connections = combine_rooms(new_rooms, room_tiles)
place_rooms_on_grid(new_rooms)
place_rooms_on_grid([connections], TileType.STAIR)
print_grid()
