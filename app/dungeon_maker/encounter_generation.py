from typing import List, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from app.utilities.typing import NID, Pos
from app.utilities import utils, static_random
from app.utilities.static_random import LCG

from app.data.database.database import DB
from app.events import regions

from app.engine import action, engine
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.region import RegionObject

from app.dungeon_maker import enemy_encounters


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

class NonEnemyEncounter:
    nid: NID
    requirements: EncounterRequirements
    weight: float

    @staticmethod
    def apply(game, pos: Pos, dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, rng: LCG):
        pass

class Empty(NonEnemyEncounter):
    nid: NID = 'empty'
    requirements: EncounterRequirements = EncounterRequirements()
    weight: float = 1.0

    @staticmethod
    def apply(game, rect: Tuple[int, int, int, int], dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, rng: LCG):
        pass

class Treasure(NonEnemyEncounter):
    nid: NID = 'empty'
    requirements: EncounterRequirements = EncounterRequirements()
    weight: float = 0.5

    @staticmethod
    def apply(game, rect: Tuple[int, int, int, int], dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, enemy_level: int, encounter_uid: int, rng: LCG):
        x, y, width, height = rect
        positions = sorted(utils.tuple_add((x, y), utils.itergrid(width, height)))

        all_positions = rng.shuffle(positions)
        position = next(all_positions)

        # Add Map Anim
        action.do(action.AddMapAnim("Treasure", position, 1.0, engine.BlendMode.NONE))

        # Add Region
        x, y = position
        name = f"Treasure_{x}_{y}"
        new_region = RegionObject(name, regions.RegionType.EVENT)
        new_region.position = position
        new_region.size = (1, 1)
        new_region.sub_nid = "Chest"
        new_region.only_once = True

        game.register_region(new_region)
        action.do(action.AddRegion(new_region))

def place_enemies(game, dungeon_theme: NID, dungeon_tilemap: DungeonTileMap, 
                  tilemap: TileMapObject, enemy_level: int, enemy_budget: float, rng: LCG):
    current_budget: float = enemy_budget
    used_enemy_positions: Set[Pos] = {}
    encounter_uid = 0
    while current_budget > 0:
        # Pick a random enemy encounter type
        idx = static_random.weighted_choice([e.weight for e in enemy_encounters.ENEMY_ENCOUNTERS], rng)
        enemy_encounter_type = enemy_encounters.ENEMY_ENCOUNTERS[idx]
        # Pick a random point on the tilemap that's far away from other points
        pos = rng.choice(dungeon_tilemap.get_open_tiles())
        positions, cost = enemy_encounter_type.apply(game, pos, dungeon_tilemap, tilemap, enemy_level, encounter_uid, rng)
        used_enemy_positions |= set(positions)
        current_budget -= cost

def place_encounters(game, dungeon_tilemap: DungeonTileMap, tilemap: TileMapObject,
                     enemy_level: int, floor_level: int, dungeon_theme: NID, seed: int):
    rng = static_random.LCG(seed)
    num_open_tiles = len(dungeon_tilemap.get_open_tiles())
    enemy_budget = 1 * (32 / 148) * num_open_tiles * (1 + enemy_level * 0.1) * (1 + floor_level * 0.1)
    print(f"Enemy Budget: {enemy_budget}")
    # Non-enemies
    for idx, section in enumerate(dungeon_tilemap.sections.values()):
        if section.has_full_room():
            valid_encounters = [e for e in ENCOUNTERS if e.requirements.meets(section.room.width, section.room.height, dungeon_theme, floor_level)]
            encounter = static_random.weighted_choice([e.weight for e in valid_encounters], rng)
            encounter.apply(game, section.room.get_rect(), tilemap, enemy_level, idx, rng)
    # Enemies
    place_enemies(game, dungeon_theme, tilemap, enemy_level, enemy_budget, rng)

ENCOUNTERS = [
    Empty,
    Treasure,
]
