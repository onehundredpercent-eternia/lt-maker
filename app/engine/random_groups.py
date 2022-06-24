from dataclasses import dataclass
import random

from enum import Enum
from typing import Dict, List, Tuple

from app.utilities.data import Data
from app.data.database import DB
from app.data.level_units import GenericUnit, UniqueUnit

from app.engine.objects.unit import UnitObject

from app.engine import action, unit_funcs
from app.engine.game_state import game

from app.utilities import utils, str_utils

import logging

# Memento Chapter = Lion Throne Chapter
# 1 = 2
# 2-3 = 3-4  # Interesting gimmicks start here, some unique weapon usage, some magic
# 4-5 = 5-6  # Promoted Boss starts here, enemy AoE and Long-Range magics
# 6 = 6  # Promoted leaders start here
# 7-8 = 7  # Unique weapons for most units by this point
# 9-10 = 8  # All Promoted Leaders and half promoted scrubs
# 11 = 9  # Fully Promoted
# 12 = 10

ELITE_CHANCE = 0.15

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
    ClassData('Archer', 2.5, 'Bow', 1),
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

anima_users = ('Mage', 'Sage', 'Shaman', 'Druid')

item_data = {
    'Myrmidon': 'Crit Sword',
    'Swordmaster': 'Vantage Sword',
    'Errant': 'Shield Sword',
    'Knight': 'Lifelink Sword',
    'Mercenary': 'Attack Sword',
    'Veteran': 'Attack+ Sword',
    'Thief': 'Slim Sword',
    'Assassin': 'Thief Sword',
    'Armor': 'Shield Lance',
    'Immortal': 'Shield+ Lance',
    'Cavalier': 'Soldier Lance',
    'Paladin': 'Aura Lance',
    'Falcoknight': 'Slim Lance',
    'Falcolord': 'Slim+ Lance',
    'Skirmisher': 'Lunge Lance',
    'Halberdier': 'Pierce Lance',
    'Fighter': 'Shield Axe',
    'Warrior': 'Cleave Axe',
    'Raider': 'Slim Axe',
    'Berserker': 'Crit+ Axe',
    'Dracoknight': 'Attack Axe',
    'Dracolord': 'Immortal Axe',
    'Vanguard': 'Shield Axe',
    'Champion': 'Provoke Axe',
    'Archer': 'Soldier Bow',
    'Marksman': 'Soldier+ Bow',
    'Hunter': 'Crit Bow',
    'Ranger': 'Mageslayer Bow',
    'Soldier': 'Soldier Lance',
    'Brigand': 'Attack Axe', 
    'Cleric': 'Grave Light',
    'Saint': 'Grave Light',
    'Seer': 'Grave Light',
    'Valkyrie': 'Grave Light',
    'Sorceror': 'Grave Dark',
    'Warlock': 'Grave Dark',
    'Acolyte': 'Grave Dark',
    'Wizard': 'Grave Dark'
}

item_data2 = {
    'Cleric': 'Heal'
}

def get_potential_leaders(klass_nid) -> List[str]:
    base_class = get_unpromoted_class(klass_nid)
    d = {
        'Soldier': ['Armor'],
    }
    if base_class in d:
        return d[base_class]
    else:
        return [base_class]

class GroupKind(Enum):
    SINGLE_TYPE = 'Single Type'
    DOUBLE_TYPE = 'Double Type'
    LEADER = 'Leader'
    SINGLE_TYPE_WITH_MAGE_SUPPORT = 'Single Type With Mage Support'
    DOUBLE_TYPE_WITH_MAGE_SUPPORT = 'Double Type With Mage Support'
    BOSS = 'Boss'

group_kind_incidence = {
    GroupKind.SINGLE_TYPE: 2,
    GroupKind.DOUBLE_TYPE: 4,
    GroupKind.LEADER: 1,
    GroupKind.SINGLE_TYPE_WITH_MAGE_SUPPORT: 1,
    GroupKind.DOUBLE_TYPE_WITH_MAGE_SUPPORT: 1,
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

def get_num_points(chapter_num: int):
    return 4 + chapter_num//2

def get_promoted_class(klass_nid: str) -> str:
    klass = DB.classes.get(klass_nid)
    turns_into = klass.turns_into
    if turns_into:
        return klass.turns_into[0]
    else:
        return klass_nid

def get_unpromoted_class(klass_nid: str) -> str:
    klass = DB.classes.get(klass_nid)
    promotes_from = klass.promotes_from
    if promotes_from:
        return klass.promotes_from
    else:
        return klass_nid

def completed_chapters() -> int:
    return game.game_vars.get('completed_chapters', 0)

def determine_avg_level():
    num_complete = completed_chapters()
    return num_complete * 2

def create_unit(klass, position, level, ai, ai_group, is_elite=False, droppable=None):
    unit_nid = str_utils.get_next_generic_nid('301', [unit.nid for unit in game.units])

    # Give items
    if klass in item_data:
        starting_items = [(item_data[klass], False)]
        if klass in item_data2:
            starting_items.append((item_data2[klass], False))
    elif klass in anima_users:
        random.seed(ai_group)
        anima_type = random.randchoice(['Fire', 'Wind', 'Thunder'])
        if anima_type == 'Fire':
            starting_items = [('Grave Fire', False)]
        elif anima_type == 'Wind':
            starting_items = [('Grave Wind', False)]
        elif anima_type == 'Thunder':
            starting_items = [('Grave Thunder', False)]
    else:
        weapon_type = class_data.get(klass).weapon_type
        base_item = weapon_type
        starting_items = [(base_item, False)]

    # Handle giving droppable weapon
    if is_elite and (not droppable or droppable == 'None'):
        droppable = 'Weapon'
    if droppable == 'Weapon':
        starting_items[0] = (starting_items[0][0], True)
    elif droppable == 'Spell':
        starting_items.append((get_random_spell(), True))
    elif droppable == 'Forge':
        starting_items.append(("Forging Crystal", True))
    elif droppable == 'Promo':
        starting_items.append(("Promotion Orb", True))
    elif droppable == 'Misc':
        starting_items.append((get_random_misc(), True))
    elif droppable == 'Any':
        starting_items.append((get_random_item(), True))

    team = 'enemy'
    starting_position = position
    level_unit_prefab = GenericUnit(unit_nid, None, level, klass, DB.factions[0].nid, starting_items, team, ai, ai_group, starting_position)
    new_unit = UnitObject.from_prefab(level_unit_prefab, game.current_mode)
    if is_elite:
        new_unit._tags.append('Elite')
    new_unit.party = game.current_party
    game.full_register(new_unit)
    action.do(action.ArriveOnMap(new_unit, new_unit.position))
    return new_unit

def build_groups():
    regions = [region for region in game.regions if region.region_type == 'group']
    # Sort so the smallest regions are decided first
    regions = sorted(regions, key=lambda region: len(region.get_all_positions()))
    for region in regions:
        build_group(region)

def build_group(region):
    logging.debug("Build Group %s", region.nid)
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
    logging.debug(all_classes)
    logging.debug("Completed Chapters: %s", completed_chapters())
    
    all_classes = [klass for klass in all_classes if class_data.get(klass).chapter_min <= completed_chapters() + 1 and class_data.get(klass).chapter_max >= completed_chapters() + 1]
    # So now we have the complete list of classes we can use
    logging.debug(all_classes)

    # Determine how many and which specific classes will belong here
    positions: List[Tuple] = region.get_all_positions()
    num_points = get_num_points(completed_chapters())
    # Don't overlap other units
    positions = [pos for pos in positions if not game.board.get_unit(pos)]

    # If they can all fly, then this is a designated Flying zone, and so we should allow untraversable spots
    if all('Flying' in DB.classes.get(klass).tags for klass in all_classes):
        pass
    else:  # Only select traversable positions
        positions = [pos for pos in positions if game.movement.check_simple_traversable(pos)]
    logging.debug("#Positions: %s", len(positions))
    logging.debug("#Points: %s", num_points)

    is_elite = game.get_random_float() < ELITE_CHANCE and completed_chapters() > 0
    logging.debug("Elite: %s", is_elite)

    # Determine level
    avg_level: int = determine_avg_level()
    if is_elite:
        level = avg_level + 2
    else:
        level = game.get_random(max(1, avg_level - 1), avg_level + 1)

    logging.debug("Avg Level: %s", level)

    if len(positions) == 1:
        kind = GroupKind.BOSS
    else:
        kind = game.get_random_weighted_choice(list(group_kind_incidence.keys()), list(group_kind_incidence.values()))

    logging.debug("Kind: %s", kind)

    # Additional group data
    droppable = group_data.get('droppable', 'None')
    ai = group_data.get('ai', 'Attack')
    ai_group = region.nid

    if kind == GroupKind.SINGLE_TYPE:
        class_to_add = game.get_random_choice(all_classes)
        point_cost = class_data.get(class_to_add).points
        logging.debug("Class To Add: %s", class_to_add)
        logging.debug("Point Cost: %s", point_cost)
        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)
        while num_points > 0:
            num_points -= point_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite, droppable)
            droppable = None

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
        logging.debug("Class To Add: %s", class_to_add)
        logging.debug("Second Class To Add: %s", second_class_to_add)
        main_points = 0.5 * num_points
        second_points = 0.5 * num_points
        main_cost = class_data.get(class_to_add).points
        second_cost = class_data.get(second_class_to_add).points

        promotion_chance = get_promotion_chance(completed_chapters(), is_elite)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)
        if game.get_random_float() < promotion_chance:
            second_class_to_add = get_promoted_class(second_class_to_add)

        while main_points > 0:
            main_points -= main_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite, droppable)
            droppable = None

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while second_points > 0:
            second_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

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
        main_cost = class_data.get(main_class_to_add).points
        mage_cost = class_data.get(mage_class_to_add).points
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

            new_unit = create_unit(main_class_to_add, position, level, ai, ai_group, is_elite, droppable)
            droppable = None

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

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
        main_cost = class_data.get(main_class_to_add).points
        second_cost = class_data.get(second_class_to_add).points
        mage_cost = class_data.get(mage_class_to_add).points
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

            new_unit = create_unit(main_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while second_points > 0:
            second_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(second_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions in region to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(mage_class_to_add, position, level, ai, ai_group, is_elite, droppable)
            droppable = None

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

        leader_cost = class_data.get(leader_class_to_add).points

        num_points -= leader_cost
        position = game.get_random_choice(positions)
        positions.remove(position)

        new_unit = create_unit(leader_class_to_add, position, level, ai, ai_group, is_elite, droppable)

        if not positions:
            logging.error("No more valid positions in region to place units")
            return

        while num_points > 0:
            point_cost = class_data.get(regular_class_to_add).points
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
        new_unit = create_unit(class_to_add, position, level, ai, ai_group, droppable=droppable)
        new_unit._tags.append('Boss')
        # Give the Boss some bonuses
        stat_changes = {'HP': 5, 'POW': 2, 'SKL': 2, 'SPD': 2, 'LCK': 5, 'DEF': 2, 'RES': 3}
        # Make sure we don't go over max
        stat_changes = {k: utils.clamp(v, 0, DB.classes.get(class_to_add).max_stats.get(k, 30) - new_unit.stats[k]) for k, v in stat_changes.items()}
        unit_funcs.apply_stat_changes(new_unit, stat_changes)
        # Give the Boss 5 free autolevels
        unit_funcs.auto_level(new_unit, 5, new_unit.level, growth_method='fixed')

def get_recruitable_unit(level_var_nid, position, level, tag_list, team):
    possible_unit_prefabs = \
        [unit for unit in DB.units if 
            unit.nid not in [u.nid for u in game.units] and 
            all(t in unit.tags for t in tag_list)]
    if not possible_unit_prefabs:
        logging.error("No possible unit to recruit with tags %s", tag_list)
        return
    unit = game.get_random_choice(possible_unit_prefabs)
    ai = 'None'
    level_unit_prefab = UniqueUnit(unit.nid, team, ai, None, None, position)
    new_unit = UnitObject.from_prefab(level_unit_prefab, game.current_mode)
    new_unit.party = game.current_party
    unit_funcs.auto_level(new_unit, level - new_unit.level, new_unit.level, growth_method='fixed')
    new_unit.level = level
    game.full_register(new_unit)
    action.do(action.SetLevelVar(level_var_nid, unit.nid))
    if new_unit.position:
        action.do(action.ArriveOnMap(new_unit, new_unit.position))
    return new_unit
