"""
Encounter generation:
1. Find each room of appropriate size
2. Randomly select a kind of encounter that fits the room
3. If it requires changing the room slightly, do so
4. Place the appropriate units down in random spots in the room
"""
from typing import List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from app.utilities.typing import NID
from app.utilities import utils, str_utils, static_random

from app.data.database.database import DB
from app.data.database.level_units import GenericUnit

from app.engine import action
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.unit import UnitObject

if TYPE_CHECKING:
    from app.dungeon_maker.terrain_generation import DungeonTileMap

@dataclass
class EncounterRequirements:
    min_width: int = None
    max_width: int = None
    min_height: int = None
    max_height: int = None
    invalid_themes: List[NID] = field(default_factory=list)
    min_floor_level: int = None
    max_floor_level: int = None

    def meets(self, width: int, height: int, theme: NID, floor_level: int) -> bool:
        valid = True

        # Check room size
        if self.min_width is not None:
            valid &= (width >= self.min_width)
        if self.max_width is not None:
            valid &= (width <= self.max_width)
        if self.min_height is not None:
            valid &= (height >= self.min_height)
        if self.max_height is not None:
            valid &= (height <= self.max_height)

        # Check theme
        valid &= (theme not in self.invalid_themes)

        # Check floor level
        if self.min_floor_level is not None:
            valid &= (floor_level >= self.min_floor_level)
        if self.max_floor_level is not None:
            valid &= (floor_level <= self.max_floor_level)

        return valid

@dataclass
class Encounter:
    nid: NID
    requirements: EncounterRequirements
    weight: float

    def apply(self, rect: Tuple[int, int, int, int], tilemap: TileMapObject):
        pass

@dataclass
class Basic(Encounter):
    nid = "basic"
    requirements = EncounterRequirements(min_width=3, min_height=3)
    weight = 1

    num_units = 4
    valid_classes = [
        "Thief",
        "Mercenary",
        "Soldier",
        "Cavalier"
        "Armor",
        "Fighter",
        "Raider",
        "Mage",
    ]

    affix_unit_chance = 0.5
    affix_classes = [
        "Archer",
        "Cleric",
        "Mage",
        "Sorceror",
        "Thief"
    ]

    def apply(self, game, rect: Tuple[int, int, int, int], tilemap: TileMapObject, 
              enemy_level: int, encounter_uid: int, rng: static_random.LCG):
        x, y, width, height = rect

        klass = rng.choice(self.valid_classes)

        # Place units on board
        all_positions = rng.shuffle(
            sorted(utils.tuple_add((x, y), utils.itergrid(width, height))))
        for _ in range(self.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))

        # Affix unit
        if rng.random() < self.affix_unit_chance:
            affix_klass = rng.choice(self.affix_classes)
            position = next(all_positions)
            unit = create_unit(game, affix_klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))


@dataclass
class TwoTypes(Encounter):
    nid = "two_types"
    requirements = EncounterRequirements(min_width=3, min_height=3)
    weight = 0.75

    num_units = 6
    valid_classes = [
        "Thief",
        "Myrmidon",
        "Mercenary",
        "Soldier",
        "Cavalier"
        "Armor",
        "Fighter",
        "Raider",
        "Archer",
        "Mage",
        "Sorceror",
    ]

    def apply(self, game, rect: Tuple[int, int, int, int], tilemap: TileMapObject, 
              enemy_level: int, encounter_uid: int, rng: static_random.LCG):
        x, y, width, height = rect

        klass1 = rng.choice(self.valid_classes)
        self.valid_classes.remove(klass1)
        klass2 = rng.choice(self.valid_classes)

        # Place units on board
        all_positions = rng.shuffle(
            sorted(utils.tuple_add((x, y), utils.itergrid(width, height))))
        for idx in range(self.num_units):
            if idx % 2 == 1:
                klass = klass2
            else:
                klass = klass1
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))

@dataclass
class Leader(Encounter):
    nid = "leader"
    requirements = EncounterRequirements(min_width=3, min_height=3)
    weight = 0.5

    num_units = 4
    valid_classes = [
        "Thief",
        "Mercenary",
        "Soldier",
        "Cavalier"
        "Armor",
        "Fighter",
        "Raider",
        "Mage",
    ]

    affix_classes = [
        "Archer",
        "Cleric",
        "Mage",
        "Sorceror",
        "Thief"
    ]

    def apply(self, game, rect: Tuple[int, int, int, int], tilemap: TileMapObject, 
              enemy_level: int, encounter_uid: int, rng: static_random.LCG):
        x, y, width, height = rect

        klass = rng.choice(self.valid_classes)
        leader_klass = rng.choice(self.valid_classes)

        # Place units on board
        all_positions = rng.shuffle(
            sorted(utils.tuple_add((x, y), utils.itergrid(width, height))))
        for idx in range(self.num_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))

        # Place leader 5 levels ahead
        position = next(all_positions)
        unit = create_unit(game, leader_klass, enemy_level + 5, encounter_uid)
        action.do(action.RegisterUnit(unit))
        action.do(action.ArriveOnMap(unit, position))

        # Affix unit
        if rng.random() < self.affix_unit_chance:
            affix_klass = rng.choice(self.affix_classes)
            position = next(all_positions)
            unit = create_unit(game, affix_klass, enemy_level, encounter_uid, rng)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))

encounters = [
    Basic(),
    TwoTypes(),
    Leader(),
]

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

def get_items(game, klass: NID, level: int, rng: static_random.LCG) -> List[NID]:
    """
    Returns list of items unit should start with
    """
    klass_prefab = DB.classes.get(klass)
    tier = convert_level_to_item_tier(level)

    # Figure out what kind of weapon this unit can wield
    usable_weapon_types: List[NID] = []
    for nid, wexp_gain in klass_prefab.wexp_gain:
        if wexp_gain.usable:
            usable_weapon_types.append(nid)

    weapon_type = rng.choice(usable_weapon_types)

    def is_weapon_type(item: ItemPrefab, weapon_type: NID):
        return item.weapon_type == weapon_type or (item.item_prefab and DB.items.get(item.item_prefab.value).weapon_type == weapon_type)

    item_prefabs = DB.items.values()
    primary_item_prefabs = [i for i in item_prefabs 
        if is_weapon_type(i, weapon_type)
        and tier in i.item_tags and 'Primary' in i.item_tags]
    secondary_item_prefabs = [i for i in item_prefabs if is_weapon_type(i, weapon_type) and tier in i.item_tags and 'Secondary' in i.item_tags]

    primary = rng.choice(primary_item_prefabs)
    secondary = rng.choice(secondary_item_prefabs)
    return [primary] + [secondary]

def create_unit(game, klass: NID, level: int, ai_group: NID, rng: static_random.LCG) -> UnitObject:
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

def place_encounters(self, game, dungeon_tilemap: DungeonTileMap, tilemap: TileMapObject,
                     enemy_level: int, floor_level: int, dungeon_theme: NID, seed: int):
    rng = static_random.LCG(seed)
    for idx, section in enumerate(dungeon_tilemap.sections.values()):
        if section.has_full_room():
            valid_encounters = [e for e in encounters if e.requirements.meets(section.room.width, section.room.height, dungeon_theme, floor_level)]
            encounter = static_random.weighted_choice([e.weight for e in valid_encounters], rng)
            encounter.apply(game, section.room.get_rect(), tilemap, enemy_level, idx, rng)
