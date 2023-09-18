import random
from dataclasses import dataclass
from typing import List, Set, Dict, Tuple

from app.utilities import utils
from app.utilities.direction import Direction
from app.utilities.algorithms.interpolation import lerp

from app.engine import pathfinding, node
from app.dungeon_maker.dungeon_tilemap import DungeonTileMap
from app.dungeon_maker.rooms import Room, RoomPrefab, Area, print_rooms
from app.dungeon_maker.meandering_path_creator import MeanderingPathCreator

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

def create_random_size(avg_size: float) -> Tuple[int, int]:
    while True:
        # Random size
        rwidth = int(round(random.normalvariate(mu=avg_size, sigma=1)))
        # Generally square
        rheight = int(round(random.normalvariate(mu=rwidth, sigma=0.75)))
        if rwidth <= 0 or rheight <= 0:
            continue
        return rwidth, rheight

def create_room(avg_size: float, map_width: int, map_height: int):
    rwidth, rheight = create_random_size(avg_size)    
    # choose a random point to place the room
    center = random.randrange(0, map_width * map_height)
    x, y = center % map_width, center // map_width
    x -= rwidth//2
    y -= rheight//2
    new_room = RoomPrefab(x, y, rwidth, rheight)
    return new_room

def find_adjacency_connections(tilemap: DungeonTileMap, rooms: List[Room], all_room_tiles: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    print("Find connections")
    # Find walls between rooms
    new_floors = set()
    all_checked_walls = set()
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    for room in rooms:
        print(room)
        for idx, wall in enumerate(room.get_walls(tilemap)):
            # Remove any walls that have already been processed
            wall = sorted(tile for tile in wall if tile not in all_checked_walls)
            direction = directions[idx]
            if len(wall) == 0:
                # No wall, just skip
                pass
            elif len(wall) % 2:  # odd
                # Remove center of wall
                idx = len(wall) // 2
                cut = wall[idx]
                new_floors.add(cut)
                next_cut = (cut[0] + direction[0], cut[1] + direction[1])
                if tilemap.get_terrain(next_cut) == 'Wall':
                    new_floors.add(next_cut)
            else:  # even
                # Remove center of wall
                idx = len(wall) // 2
                cut1 = wall[idx - 1]
                cut2 = wall[idx]
                new_floors.add(cut1)
                new_floors.add(cut2)
                for cut in [cut1, cut2]:
                    next_cut = (cut[0] + direction[0], cut[1] + direction[1])
                    if tilemap.get_terrain(next_cut) == 'Wall':
                        new_floors.add(next_cut)
            all_checked_walls |= set(wall)
    return new_floors

def place_connections_onto_grid(tilemap: DungeonTileMap, connections: Set[Tuple[int, int]]):
    for connection in connections:
        # Check layers of nearby positions
        north, east, south, west = tilemap.get_cardinal_layers(connection)
        nt, et, st, wt = tilemap.get_cardinal_terrain(connection)
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
            if north != south and north and south and nt != 'Wall' and st != 'Wall':
                tilemap.terrain_grid[connection] = 'StairsUpDown'
            elif east != west and east and west and et != 'Wall' and wt != 'Wall':
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

def create_2_tile_walls(tilemap: DungeonTileMap) -> None:
    for pos in tilemap.terrain_grid.keys():
        layer = tilemap.get_layer(pos)
        if layer == 1:
            # Remove the top tiles of the room
            north = tilemap.get_terrain((pos[0], pos[1] - 1))
            north2 = tilemap.get_terrain((pos[0], pos[1] - 2))
            if north == 'Wall' and north2 != 'Wall':
                tilemap.set_terrain(*pos, 'Wall')
                # Also fix anything that is now blocked
                left = (pos[0] - 1, pos[1])
                right = (pos[0] + 1, pos[1])
                if tilemap.get_terrain(left) in ('StairsLeft', 'StairsRight'):
                    tilemap.set_terrain(*left, 'Floor')
                elif tilemap.get_terrain(right) in ('StairsLeft', 'StairsRight'):
                    tilemap.set_terrain(*right, 'Floor')

def fill_large_empty_areas(tilemap: DungeonTileMap, old: str, new: str, layer_choice: List[int]) -> List[List[Tuple[int, int]]]:
    large_empty_size_room_limit = 11
    tiles = [pos for pos in tilemap.terrain_grid.keys() if tilemap.get_terrain(pos) == old]
    blobs = []
    while tiles:
        tile = tiles[-1]
        blob = flood_fill(tilemap.check_bounds, tiles, tile)
        blobs.append(blob)
        for b in blob:
            if b in tiles:
                tiles.remove(b)

    # Find where we can make new rooms
    new_rooms = []
    for blob in blobs:
        layer = random.choice(layer_choice)
        if len(blob) > large_empty_size_room_limit:
            room = []
            for tile in blob:
                north, east, south, west = tilemap.get_cardinal_terrain(tile)
                if (not north or north == old) and \
                        (not east or east == old) and \
                        (not south or south == old) and \
                        (not west or west == old):
                    room.append(tile)
            if room:
                new_rooms.append(room)

    # Now actually convert these to floors
    for room in new_rooms:
        for tile in room:
            tilemap.set_terrain(*tile, new)
            tilemap.set_layer(*tile, layer)

    return new_rooms

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
    theme = theme.lower()
    print("Theme: %s" % theme)
    random.seed(seed)

    # Keep trying until we get a good one
    while True:
        result =_generate_dungeon_process(theme, size, seed)
        if result:
            break

    tilemap, start_corner, end_corner = result
    return tilemap, start_corner, end_corner

def _generate_dungeon_process(theme: str, size: Tuple[int, int], seed: int):
    print("Start Process!")
    width, height = size
    # Set up magic numbers
    avg_size = 3.5
    num_rooms = 6

    tilemap = DungeonTileMap(width, height)
    start_corner, end_corner = None, None

    if theme == 'simple':
        """
        Essentially it draws a single meandering path from
        the start corner to the end corner
        Sometimes it draws smaller rooms that fit inside corners and such
        """

        tilemap.reset_grid('Wall')

        # Choose start and end corner randomly
        valid_directions = [Direction.NORTHWEST, Direction.NORTHEAST, Direction.SOUTHEAST, Direction.SOUTHWEST]
        start_corner = random.choice(valid_directions)
        valid_directions.remove(start_corner)
        end_corner = random.choice(valid_directions)
        valid_directions.remove(end_corner)
        print(start_corner, end_corner)
        
        # Find start and closest tile
        # Don't always pick the exact corner. Sometimes randomly pick other nearby tiles
        num_tiles_to_pick_from = 12  
        all_tiles = [(x, y) for x in range(width) for y in range(height)]
        starting_tiles = sorted(all_tiles, key=Direction.sorting_key(start_corner, (width, height)))
        start_tile = random.choice(starting_tiles[:num_tiles_to_pick_from])
        if Direction.opposite(start_corner) == end_corner:
            closest_corner = random.choice(valid_directions)
        else:
            closest_corner = Direction.closer_of(start_corner, valid_directions)
        ending_tiles = sorted(all_tiles, key=Direction.sorting_key(end_corner, (width, height)))
        end_tile = random.choice(ending_tiles[:num_tiles_to_pick_from])
        closest_tiles = sorted(all_tiles, key=Direction.sorting_key(closest_corner, (width, height)))
        closest_tile = random.choice(closest_tiles[:num_tiles_to_pick_from])
        
        # Draw path from start to closest corner
        # Create grid
        cells = []
        for x in range(width):
            for y in range(height):
                cells.append(node.Node(x, y, True, 1))
        pathfinder = pathfinding.AStar(start_tile, closest_tile, cells,
                                       (0, 0, width, height), height, None)
        can_move_through = lambda adj, team: True
        path1 = pathfinder.process(can_move_through)
        path1 = list(reversed(path1))
        print(path1, start_tile, closest_corner, closest_tile)

        # Decide on width for each tile
        tile_radius = 2
        tile_extend = tile_radius * 2

        # Draw meandering space filling path to end corner
        mpathfinder = MeanderingPathCreator(closest_tile, end_tile, tilemap.get_bounds(), tile_radius, seed=seed)
        # Keep out of the old path
        for tile in path1:
            mpathfinder.add_to_keep_out(tile)
        path2 = mpathfinder.process()
        print(path2, closest_tile, end_tile)
        path = path1[:-1] + path2
        print(path)
        # Now we have a path
        
        # Fill with floor and walls
        rooms = []
        for pos in path:
            x, y = pos[0] - tile_radius, pos[1] - tile_radius
            room_prefab = RoomPrefab(x, y, tile_extend + 1, tile_extend + 1)
            rooms.append(Room.from_prefab(room_prefab, tilemap))

        # Override all walls with floors
        for room in rooms:
            for tile in room.tiles:
                tilemap.terrain_grid[tile] = 'Floor'
                tilemap.set_layer(*tile, 1)
        tilemap.print_grid()

        # Fill large empty areas with floor 2
        new_rooms: List[List[Tuple[int, int]]] = \
            fill_large_empty_areas(tilemap, 'Wall', 'Floor', [2])
        print("Fill Large Empty Areas")
        tilemap.print_grid()
        # Draw doors to floor 2 areas
        connections = []
        print(new_rooms)
        for room in new_rooms:
            valid_tiles = [tile for tile in room if tilemap.get_terrain(tile) == 'Floor']
            selected_point = random.choice(valid_tiles)
            for direction in [Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST]:
                wall = False
                counter = 0
                done = False
                while not done and counter < 10:
                    counter += 1
                    # Get the next point
                    selected_point = Direction.next(direction, selected_point)
                    # Figure out what to do
                    if tilemap.get_terrain(selected_point) == 'Wall':
                        wall = True
                        connections.append(selected_point)
                    elif wall:
                        done = True

        place_connections_onto_grid(tilemap, connections)

    elif theme == 'noise':
        # Create several rooms and place them in the map
        # Some of them will be level 1 and some level 2
        # A room needs to have walls and a floor
        room_prefabs: List[RoomPrefab] = []
        rooms: List[Room] = []
        while len(rooms) < num_rooms:
            new_room_prefab: RoomPrefab = create_room(avg_size, width, height)
            if not any(room_prefab.overlaps(new_room_prefab) for room_prefab in room_prefabs):
                room_prefabs.append(new_room_prefab)
                new_room = Room.from_prefab(new_room_prefab, tilemap)
                rooms.append(new_room)
                # idx = len(rooms) - 1
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

    else:
        print("Theme %s is not supported" % theme)
        raise NotImplementedError

    # all themes use this section
    print("Tilemap Grid")
    tilemap.print_grid()

    print("2 tile walls")
    # Make sure there's room for 2-tile tall walls in layer 1 rooms
    create_2_tile_walls(tilemap)

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
        return None

    final_areas: List[Area] = find_all_areas(floor_tiles)
    print_rooms(final_areas)

    # Add Pillars where appropriate
    add_pillars(tilemap, final_areas)

    convert_to_floor_2(tilemap)

    tilemap.print_grid()

    # Done!
    return tilemap, start_corner, end_corner
