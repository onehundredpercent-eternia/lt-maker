from enum import Enum
from typing import Dict, List, Tuple

from app.data.database import DB
from app.data.level_units import GenericUnit

from app.engine.objects.unit import UnitObject

from app.engine import action
from app.engine.game_state import game

from app.utilities import str_utils

import logging

# TODO:
# Elite modifier
# Promotion chance/requirement
# Better Items

# Memento Chapter = Lion Throne Chapter
# 1 = 2
# 2-3 = 3-4  # Interesting gimmicks start here, some unique weapon usage, some magic
# 4-5 = 5-6  # Promoted Boss starts here, enemy AoE and Long-Range magics
# 6 = 6  # Promoted leaders start here
# 7-8 = 7  # Unique weapons for most units by this point
# 9-10 = 8  # All Promoted Leaders and half promoted scrubs
# 11 = 9  # Fully Promoted
# 12 = 10

POSITIONS_TO_POINTS = 0.5
ELITE_CHANCE = 0.15
# Higher level when Elite, also gain better weapons (anything else?)
# Tag Elite groups so they are visible

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
    ClassData('Dracoknight', 5, 'Axe', 5),
    ClassData('Fighter', 2, 'Axe', 1),
    ClassData('Vanguard', 3, 'Axe', 3),
    ClassData('Raider', 2, 'Axe', 2),
    ClassData('Archer', 2, 'Bow', 1),
    ClassData('Hunter', 2, 'Bow', 2),
    ClassData('Soldier', 1.5, 'Lance', 1, 9),
    ClassData('Brigand', 1.5, 'Axe', 1, 9),
    ClassData('Seeress', 4, 'Light', 4),
    ClassData('Cleric', 3, 'Light', 3),
    ClassData('Mage', 2.5, 'Anima', 2),
    ClassData('Shaman', 3.5, 'Anima', 3),
    ClassData('Acolyte', 2.5, 'Dark', 2),
    ClassData('Sorceror', 3, 'Dark', 2),
])

@dataclass
class ItemData:
    nid: str
    points: float
    chapter_min: int
    chapter_max: int = 12

base_items = {
    'Sword': 'Sword',
    'Lance': 'Lance',
    'Axe': 'Axe',
    'Bow': 'Bow',
    'Light': 'Light',
    'Anima': 'Anima',
    'Dark': 'Dark',
}

# Ideally we standardize item access, so we minimize having to read characters
# Elite units have different loadouts
# Take a look at items in Conquest?

# Take for instance, soldiers:
    # from Chapter 1 to 2, regular Lance
    # from chapter 3 to 9, mercian lance

# Or Myrmidons:
    # from chapter 1 to 3, regular sword
    # from chapter 3 to 6, cimbrian sword
    # from chapter 7 to 12, killing edge

sword_item_data = Data({
    ItemData('Sword', 0, 0),
    ItemData('Mercian Sword', 1, 3),
    ItemData('Cimbrian Sword', 2, 5),
    ItemData('Aellulian Sword', 4, 6),
})

anima_item_data = Data({
    ItemData('Anima', 0, 0),
    ItemData('Elfire', 2, 5),
    ItemData('Wyrmsfire', 5, 6),
})

item_data = {
    'Sword': sword_item_data,
    'Anima': anima_item_data
}

class GroupKind(Enum):
    SINGLE_TYPE = 'Single Type'
    DOUBLE_TYPE = 'Double Type'
    LEADER = 'Leader'
    SINGLE_TYPE_WITH_MAGE_SUPPORT = 'Single Type With Mage Support'
    DOUBLE_TYPE_WITH_MAGE_SUPPORT = 'Double Type With Mage Support'
    BOSS = 'Boss'

group_kind_incidence = {
    GroupKind.SINGLE_TYPE = 2,
    GroupKind.DOUBLE_TYPE = 4,
    GroupKind.LEADER = 1,
    GroupKind.SINGLE_TYPE_WITH_MAGE_SUPPORT = 1,
    GroupKind.DOUBLE_TYPE_WITH_MAGE_SUPPORT = 1,
}

def get_promotion_chance(chapter_num: int, is_elite: bool = False, is_leader: bool = False) -> float:
    """
    Returns a floating point number between 0 and 1 describing the chance that an enemy unit
    should be promoted by this point
    """
    starting_promotion_chapter = 6  # Chapter 7 is first chapter with promoted units, normally
    if is_elite and is_leader:
        starting_promotion_chapter = 3  # Chapter 4
    elif is_elite or is_leader:
        starting_promotion_chapter = 5  # Chapter 6
    base_val = (max(0, chapter_num - starting_promotion_chapter) / 5) ** 2
    return base_val

def get_promoted_class(klass_nid: str):
    klass = DB.classes.get(klass_nid)
    turns_into = klass.turns_into
    if turns_into:
        return klass.turns_into[0]
    else:
        return klasS_nid

def completed_chapters() -> int:
    return game.game_vars.get('completed_chapters', 0)

def determine_avg_level():
    num_complete = completed_chapters()
    return num_complete * 2

def create_unit(klass, position, level, ai, ai_group, is_elite=False):
    unit_nid = str_utils.get_next_int('301', [unit.nid for unit in game.units])
    weapon_type = class_data[klass].weapon_type
    base_item = base_items[weapon_type]
    starting_items = [base_item]
    team = 'enemy'
    ai_group = region.nid  # All units in a region work in the same group
    starting_position = position
    level_unit_prefab = GenericUnit(unit_nid, None, level, klass, DB.factions[0].nid, starting_items, team, ai, ai_group, starting_position)
    new_unit = UnitObject.from_prefab(level_unit_prefab)
    if is_elite:
        new_unit._tags.append('Elite')
    new_unit.party = game.current_party
    game.full_register(new_unit)
    action.ArriveOnMap(new_unit, new_unit.position))
    return new_unit

def build_groups():
    regions = [region for region in game.regions if region.region_type == 'group']
    # Sort so the smallest regions are decided first
    regions = sorted(regions, key=lambda region: len(region.get_all_positions()))
    for region in regions:
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
    
    all_classes = [klass for klass in all_classes if class_data[klass].chapter_min >= completed_chapters() and class_data[klass].chapter_max <= completed_chapters()]
    # So now we have the complete list of classes we can use

    # Determine how many and which specific classes will belong here
    positions: List[Tuple] = region.get_all_positions()
    num_points = len(positions) * POSITIONS_TO_POINTS
    # Don't overlap other units
    positions = [pos for pos in positions if not game.get_unit(pos)]

    # If they can all fly, then this is a designated Flying zone, and so we should allow untraversable spots
    if all('Flying' in DB.classes.get(klass).tags for klass in all_classes):
        pass
    else:  # Only select traversable positions
        positions = [pos for pos in positions if game.movement.check_simple_traversable(pos)]

    is_elite = game.get_random_float() < ELITE_CHANCE

    # Determine level
    avg_level: int = determine_avg_level()
    if is_elite:
        level = avg_level + 2
    else:
        level = game.get_random(max(1, avg_level - 1), avg_level + 1)

    if len(positions) == 1:
        kind = GroupKind.BOSS
    else:
        kind = game.get_weighted_random_choice(group_kind_incidence.keys(), group_kind_incidence.values())

    if kind == GroupKind.SINGLE_TYPE:
        class_to_add = game.get_random_choice(all_classes)
        point_cost = class_data[class_to_add].points
        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)
        while num_points > 0:
            num_points -= point_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

    elif kind == GroupKind.DOUBLE_TYPE:
        class_to_add = game.get_random_choice(all_classes)
        all_classes.remove(class_to_add)
        if all_classes:
            second_class_to_add = game.get_random_choice(all_classes)
        else:
            second_class_to_add = class_to_add
        main_points = 0.5 * num_points
        second_points = 0.5 * num_points
        main_cost = class_data[class_to_add].points
        second_cost = class_data[second_class_to_add].points

        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)
        if game.get_random_float() < promotion_chance:
            second_class_to_add = get_promoted_class(second_class_to_add)

        while main_points > 0:
            num_points -= main_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while second_points > 0:
            num_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

    elif kind == GroupKind.SINGLE_TYPE_WITH_MAGE_SUPPORT:
        all_mage_classes = [klass for klass in all_classes if 'Mage' in DB.classes.get(klass).tags]
        all_non_mage_classes = [klass for klass in all_classes if 'Mage' not in DB.classes.get(klass).tags]

        main_class_to_add = game.get_random_choice(all_non_mage_classes)
        if all_mage_classes:
            mage_class_to_add = game.get_random_choice(all_mage_classes)
        else:
            mage_class_to_add = main_class_to_add
        main_cost = class_data[main_class_to_add].points
        mage_cost = class_data[mage_class_to_add].points
        # Split 3 to 1  # TODO is this actually a good split?
        main_points = num_points * 0.75
        mage_points = num_points * 0.25

        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            main_class_to_add = get_promoted_class(main_class_to_add)
        if game.get_random_float() < promotion_chance:
            mage_class_to_add = get_promoted_class(mage_class_to_add)

        while main_points > 0:
            main_points -= main_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(main_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(mage_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

    elif kind == GroupKind.DOUBLE_TYPE_WITH_MAGE_SUPPORT:
        all_mage_classes = [klass for klass in all_classes if 'Mage' in DB.classes.get(klass).tags]
        all_non_mage_classes = [klass for klass in all_classes if 'Mage' not in DB.classes.get(klass).tags]

        main_class_to_add = game.get_random_choice(all_non_mage_classes)
        all_non_mage_classes.remove(main_class_to_add)
        if all_non_mage_classes:
            second_class_to_add = game.get_random_choice(all_non_mage_classes)
        else:
            second_class_to_add = main_class_to_add
        if all_mage_classes:
            mage_class_to_add = game.get_random_choice(all_mage_classes)
        else:
            mage_class_to_add = main_class_to_add
        main_cost = class_data[main_class_to_add].points
        second_cost = class_data[second_class_to_add].points
        mage_cost = class_data[mage_class_to_add].points
        # Split 1.5 to 1.5 to 1  # TODO is this actually a good split?
        main_points = num_points * 0.375
        second_points = num_points * 0.375
        mage_points = num_points * 0.25

        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            main_class_to_add = get_promoted_class(main_class_to_add)
        if game.get_random_float() < promotion_chance:
            second_class_to_add = get_promoted_class(second_class_to_add)
        if game.get_random_float() < promotion_chance:
            mage_class_to_add = get_promoted_class(mage_class_to_add)

        while main_points > 0:
            main_points -= main_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(main_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while second_points > 0:
            second_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(second_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(mage_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

    elif kind == GroupKind.LEADER:
        regular_class_to_add = game.get_random_choice(all_classes)
        leader_classes = get_potential_leaders(regular_class_to_add)
        leader_class_to_add = game.get_random_choice(leader_classes)

        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            regular_class_to_add = get_promoted_class(regular_class_to_add)
        leader_promotion_chance = get_promotion_chance(completed_chapters(), is_elite, True)
        if game.get_random_float() < leader_promotion_chance:
            leader_class_to_add = get_promoted_class(leader_class_to_add)

        leader_cost = class_data[leader_class_to_add].points

        
        num_points -= leader_cost
        position = game.get_random_choice(positions)
        positions.remove(position)

        ai = group_data.get('ai', 'Attack')
        ai_group = region.nid
        new_unit = create_unit(leader_class_to_add, position, level, ai, ai_group, is_elite)

        if not positions:
            logging.error("No more valid positions in region to place units")
            return

        while num_points > 0:
            point_cost = class_data[regular_class_to_add].points
            num_points -= point_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            ai = group_data.get('ai', 'Attack')
            ai_group = region.nid
            new_unit = create_unit(regular_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

    elif kind == GroupKind.BOSS:
        boss_classes = [c for c in all_classes if c != 'Soldier']
        class_to_add = game.get_random_choice(boss_classes)
        position = game.get_random_choice(positions)
        positions.remove(position)

        promotion_chance = get_promotion_chance(completed_chapters(), True, True)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)

        ai = group_data.get('ai', 'Guard')
        ai_group = region.nid
        level += 2  # Boss is two levels above by default
        new_unit = create_unit(class_to_add, position, level, ai, ai_group)
        new_unit._tags.append('Boss')
        # Give the Boss some bonuses
        stat_changes = {'HP': 5, 'POW': 2, 'SKL': 2, 'SPD': 2, 'LCK': 5, 'DEF': 2, 'RES': 3}
        # Make sure we don't go over max
        stat_changes = {k: utils.clamp(v, 0, DB.classes.get(class_to_add).maximum.get(k, 30) - new_unit.stats[k]) for k, v in stat_changes.items()}
        unit_funcs.apply_stat_changes(stat_changes)
        # Give the Boss 5 free autolevels
        unit_funcs.auto_level(new_unit, 5, new_unit.level, growth_method='fixed')
