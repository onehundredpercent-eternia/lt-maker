from typing import Dict, List, Tuple

from app.data.database import DB
from app.data.level_units import GenericUnit

from app.engine.objects.unit import UnitObject

from app.engine.game_state import game

from app.utilities import str_utils

@dataclass
class ClassData:
    nid: str
    points: float
    weapon_type: str
    chapter_min: int
    chapter_max: int = 12

class_data = Data([
    ClassData('Myrmidon', 3, 'Sword', 3),
    ClassData('Errant', 2, 'Sword', 1),
    ClassData('Mercenary', 2, 'Sword', 2),
    ClassData('Thief', 2, 'Sword', 4),
    ClassData('Armor', 3, 'Lance', 2),
    ClassData('Cavalier', 2, 'Lance', 2),
    ClassData('Falcoknight', 4, 'Lance', 5),
    ClassData('Skirmisher', 2, 'Lance', 1),
    ClassData('Dracoknight', 5, 'Lance', 5),
    ClassData('Fighter', 2, 'Lance', 1),
    ClassData('Vanguard', 3, 'Lance', 3),
    ClassData('Raider', 2, 'Lance', 2),
    ClassData('Archer', 2, 'Bow', 1),
    ClassData('Hunter', 2, 'Bow', 2),
    ClassData('Soldier', 1.5, 'Lance', 1),
    ClassData('Brigand', 1.5, 'Axe', 1),
    ClassData('Seeress', 4, 'Light', 4),
    ClassData('Cleric', 3, 'Light', 3),
    ClassData('Mage', 2, 'Anima', 2),
    ClassData('Shaman', 3.5, 'Anima', 3),
    ClassData('Acolyte', 2, 'Dark', 2),
    ClassData('Sorceror', 3, 'Dark', 2),
])

base_items = {
    'Sword': 'Grave Sword',
    'Lance': 'Grave Lance',
    'Axe': 'Grave Axe',
    'Bow': 'Grave Bow',
    'Light': 'Light',
    'Anima': 'Anima',
    'Dark': 'Dark',
}

group_kinds = ('Single Type', 'Double Type', 'Leader', 'Single Type Mage Support', 'Double Type Mage Support')

# Elite is just a %chance modifier that gets applied after the fact

def completed_chapters() -> int:
    return game.game_vars.get('completed_chapters', 0)

def determine_avg_level():
    num_complete = completed_chapters()
    return num_complete * 2

def build_groups():
    for region in game.regions:
        if region.region_type == 'group':
            build_group(region)

def build_group(region):
    group_data: Dict = region.group_data

    # Determine which classes we can put here
    all_classes = set(class_data.keys())
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

    current_chapter = completed_chapters()
    all_classes = [klass for klass in all_classes if class_data[klass].chapter_min >= current_chapter and class_data[klass].chapter_max <= current_chapter]
    class_idx = game.get_random(0, len(all_classes) - 1)
    class_to_add = all_classes[class_idx]
    num_to_add = num_points // class_data[class_to_add].points + 1

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
        starting_items = [base_items[class_data[klass].weapon_type]]
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
