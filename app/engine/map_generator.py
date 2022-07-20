from dataclasses import dataclass

from typing import Dict, List, Tuple

from app.constants import TILEWIDTH, TILEHEIGHT

from app.dungeon_maker import dungeon_maker, terrain_maker

from app.engine.objects.tilemap import TileMapObject

from app.engine import action, engine, random_groups
from app.events import regions
from app.engine.game_state import game

from app.utilities import utils
from app.utilities.algorithms.interpolation import lerp

import logging

def determine_sprite(pos: tuple, terrain, tilemap):
    def _push_to_tilemap(pos: tuple, new_coords: tuple):
        """
        pos is in tile space (8x8)
        """

        new_coord = terrain_maker.random_choice(new_coords, pos)
        tilemap.tile_grid[pos] = new_coord

    new_coords1, new_coords2, new_coords3, new_coords4 = \
        terrain.determine_sprite_coords(tilemap, pos)

    _push_to_tilemap((pos[0] * 2, pos[1] * 2), new_coords1)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2), new_coords2)
    _push_to_tilemap((pos[0] * 2 + 1, pos[1] * 2 + 1), new_coords3)
    _push_to_tilemap((pos[0] * 2, pos[1] * 2 + 1), new_coords4)

def get_floor_positions():
    valid_positions = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
    return sorted([pos for pos in valid_positions if game.movement.check_simple_traversable(pos)])

def find_all_rooms(positions: List[Tuple]) -> List[List[Tuple]]:
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
        room = sorted(list(dungeon_maker.flood_fill(lambda x, y: True, room_positions, pos)))
        if len(room) > 2:
            rooms.append(room)
            for pos in room:
                if pos in positions:
                    positions.remove(pos)

    # Print rooms
    all_positions = {}
    for idx, room in enumerate(rooms):
        all_positions.update({pos: idx for pos in room})
    width = max(pos[0] for pos in all_positions.keys()) + 1
    height = max(pos[1] for pos in all_positions.keys()) + 1
    for y in range(width):
        print("%02d " % y, end='')
        for x in range(height):
            if (x, y) in all_positions:
                print("%d" % all_positions[(x, y)], end='')
            else:
                print(" ", end='')
        print("\n", end='')

    return rooms

def find_room_with(rooms: List[List[Tuple]], position: Tuple) -> List[Tuple]:
    for room in rooms:
        if position in room:
            return room
    # We couldn't find this position in any of the rooms, try and find closest position
    counter = 1
    while counter < 4:
        for room in rooms:
            for pos in room:
                if utils.calculate_distance(pos, position) <= counter:
                    return room
        counter += 1

    logging.error("Could not find room close to position %s", position)
    return None

def generate_map(theme=None, enemy_type=None, size=None) -> None:
    theme = theme or 'default'
    enemy_type = [enemy_type] or ['Soldier']
    size = size or (20, 20)
    # Generate map prefab (called dungeon)
    seed = game.game_vars.get('_random_seed', -1)
    dungeon = dungeon_maker.generate_dungeon(theme, size, seed)
    DB_terrain = terrain_maker.get_terrain(theme)

    # Need to create an image for the base layer
    im_width, im_height = dungeon.width * TILEWIDTH, dungeon.height * TILEHEIGHT
    surf = engine.create_surface((im_width, im_height))
    engine.fill(surf, (0, 0, 0))

    processed_nids = set()
    for pos in dungeon.terrain_grid:
        terrain_nid = dungeon.get_terrain(pos)
        terrain = DB_terrain.get(terrain_nid)
        if terrain_nid not in processed_nids:
            terrain.single_process(dungeon)
            processed_nids.add(terrain_nid)
        determine_sprite(pos, terrain, dungeon)

    # Draw the tile grid
    for pos, tile_coord in dungeon.tile_grid.items():
        terrain_pos = (pos[0] // 2, pos[1] // 2)
        terrain_nid = dungeon.get_terrain(terrain_pos)
        if not terrain_nid:
            continue
        terrain = DB_terrain.get(terrain_nid)
        pix = terrain.get_image(tile_coord)
        surf.blit(pix, (pos[0] * TILEWIDTH//2, pos[1] * TILEHEIGHT//2))

    # Now we have the surface to use as a real tilemap
    level_nid = str(random_groups.completed_chapters())
    tilemap = TileMapObject.build_from_scratch(level_nid, dungeon, surf)
    # Now we have a complete tilemap
    # Lets build a level
    game.build_level_from_scratch(level_nid, tilemap)

    # Choose a starting room and an ending/boss room
    valid_positions = get_floor_positions()
    southwest_corner = sorted(valid_positions, key=lambda x: x[0] + -x[1])[0]
    northeast_corner = sorted(valid_positions, key=lambda x: -x[0] + x[1])[0]
    rooms: List[List[Tuple]] = find_all_rooms(valid_positions)
    starting_room_tiles: List[Tuple] = find_room_with(rooms, southwest_corner)
    ending_room_tiles: List[Tuple] = find_room_with(rooms, northeast_corner)

    # Create formations
    num_formations = int(utils.clamp(lerp(6, 12, random_groups.completed_chapters() / (random_groups.LAST_CHAPTER - 1)), 6, 12))
    # Starting from southwest corner of room
    tiles = sorted(starting_room_tiles, key=lambda x: x[0] + -x[1])
    formation_tiles = tiles[:num_formations]
    for idx, tile in enumerate(formation_tiles):
        formation_region = regions.Region('Formation%02d' % idx)
        formation_region.region_type = regions.RegionType.FORMATION
        formation_region.position = tile
        formation_region.size = (1, 1)
        game.register_region(formation_region)
        action.do(action.AddRegion(formation_region))

    # Figure out basic starting position
    start_pos_x = sum(form[0] for form in formation_tiles) / len(formation_tiles)
    start_pos_y = sum(form[1] for form in formation_tiles) / len(formation_tiles)
    start_pos = (start_pos_x, start_pos_y)

    # Figure out boss position
    # Find northeast most position
    boss_pos = sorted(ending_room_tiles, key=lambda x: (-x[0] + x[1]))[0]

    # Populate rooms with enemies
    group_data = {'valid_tags': enemy_type}
    from app.engine import static_random
    logging.debug(static_random.get_other_random_state())
    for idx, room in enumerate(rooms):
        if room is starting_room_tiles:
            logging.debug("Starting")
            valid_tiles = [tile for tile in room if 
                           all(utils.calculate_distance(tile, form_tile) > 3 for form_tile in formation_tiles)]
            random_groups.build_group('%d' % idx, group_data, valid_tiles)
            logging.debug(static_random.get_other_random_state())

        elif room is ending_room_tiles:
            logging.debug("Ending")
            random_groups.build_group('Boss', group_data, [boss_pos])
            logging.debug(static_random.get_other_random_state())
            random_groups.build_group('%d' % idx, group_data, room)
            logging.debug(static_random.get_other_random_state())

        else:
            logging.debug("Regular")
            random_groups.build_group('%d' % idx, group_data, room)
            logging.debug(static_random.get_other_random_state())

    logging.debug(static_random.get_other_random_state())

    # Generate grave tree regions
    ### TODO: Figure out a good way to place these.
    num_grave_trees = int(lerp(3, 6, random_groups.completed_chapters() / random_groups.LAST_CHAPTER))
    valid_positions = get_floor_positions()
    valid_positions = [pos for pos in valid_positions if all(utils.calculate_distance(pos, form_tile) > 8 for form_tile in formation_tiles)]
    # Choose X random positions
    counter = num_grave_trees
    while counter > 0 and valid_positions:
        counter -= 1
        pos = game.get_random_choice(valid_positions)
        valid_positions.remove(pos)
        distance = utils.calculate_distance(start_pos, pos)
        grave_region = regions.Region('Grave%d' % counter)
        grave_region.region_type = regions.RegionType.TIME
        grave_region.position = pos
        grave_region.size = (1, 1)
        grave_region.sub_nid = int(distance / 5) + 1
        game.register_region(grave_region)
        action.do(action.AddRegion(grave_region))
    logging.debug(static_random.get_other_random_state())

    print("Done!")
