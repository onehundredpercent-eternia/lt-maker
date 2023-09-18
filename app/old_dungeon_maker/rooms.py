from dataclasses import dataclass
from typing import List, Set, Tuple

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
