from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from app.utilities.typing import NID, Pos
from app.utilities import utils, str_utils
from app.utilities.static_random import LCG

from app.data.database.database import DB
from app.data.database.level_units import GenericUnit

from app.engine import action
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.unit import UnitObject
from app.data.database.items import ItemPrefab

if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap

def calculate_cost(unit: UnitObject) -> float:
    k = DB.classes.get(unit.klass)
    if 'LowLevel' in k.tags:
        return 0.75
    elif 'MidLevel' in k.tags:
        return 1
    elif 'HighLevel' in k.tags:
        return 1.5
    else:
        return 1

def convert_level_to_item_tier(level: int) -> str:
    if 1 <= level <= 5:
        return 'Bronze'
    elif 6 <= level <= 12:
        return 'Iron'
    elif 13 <= level <= 19:
        return 'Steel'
    elif 20 <= level <= 32:
        return 'Silver'
    else:
        return 'Mithril'

def get_items(game, klass: NID, level: int, rng: LCG) -> List[NID]:
    """
    Returns list of items unit should start with
    """
    klass_prefab = DB.classes.get(klass)
    tier = convert_level_to_item_tier(level)

    # Figure out what kind of weapon this unit can wield
    usable_weapon_types: List[NID] = []
    for nid, wexp_gain in klass_prefab.wexp_gain.items():
        if wexp_gain.usable:
            usable_weapon_types.append(nid)

    weapon_type = rng.choice(usable_weapon_types)

    def is_weapon_type(item: ItemPrefab, weapon_type: NID):
        return (item.weapon_type and item.weapon_type.value == weapon_type) \
            or (item.item_prefab and DB.items.get(item.item_prefab.value).weapon_type 
                and DB.items.get(item.item_prefab.value).weapon_type.value == weapon_type)

    item_prefabs = DB.items.values()
    item_prefabs = [
        i for i in item_prefabs 
        if is_weapon_type(i, weapon_type)
        and i.item_tags
        and tier in i.item_tags.value
    ]

    primary = rng.choice(item_prefabs)
    return [primary.nid]

def create_unit(game, klass: NID, level: int, ai_group: NID, rng: LCG) -> UnitObject:
    """
    Given a desired unit's class, level, and ai_group,
    creates and returns the newly created unit
    """
    unit_nid = str_utils.get_next_int('201', [unit.nid for unit in game.units])
    items: List[NID] = get_items(game, klass, level, rng)
    unit_prefab = GenericUnit(unit_nid, None, level, klass, "Enemy", items, [], "enemy", "Defend", ai_group=ai_group)
    unit = UnitObject.from_prefab(unit_prefab, game.current_mode)
    unit.party = game.current_party
    return unit

def get_valid_classes(level: int, tag: str) -> List[NID]:
    if level <= 4:
        level_tags = ["LowLevel",]
    elif level <= 10:
        level_tags = ["LowLevel", "MidLevel"]
    else:
        level_tags = ["LowLevel", "MidLevel", "HighLevel"]

    klasses = []
    for klass in DB.classes:
        if any(t in klass.tags for t in level_tags) and tag in klass.tags:
            klasses.append(klass.nid)
    return klasses

@dataclass
class EnemyEncounter:
    nid: NID
    weight: float

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG):
        pass

@dataclass
class Basic(EnemyEncounter):
    nid = "basic"
    weight = 0.3
    num_units = 4
    nearby = 3

    affix_unit_chance = 0.5
    affix_classes = [
        "Archer",
        "Cleric",
        "Mage",
        "Seeress",
        "Sorceror",
        "Thief",
        "Sentinel",
    ]

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG) -> Tuple[List[Pos], float]:
        """
        Places the enemy encounter on the map
        Returns the positions placed at, plus the cost
        """
        klass = rng.choice(get_valid_classes(enemy_level, tag))

        # Place units on board
        valid_positions = [p for p in dungeon_tilemap.get_open_tiles() if utils.calculate_distance(p, pos) <= Basic.nearby]
        rng.shuffle(valid_positions)
        all_positions = iter(valid_positions)

        used_positions: List[Pos] = []
        total_cost: float = 0
        for _ in range(Basic.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        # Affix unit
        if rng.random() < Basic.affix_unit_chance:
            affix_klass = rng.choice(Basic.affix_classes)
            position = next(all_positions)
            unit = create_unit(game, affix_klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        return used_positions, total_cost


@dataclass
class TwoTypes(EnemyEncounter):
    nid = "two_types"
    weight = 0.3
    num_units = 6
    nearby = 4

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG) -> Tuple[List[Pos], float]:
        klasses = get_valid_classes(enemy_level, tag).copy()
        klass1 = rng.choice(klasses)
        klasses.remove(klass1)
        klass2 = rng.choice(get_valid_classes(enemy_level, tag))

        # Place units on board
        valid_positions = [p for p in dungeon_tilemap.get_open_tiles() if utils.calculate_distance(p, pos) <= TwoTypes.nearby]
        rng.shuffle(valid_positions)
        all_positions = iter(valid_positions)

        used_positions: List[Pos] = []
        total_cost: float = 0
        for idx in range(TwoTypes.num_units):
            if idx % 2 == 1:
                klass = klass2
            else:
                klass = klass1
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        return used_positions, total_cost

@dataclass
class Leader(EnemyEncounter):
    nid = "leader"
    weight = 0.3
    nearby = 3
    num_units = 4

    leader_classes = [
        "Archer",
        "Sorceror",
        "Mercenary",
        "Myrmidon",
        "Sentinel",
        "Dracoknight",
        "Falcoknight",
    ]

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG) -> Tuple[List[Pos], float]:
        klass = rng.choice(get_valid_classes(enemy_level, tag))
        leader_klass = rng.choice(Leader.leader_classes)

        # Place units on board
        valid_positions = [p for p in dungeon_tilemap.get_open_tiles() if utils.calculate_distance(p, pos) <= Leader.nearby]
        rng.shuffle(valid_positions)
        all_positions = iter(valid_positions)

        used_positions: List[Pos] = []
        total_cost: float = 0
        for idx in range(Leader.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        # Place leader 5 levels ahead
        position = next(all_positions)
        unit = create_unit(game, leader_klass, enemy_level + 5, encounter_uid, rng)
        action.do(action.RegisterUnit(unit))
        action.do(action.ArriveOnMap(unit, position))
        used_positions.append(position)
        total_cost += calculate_cost(unit)

        return used_positions, total_cost

@dataclass
class Elite(EnemyEncounter):
    nid = "elite"
    weight = 0.3
    nearby = 3
    num_units = 3

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG) -> Tuple[List[Pos], float]:
        klass = rng.choice(get_valid_classes(enemy_level, tag))

        # Place units on board
        valid_positions = [p for p in dungeon_tilemap.get_open_tiles() if utils.calculate_distance(p, pos) <= Elite.nearby]
        rng.shuffle(valid_positions)
        all_positions = iter(valid_positions)

        used_positions: List[Pos] = []
        total_cost: float = 0
        for idx in range(Elite.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level + 2, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        return used_positions, total_cost

@dataclass
class Weak(EnemyEncounter):
    nid = "weak"
    weight = 0.1
    num_units = 8
    nearby = 5

    weak_classes = [
        "Soldier",
        "Raider",
    ]

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, 
              tag: str, rng: LCG) -> Tuple[List[Pos], float]:
        """
        Places the enemy encounter on the map
        Returns the positions placed at, plus the cost
        """
        klass = rng.choice(Weak.weak_classes)

        # Place units on board
        valid_positions = [p for p in dungeon_tilemap.get_open_tiles() if utils.calculate_distance(p, pos) <= Weak.nearby]
        rng.shuffle(valid_positions)
        all_positions = iter(valid_positions)

        used_positions: List[Pos] = []
        total_cost: float = 0
        for _ in range(Weak.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level - 2, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))
            used_positions.append(position)
            total_cost += calculate_cost(unit)

        return used_positions, total_cost

ENEMY_ENCOUNTERS = [
    Basic,
    TwoTypes,
    Leader,
    Elite,
    Weak,
]
