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

def get_floor_positions():
    valid_positions = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
    return sorted([pos for pos in valid_positions if game.movement.check_simple_traversable(pos)])

def build_tilemap(theme, map_palette, size, seed, level_nid):
    dungeon = dungeon_maker.generate_dungeon(theme, size, seed)
    DB_terrain = terrain_maker.get_terrain(map_palette)

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
        sprite = terrain.determine_sprite(dungeon, pos)
        dungeon.tile_grid[pos] = sprite

    # Draw the tile grid
    for pos, pix in dungeon.tile_grid.items():
        surf.blit(pix, (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT))

    # Now we have the surface to use as a real tilemap
    scratch_data = {
        'size': size,
        'theme': theme,
        'seed': seed,
        'map_palette': map_palette,
        'level_nid': level_nid,
    }
    tilemap = TileMapObject.build_from_scratch(level_nid, dungeon, surf, scratch_data)
    return tilemap

def generate_map(theme=None, map_palette=None, enemy_type=None, size=None) -> None:
    theme = theme or 'default'
    map_palette = map_palette or 'dungeon'
    enemy_type = [enemy_type] or ['Soldier']
    size = size or (20, 20)
    # Generate map prefab (called dungeon)
    seed = int(game.game_vars.get('_random_seed', -1) + (random_groups.completed_chapters() * 1024))

    level_nid = str(random_groups.completed_chapters())
    tilemap = build_tilemap(theme, map_palette, size, seed, level_nid)
    
    # Now we have a complete tilemap
    # Lets build a level
    game.build_level_from_scratch(level_nid, tilemap)

    game.tilemap.save_screenshot()

    # Find floor positions
    valid_positions = get_floor_positions()
    # Create formations
    num_formations = int(utils.clamp(lerp(6, 12, random_groups.completed_chapters() / (random_groups.LAST_CHAPTER - 1)), 6, 12))
    # Starting from southwest corner of room
    tiles = sorted(valid_positions, key=lambda x: x[0] + -x[1])
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
    boss_pos = sorted(valid_positions, key=lambda x: (-x[0] + x[1]))[0]

    # Populate rooms with enemies
    group_data = {'valid_tags': enemy_type}
    from app.engine import static_random
    static_random.set_other_random_state(seed)
    logging.debug(static_random.get_other_random_state())

    # Handle boss
    logging.debug("Place Boss")
    boss_data = {**group_data, **{'ai': 'Defend'}}
    random_groups.build_group('Boss', boss_data, [boss_pos])

    # Now place the rest of the units
    logging.debug("Place all enemy units")
    valid_tiles = [tile for tile in valid_positions if 
                   all(utils.calculate_distance(tile, form_tile) > 3 for form_tile in formation_tiles)]
    valid_tiles = list(sorted(valid_tiles))
    random_groups.build_groups(group_data, valid_tiles)

    # Generate grave tree regions
    num_grave_trees = int(lerp(3, 6, random_groups.completed_chapters() / random_groups.LAST_CHAPTER))
    valid_positions = get_floor_positions()
    # Don't be on top row (hard to see) or near player
    valid_positions = [pos for pos in valid_positions if 
                       pos[1] > 0 and 
                       all(utils.calculate_distance(pos, form_tile) > 8 for form_tile in formation_tiles)]
    valid_positions = sorted(valid_positions)
    # Choose X random positions
    counter = num_grave_trees
    while counter > 0 and valid_positions:
        counter -= 1
        pos = game.get_random_choice(valid_positions)
        # must be at least 8 tiles away
        for position in valid_positions[:]:
            if utils.calculate_distance(position, pos) <= 8:
                valid_positions.remove(position)
        distance = utils.calculate_distance(start_pos, pos)
        grave_region = regions.Region('Grave%d' % counter)
        grave_region.region_type = regions.RegionType.TIME
        grave_region.position = pos
        grave_region.size = (1, 1)
        grave_region.sub_nid = int(distance / 4) + 1
        game.register_region(grave_region)
        action.do(action.AddRegion(grave_region))
    logging.debug(static_random.get_other_random_state())

    game.map_view.save_screenshot()

    print("Done!")
