from __future__ import annotations

import random
from typing import Set, TYPE_CHECKING

from app.utilities.typing import Pos

if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain

RANDOM_SEED = 0

def get_random_seed() -> int:
    return RANDOM_SEED

def set_random_seed(val: int):
    global RANDOM_SEED
    RANDOM_SEED = val

def random_choice(choices: list, pos: tuple, seed: int = None, offset: int = 0):
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos[0] * 1024**2 + pos[1] * 1024 + offset)
    return random.choice(choices)

def random_random(pos: tuple, seed: int = None, offset: int = 0):
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos[0] * 1024**2 + pos[1] * 1024 + offset)
    return random.random()

def flood_fill(tilemap: DungeonTileMap, pos: Pos, 
               diagonal: bool = False, match: Set[Terrain] = None,
               match_only_these_positions: Set[Pos] = None) -> Set[Pos]:
    """
    # tilemap - the Dungeon tilemap to work on
    # pos - Which position to start the flood fill on 
    # diagonal (optional) - Whether to flood fill diagonally in addition to cardinally
    # match - Set of terrain that counts as a match
    # match_only_these_positions - Set of positions that count as being valid to flood fill onto
    """
    blob_positions = set()
    unexplored_stack = []
    # Get coords like current coord in current_layer
    if not match:
        current_tile = tilemap.get_terrain(pos)
        match = {current_tile}

    def find_similar(starting_pos: Pos, match: set):
        unexplored_stack.append(starting_pos)

        counter = 0
        while unexplored_stack and counter < 99999:
            current_pos = unexplored_stack.pop()

            if current_pos in blob_positions:
                continue
            if not tilemap.check_bounds(current_pos):
                continue
            if match_only_these_positions:  # Just check if it's in the set
                if current_pos not in match_only_these_positions:
                    continue
            else:
                nid = tilemap.get_terrain(current_pos)
                if nid not in match:
                    continue

            blob_positions.add(current_pos)
            unexplored_stack.append((current_pos[0] + 1, current_pos[1]))
            unexplored_stack.append((current_pos[0] - 1, current_pos[1]))
            unexplored_stack.append((current_pos[0], current_pos[1] + 1))
            unexplored_stack.append((current_pos[0], current_pos[1] - 1))
            if diagonal:
                unexplored_stack.append((current_pos[0] - 1, current_pos[1] - 1))
                unexplored_stack.append((current_pos[0] - 1, current_pos[1] + 1))
                unexplored_stack.append((current_pos[0] + 1, current_pos[1] - 1))
                unexplored_stack.append((current_pos[0] + 1, current_pos[1] + 1))
            counter += 1
        if counter >= 99999:
            raise RuntimeError("Unexpected infinite loop in generic flood_fill")

    # Determine which coords should be flood-filled
    find_similar(pos, match)
    return blob_positions
