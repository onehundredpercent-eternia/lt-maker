from __future__ import annotations

from typing import TYPE_CHECKING

from app.utilities.typing import Pos

from app.dungeon_maker import encounter_generation, tilemap_generation, utilities
from app.engine import action, pathfinding

from app.engine.objects.region import RegionObject
from app.events import regions
from app.utilities import utils, str_utils

from app.utilities.typing import NID
from app.data.database.database import DB

if TYPE_CHECKING:
    from app.events.event import Event

def generate_dungeon(self: Event, chapter: NID, dungeon_theme: str, 
                     dungeon_palette: str, enemy_level: int, enemy_tag: NID,
                     seed: int = None, flags=None):
    if seed is None:
        seed = -1
    tilemap, dungeon_tilemap = \
        tilemap_generation.generate_map(dungeon_theme, dungeon_palette, seed)
    
    # Actually set up
    self.game.level.tilemap = tilemap
    self.game.set_up_game_board(self.game.level.tilemap)

    # Create the start and end regions
    start_pos = dungeon_tilemap.get_start_pos()

    start_region = RegionObject("Start", regions.RegionType.NORMAL)
    start_region.position = start_pos
    start_region.size = (1, 1)
    self.game.register_region(start_region)
    action.do(action.AddRegion(start_region))

    end_pos = dungeon_tilemap.get_end_pos()

    end_region = RegionObject("End", regions.RegionType.EVENT)
    end_region.position = end_pos
    end_region.size = (1, 1)
    end_region.sub_nid = "Descend"
    self.game.register_region(end_region)
    action.do(action.AddRegion(end_region))

    floor_level = str_utils.find_last_number(chapter)

    # Place encounters
    encounter_generation.place_encounters(
        self.game, dungeon_tilemap, tilemap, 
        enemy_level, floor_level, dungeon_theme, 
        enemy_tag, dungeon_palette, seed)

    # Can't use turnwheel to go any further back
    self.game.action_log.set_first_free_action()

def place_party(self: Event, position: Pos, party_size: int, flags=None):
    members = self.game.get_all_units_in_party()
    for i in range(party_size):
        unit = members[i]
        current_occupant = self.game.board.get_unit(position)
        if current_occupant:
            pos = self.game.target_system.get_closest_reachable_tile(unit, position)
            if not pos:
                self.logger.warning("Somehow wasn't able to find a nearby open tile")
                return None
        else:
            pos = position
        # Actually place unit
        action.do(action.ArriveOnMap(unit, position))

def place_graves(self: Event, start_position: Pos, num: int, seed: int = None, flags=None):
    DISTANCE = 10
    if seed is None:
        seed = -1

    grid = self.game.board.get_movement_grid(DB.mcost.unit_types[0])
    open_tiles = []
    for pos in utils.itergrid(self.game.board.width, self.game.board.height):
        if grid.get(pos) and grid.get(pos).cost <= 1:
            open_tiles.append(pos)

    open_tiles = [pos for pos in open_tiles if utils.calculate_distance(pos, start_position) > DISTANCE]
    counter = num
    grave_tiles = []
    while counter > 0 and open_tiles:
        counter -= 1
        tile = utilities.random_choice(open_tiles, start_position, seed, offset=counter)
        grave_tiles.append(tile)
        open_tiles = [
            pos for pos in open_tiles 
            if all(utils.calculate_distance(pos, grave_t) > DISTANCE for grave_t in grave_tiles)]

    def get_grave_time(start_pos: Pos, tile_pos: Pos):
        pathfinder = pathfinding.AStar(start_pos, tile_pos, grid)
        path = pathfinder.process(lambda adj: True)
        if path is None:
            path = []
        path_length = len(path)
        return path_length // 5 + 1

    for idx, tile_pos in enumerate(grave_tiles):
        grave_region = RegionObject("Grave_%d" % idx, regions.RegionType.NORMAL)
        grave_region.position = tile_pos
        grave_region.size = (1, 1)
        grave_region.time_left = get_grave_time(start_position, tile_pos)
        self.game.register_region(grave_region)
        action.do(action.AddRegion(grave_region))
