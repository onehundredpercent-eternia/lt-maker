from typing import Dict, List, Tuple

from app.data.database import DB
from app.data.level_units import GenericUnit

from app.engine.objects.unit import UnitObject

from app.engine.game_state import game

from app.utilities import str_utils

class_points = {
    'Myrmidon': 3,
    'Errant': 2,
    'Mercenary': 2,
    'Thief': 2,
    'Armor': 3,
    'Cavalier': 2,
    'Falcoknight': 4,
    'Skirmisher': 2,
    'Dracoknight': 5,
    'Fighter': 2,
    'Vanguard': 3,
    'Raider': 2,
    'Archer': 2,
    'Hunter': 2,
    'Soldier': 1.5,
    'Brigand': 1.5, 
}   

def determine_avg_level():
    num_complete = game.game_vars.get('completed_chapters', 0)
    return num_complete * 2

def build_groups():
    for region in game.regions:
        if region.region_type == 'group':
            build_group(region)

def build_group(region):
    group_data: Dict = region.group_data

    # Determine which classes we can put here
    all_classes = set(class_points.keys())
    valid_classes: List[str] = group_data.get('valid_classes', [])
    if valid_classes:
        all_classes &= set(valid_classes)
    valid_tags: List[str] = group_data.get('valid_tags', [])
    if valid_tags:
        valid_classes = \
            [klass for klass in all_classes \
             if any(tag in DB.classes.get(klass).tags for tag in valid_tags)]
        all_classes &= set(valid_classes)
    all_classes = list(all_classes)

    # Determine how many and which specific classes will belong here
    positions: List[Tuple] = region.get_all_positions()
    num_points = len(positions) / 2
    # Don't overlap other units
    positions = [pos for pos in positions if not game.get_unit(pos)]

    class_idx = game.get_random(0, len(all_classes) - 1)
    class_to_add = all_classes[class_idx]
    num_to_add = num_points // class_points[class_to_add] + 1

    # Assign units to positions
    position_to_add = []
    while num_to_add > 0:
        # print(len(positions) - 1, region.nid, num_to_add)
        pos_idx = game.get_random(0, len(positions) - 1)
        position = positions[pos_idx]
        position_to_add.append(position)
        positions.remove(position)
        num_to_add -= 1

    # Determine level
    avg_level: int = determine_avg_level()
    level = game.get_random(max(1, avg_level - 1), avg_level + 1)

    for position in position_to_add:
        unit_nid = str_utils.get_next_int('301', [unit.nid for unit in game.units])
        klass = class_to_add
        starting_items = []
        team = 'enemy'
        ai = group_data.get('ai', 'Attack')
        ai_group = region.nid  # All units in a region work in the same group
        starting_position = position
        level_unit_prefab = GenericUnit(unit_nid, None, level, klass, DB.factions[0].nid, starting_items, team, ai, ai_group, starting_position)
        new_unit = UnitObject.from_prefab(level_unit_prefab)
        new_unit.party = game.current_party
        if len(position_to_add) == 1:
            new_unit._tags.append('Boss')
        game.full_register(new_unit)
        game.arrive(new_unit)
