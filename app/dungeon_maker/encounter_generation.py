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

    valid_classes = [
        "Mercenary",
        "Soldier",
        "Fighter",
    ]

    def apply(self, game, rect: Tuple[int, int, int, int], tilemap: TileMapObject, 
              enemy_level: int, encounter_uid: int, rng: static_random.LCG):
        x, y, width, height = rect
        area = (width - x) * (height - y)
        max_number_of_units = max(5, area // 2)

        klass = rng.choice(self.valid_classes)

        # Place units on board
        all_positions = rng.shuffle(
            sorted(utils.tuple_add((x, y), utils.itergrid(width, height))))
        for _ in range(max_number_of_units):
            position = next(all_positions)
            unit = create_unit(game, klass, enemy_level, encounter_uid)
            action.do(action.RegisterUnit(unit))
            action.do(action.ArriveOnMap(unit, position))

encounters = [
    Basic()
]

def get_items(self, game, klass: NID, level: int, rng: static_random.LCG) -> List[NID]:
    klass_prefab = DB.classes.get(klass)
    # Figure out what kind of weapon this unit can wield
    usable_weapon_types: List[NID] = []
    for nid, wexp_gain in klass_prefab.wexp_gain:
        if wexp_gain.usable:
            usable_weapon_types.append(nid)

    weapon_type = rng.choice(usable_weapon_types)
    match weapon_type:
        case 'Sword':
            return ['Bronze Sword']
        case 'Lance':
            return ['Bronze Lance']
        case 'Axe':
            return ['Bronze Axe']
    return []

def create_unit(self, game, klass: NID, level: int, ai_group: NID) -> UnitObject:
    """
    Given a desired unit's class, level, and ai_group,
    creates and returns the newly created unit
    """
    unit_nid = str_utils.get_next_int('201', [unit.nid for unit in game.units])
    items: List[NID] = get_items(game, klass, level)
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
