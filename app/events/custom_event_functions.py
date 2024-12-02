from typing import TYPE_CHECKING, Set, Tuple

from app.utilities.typing import NID, Pos

from app.dungeon_maker import encounter_generation, tilemap_generation
from app.engine import action

if TYPE_CHECKING:
    from app.events.event import Event

def generate_dungeon(self: Event, floor_level: int, dungeon_theme: str, 
                     dungeon_palette: str, enemy_level: int, seed: int = None, 
                     flags=None):
    if seed is None:
        seed = -1
    tilemap, dungeon_tilemap = \
        tilemap_generation.generate_map(dungeon_theme, dungeon_palette, seed)
    
    # Actually set up
    self.game.level.tilemap = tilemap
    self.game.set_up_game_board(self.game.level.tilemap)
    
    # Place encounters
    encounter_generation.place_encounters(
        self.game, dungeon_tilemap, tilemap, 
        enemy_level, floor_level, dungeon_theme, seed)

    # Can't use turnwheel to go any further back
    self.game.action_log.set_first_free_action()

def place_party(self: Event, position: Pos, party_size: int, flags=None):
    members = self.game.get_party_members()
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
