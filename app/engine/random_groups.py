from dataclasses import dataclass

from enum import Enum
from typing import Dict, List, Tuple

from app.constants import TILEWIDTH, TILEHEIGHT

from app.utilities.data import Data
from app.data.database import DB
from app.data.level_units import GenericUnit, UniqueUnit

from app.dungeon_maker import dungeon_maker, terrain_maker

from app.engine.objects.unit import UnitObject
from app.engine.objects.tilemap import TileMapObject

from app.engine import action, unit_funcs, engine, item_funcs
from app.events import regions
from app.engine.game_state import game

from app.utilities import utils, str_utils
from app.utilities.algorithms.interpolation import lerp

import logging

# Memento Chapter = Lion Throne Chapter
# 0 = 2
# 1-2 = 3-4  # some unique weapon usage, some magic
# 3-4 = 5-6  # Promoted Boss starts here, enemy AoE and Long-Range magics
# 5 = 6  # Promoted leaders start here
# 6 = 7  # Unique weapons for most units by this point
# 7 = 8 # All Promoted Leaders and half promoted scrubs
# 8 = 9 # Fully Promoted  
# 9 = 10  # Boss Fight

LAST_CHAPTER = 9

@dataclass
class ClassData:
    nid: str
    points: float
    weapon_type: str
    chapter_min: int
    chapter_max: int = LAST_CHAPTER

class_data = Data([
    ClassData('Myrmidon', 3, 'Sword', 2),
    ClassData('Errant', 2, 'Sword', 1),
    ClassData('Mercenary', 2, 'Sword', 1),
    ClassData('Thief', 2, 'Sword', 3),
    ClassData('Sentinel', 3, 'Lance', 2),
    ClassData('Cavalier', 2, 'Lance', 2),
    ClassData('Falcoknight', 4, 'Lance', 4),
    ClassData('Skirmisher', 2, 'Lance', 1),
    ClassData('Dracoknight', 5, 'Axe', 4),
    ClassData('Fighter', 2, 'Axe', 1),
    ClassData('Vanguard', 3, 'Axe', 2),
    ClassData('Raider', 2, 'Axe', 2),
    ClassData('Archer', 2.5, 'Bow', 1),
    ClassData('Nomad', 3, 'Bow', 3),
    ClassData('Soldier', 1.5, 'Lance', 1, 7),
    ClassData('Brigand', 1.5, 'Axe', 1, 7),
    ClassData('Seeress', 4, 'Light', 4),
    ClassData('Cleric', 3, 'Light', 3),
    ClassData('Mage', 2.5, 'Anima', 2),
    ClassData('Maligknight', 5, 'Anima', 6),
    ClassData('Acolyte', 2.5, 'Dark', 2),
    ClassData('Sorceror', 3, 'Dark', 2),
])

anima_users = ('Mage', 'Sage', 'Maligknight', 'Maliglord')

item_data = {
    'Myrmidon': 'Crit Sword',
    'Swordmaster': 'Vantage Sword',
    'Errant': 'Shield Sword',
    'Knight': 'Lifelink Sword',
    'Mercenary': 'Attack Sword',
    'Veteran': 'Attack+ Sword',
    'Thief': 'Slim Sword',
    'Assassin': 'Thief Sword',
    'Sentinel': 'Shield Lance',
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
    'Saint': 'Charisma',
    'Seeress': 'Glimmer',
    'Valkyrie': 'Miracle',
    'Warlock': 'Luna',
}

item_data2 = {
    'Cleric': 'Heal',
    'Saint': 'Physic',
    'Seeress': 'Fortune',
    'Valkyrie': 'Sunbeam',
}

def get_potential_leaders(klass_nid) -> List[str]:
    base_class = get_unpromoted_class(klass_nid)
    d = {
        'Soldier': ['Sentinel'],
        'Brigand': ['Mercenary']
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
    base_val = (max(0, chapter_num - starting_promotion_chapter) / 4) ** 2
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

def determine_avg_level() -> int:
    num_complete = completed_chapters()
    return num_complete * 2

def get_elite_chance() -> float:
    return lerp(0.1, 0.25, completed_chapters() / LAST_CHAPTER)

def get_random_item(tags=None):
    tags = tags or []
    all_items = []
    all_chances = []
    for tag in tags:
        if tag == 'Forge':
            chance = 5
            items = [item for item in DB.items if tag in item.tags]
        elif tag == 'Promo':
            chance = 5
            items = [item for item in DB.items if tag in item.tags]
        else:
            chance = 30
            items = [item for item in DB.items if tag in item.tags]
        all_items.append(items)
        all_chances.append(chance)
    items = game.get_random_weighted_choice(all_items, all_chances)
    return game.get_random_choice(items)

def get_random_tree_item():
    chapter_num = completed_chapters()
    if chapter_num == 0:
        tags = ['Weapon']
    elif chapter_num == 1:
        tags = ['Weapon', 'Spell', 'Accessory']
    elif chapter_num == 2:
        tags = ['Weapon', 'Spell', 'Forge', 'Accessory']
    elif chapter_num == 3:
        tags = ['Weapon', 'Spell', 'Forge', 'Accessory']
    elif chapter_num == 4:
        tags = ['Weapon', 'Spell', 'Forge', 'Promo', 'Accessory']
    elif chapter_num == 5:
        tags = ['Weapon', 'Weapon+', 'Spell', 'Forge', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 6:
        tags = ['Weapon+', 'Spell', 'Spell+', 'Forge', 'Promo', 'Accessory', 'Accessory+']
    elif chapter_num == 7:
        tags = ['Weapon+', 'Spell+', 'Promo', 'Accessory+']
    elif chapter_num >= 8:
        tags = ['Weapon+', 'Spell+', 'Accessory+']
    return get_random_item(tags)

def create_unit(klass, position, level, ai, ai_group, is_elite=False, droppable=None):
    chapter_num = completed_chapters()
    unit_nid = str_utils.get_next_generic_nid('301', [unit.nid for unit in game.units])

    # Give items
    if klass in item_data and level >= 5:
        starting_items = [(item_data[klass], False)]
    elif klass in anima_users:
        anima_type = game.get_random_choice(['Fire', 'Wind', 'Thunder'])
        if anima_type == 'Fire':
            starting_items = [('Grave Fire', False)]
        elif anima_type == 'Wind':
            starting_items = [('Grave Wind', False)]
        elif anima_type == 'Thunder':
            starting_items = [('Grave Thunder', False)]
    else:
        weapon_type = class_data.get(klass).weapon_type
        base_item = weapon_type
        starting_items = [('Grave %s' % base_item, False)]

    if klass in item_data2:
        starting_items.append((item_data2[klass], False))

    # Handle giving droppable weapon
    if is_elite and (not droppable or droppable == 'None'):
        droppable = 'Weapon'
    if droppable == 'Weapon':
        starting_items[0] = (starting_items[0][0], True)
    elif droppable in ('Weapon+', 'Spell', 'Spell+', 'Forge', 'Promo', 'Accessory', 'Accessory+'):
        starting_items.append((get_random_item([droppable]), True))
    elif droppable == 'Any':
        weapon = 'Weapon+' if chapter_num >= 5 else 'Weapon'
        spell = 'Spell+' if chapter_num >= 6 else 'Spell'
        accessory = 'Accessory+' if chapter_num >= 5 else 'Accessory'
        tags = [weapon, spell, accessory, 'Forge']
        if chapter_num > 3:
            tags.append('Promo')
        starting_items.append((get_random_item(tags), True))

    logging.debug('Starting Items: %s', starting_items)
    assert all(item[0] in DB.items.keys() for item in starting_items)
    team = 'enemy'
    starting_position = position
    level_unit_prefab = GenericUnit(unit_nid, None, level, klass, DB.factions[0].nid, starting_items, team, ai, ai_group, starting_position)
    logging.debug(level_unit_prefab.starting_items)
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
        build_group(region.nid, region.group_data, region.get_all_positions())

def build_group(group_nid: str, group_data: Dict, positions: List[Tuple]):
    logging.debug("Build Group %s", group_nid)

    # Determine which classes we can put here
    all_classes = set(class_data.keys())
    assert all(klass in DB.classes.keys() for klass in all_classes)
    valid_classes: List[str] = group_data.get('valid_classes', [])
    if valid_classes:
        all_classes &= set(valid_classes)
    valid_tags: List[str] = group_data.get('valid_tags', [])
    if valid_tags:
        logging.debug("Valid Tags: %s", valid_tags)
        valid_classes = \
            [klass for klass in all_classes \
             if any(tag in DB.classes.get(klass).tags for tag in valid_tags)]
        all_classes &= set(valid_classes)
    all_classes = list(all_classes)
    logging.debug("Valid Classes: %s", all_classes)
    logging.debug("Completed Chapters: %s", completed_chapters())
    assert len(all_classes) > 0
    
    all_classes = [klass for klass in all_classes if class_data.get(klass).chapter_min <= completed_chapters() + 1 and class_data.get(klass).chapter_max >= completed_chapters() + 1]
    # So now we have the complete list of classes we can use
    logging.debug("Valid Classes: %s", all_classes)
    assert len(all_classes) > 0

    # Determine how many and which specific classes will belong here
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

    is_elite = game.get_random_float() < get_elite_chance() and completed_chapters() > 0
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
    ai_group = group_nid

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
                logging.error("No more valid positions to place units")
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
                logging.error("No more valid positions to place units")
                return

        while second_points > 0:
            second_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions to place units")
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
                logging.error("No more valid positions to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(mage_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions to place units")
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
                logging.error("No more valid positions to place units")
                return

        while second_points > 0:
            second_points -= second_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(second_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions to place units")
                return

        while mage_points > 0:
            mage_points -= mage_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(mage_class_to_add, position, level, ai, ai_group, is_elite, droppable)
            droppable = None

            if not positions:
                logging.error("No more valid positions to place units")
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
            logging.error("No more valid positions to place units")
            return

        while num_points > 0:
            point_cost = class_data.get(regular_class_to_add).points
            num_points -= point_cost
            position = game.get_random_choice(positions)
            positions.remove(position)

            new_unit = create_unit(regular_class_to_add, position, level, ai, ai_group, is_elite)

            if not positions:
                logging.error("No more valid positions to place units")
                return

    elif kind == GroupKind.BOSS:
        boss_classes = [c for c in all_classes if c != 'Soldier']
        class_to_add = game.get_random_choice(boss_classes)
        position = game.get_random_choice(positions)
        positions.remove(position)

        promotion_chance = get_promotion_chance(completed_chapters(), True, True)
        if game.get_random_float() < promotion_chance:
            class_to_add = get_promoted_class(class_to_add)

        ai = group_data.get('ai', 'Attack')
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

def get_recruitable_unit(level_var_nid, level, tag_list, team):
    possible_unit_prefabs = \
        [unit for unit in DB.units if 
            unit.nid not in [u.nid for u in game.units] and 
            any(t in unit.tags for t in tag_list)]
    if not possible_unit_prefabs:
        logging.error("No possible unit to recruit with tags %s", tag_list)
        return
    unit = game.get_random_choice(possible_unit_prefabs)
    ai = 'None'
    level_unit_prefab = UniqueUnit(unit.nid, team, ai, None, None, None)
    new_unit = UnitObject.from_prefab(level_unit_prefab, game.current_mode)
    new_unit.party = game.current_party
    unit_funcs.auto_level(new_unit, level - new_unit.level, new_unit.level, growth_method='fixed')
    new_unit.level = level
    game.full_register(new_unit)
    action.do(action.SetLevelVar(level_var_nid, unit.nid))
    if new_unit.klass in item_data and new_unit.level >= 5:
        item_id = item_data[new_unit.klass]
        item = item_funcs.create_item(None, item_id)
        game.register_item(item)
        action.do(action.GiveItem(new_unit, item))
    if new_unit.klass in item_data2:
        item_id = item_data2[new_unit.klass]
        item = item_funcs.create_item(None, item_id)
        game.register_item(item)
        action.do(action.GiveItem(new_unit, item))
    return new_unit

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

def generate_map(theme=None, enemy_type=None, size=None) -> None:
    theme = theme or 'default'
    enemy_type = [enemy_type] or ['Soldier']
    size = size or (20, 20)
    # Generate map prefab (called dungeon)
    seed = game.game_vars.get('_random_seed', -1)
    dungeon, rooms = dungeon_maker.generate_dungeon(theme, size, seed)
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
    level_nid = str(completed_chapters())
    tilemap = TileMapObject.build_from_scratch(level_nid, dungeon, surf)
    # Now we have a complete tilemap
    # Lets build a level
    game.build_level_from_scratch(level_nid, tilemap)

    # Choose a starting room and an ending/boss room
    biggest_south_room = rooms[0]
    biggest_north_room = rooms[0]
    for room in rooms[1:]:
        if room.y >= dungeon.height * 0.75:
            if room.size > biggest_south_room.size:
                biggest_south_room = room
        if room.y <= dungeon.height * 0.25:
            if room.size >= biggest_north_room.size:
                biggest_north_room = room

    starting_room = biggest_south_room
    ending_room = biggest_north_room

    # Create formations
    num_formations = int(lerp(6, 12, completed_chapters() / LAST_CHAPTER))
    # Starting from southwest corner of room
    tiles = sorted(starting_room.tiles, key=lambda x: (x[0], -x[1]))
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
    boss_pos = sorted(room.tiles, key=lambda x: (-x[0], x[1]))[0]

    # Populate rooms with enemies
    group_data = {'valid_tags': enemy_type}
    for idx, room in enumerate(rooms):
        if room is starting_room:
            valid_tiles = [tile for tile in room.tiles if 
                           all(utils.calculate_distance(tile, form_tile) > 3 for form_tile in formation_tiles)]
            build_group('%d' % idx, group_data, valid_tiles)
        elif room is ending_room:
            build_group('Boss', group_data, [boss_pos])
            build_group('%d' % idx, group_data, room.tiles)
        else:
            build_group('%d' % idx, group_data, room.tiles)

    # Generate grave tree regions
    num_grave_trees = int(lerp(3, 6, completed_chapters() / LAST_CHAPTER))
    valid_positions = [(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)]
    valid_positions = [pos for pos in valid_positions if all(utils.calculate_distance(pos, form_tile) > 8 for form_tile in formation_tiles)]
    valid_positions = sorted([pos for pos in valid_positions if game.movement.check_simple_traversable(pos)])
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

    print("Done!")
