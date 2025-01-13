from __future__ import annotations

from typing import List, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field

from app.constants import TILEWIDTH, TILEHEIGHT

from app.utilities.typing import NID, Pos
from app.utilities import utils, static_random
from app.utilities.static_random import LCG

from app.events import regions

from app.engine import action, engine
from app.engine.objects.tilemap import TileMapObject, LayerObject
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
    def apply(game, rect: Tuple[int, int, int, int], dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, dungeon_palette: str, 
              enemy_level: int, encounter_uid: int, rng: LCG):
        pass

class Empty(NonEnemyEncounter):
    nid: NID = 'empty'
    requirements: EncounterRequirements = EncounterRequirements()
    weight: float = 1.0

    @staticmethod
    def apply(game, rect: Tuple[int, int, int, int], dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, dungeon_palette: str, 
              enemy_level: int, encounter_uid: int, rng: LCG):
        pass

class Treasure(NonEnemyEncounter):
    nid: NID = 'empty'
    requirements: EncounterRequirements = EncounterRequirements()
    weight: float = 0.5

    @staticmethod
    def apply(game, rect: Tuple[int, int, int, int], dungeon_tilemap: DungeonTileMap, 
              tilemap: TileMapObject, dungeon_palette: str, 
              enemy_level: int, encounter_uid: int, rng: LCG):
        x, y, width, height = rect
        positions = []
        for (i, j) in utils.itergrid(width, height):
            positions.append((x + i, y + j))
        rng.shuffle(positions)
        position = next(iter(positions))

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

        # Modify tilemap
        treasure_im_fn = f'app/dungeon_maker/palettes/{dungeon_palette}/treasure.png'
        treasure_im = engine.image_load(treasure_im_fn)
        treasure_sprite = engine.subsurface(treasure_im, (0, 0, 20, 16))
        open_treasure_sprite = engine.subsurface(treasure_im, (0, 16, 20, 16))

        # Switch terrain & modify base image
        pixel_pos = (position[0] * TILEWIDTH, position[1] * TILEHEIGHT)
        base_layer = tilemap.layers[0]
        base_layer.terrain[position] = "Chest"
        base_layer.image.blit(treasure_sprite, pixel_pos)

        # Now create a new layer
        treasure_layer = LayerObject(name, False, tilemap)
        treasure_layer.visible = False
        treasure_layer.set_image(open_treasure_sprite)
        treasure_layer.pixel_bounds = [pixel_pos[0], pixel_pos[1], pixel_pos[0] + 20, pixel_pos[1] + 16]
        tilemap.layers.append(treasure_layer)


def _place_enemies(game, dungeon_theme: NID, dungeon_tilemap: DungeonTileMap, 
                   tilemap: TileMapObject, enemy_level: int, enemy_budget: float, 
                   enemy_tag: str, rng: LCG):
    START_DISTANCE = 5
    ENEMY_DISTANCE = 6
    current_budget: float = enemy_budget
    valid_enemy_positions: Set[Pos] = set(dungeon_tilemap.get_open_tiles())
    valid_enemy_positions -= game.target_system.find_manhattan_spheres(range(START_DISTANCE + 1), *dungeon_tilemap.get_start_pos())
    valid_enemy_positions: List[Pos] = list(sorted(valid_enemy_positions))
    encounter_uid = 0
    while current_budget > 0 and valid_enemy_positions:
        # Pick a random enemy encounter type
        idx = static_random.weighted_choice([e.weight for e in enemy_encounters.ENEMY_ENCOUNTERS], rng)
        enemy_encounter_type = enemy_encounters.ENEMY_ENCOUNTERS[idx]
        # Pick a random point on the tilemap that's far away from other enemies / players
        pos = rng.choice(valid_enemy_positions)
        positions, cost = enemy_encounter_type.apply(
                game, pos, dungeon_tilemap, 
                tilemap, enemy_level, encounter_uid, enemy_tag, rng)

        # Remove the positions near this group as valid
        valid_enemy_positions = set(valid_enemy_positions)
        for position in positions:
            valid_enemy_positions -= game.target_system.find_manhattan_spheres(range(ENEMY_DISTANCE + 1), *position)
        valid_enemy_positions = list(sorted(valid_enemy_positions))

        current_budget -= cost
        print(f"Type: {enemy_encounter_type}, Cost: {cost}, Remaining Budget: {current_budget}, Remaining Enemy Positions: {len(valid_enemy_positions)}")

def place_encounters(game, dungeon_tilemap: DungeonTileMap, tilemap: TileMapObject,
                     enemy_level: int, floor_level: int, dungeon_theme: NID, 
                     enemy_tag: str, dungeon_palette: str, seed: int):
    rng = static_random.LCG(seed)
    num_open_tiles = len(dungeon_tilemap.get_open_tiles())
    enemy_budget = 0.5 * (32 / 148) * num_open_tiles * (1 + enemy_level * 0.1) * (1 + floor_level * 0.1)
    print(f"Enemy Budget: {enemy_budget}")
    # Non-enemies
    for idx, section in enumerate(dungeon_tilemap.sections.values()):
        if section.has_full_room():
            valid_encounters = [e for e in ENCOUNTERS if e.requirements.meets(section.room.width, section.room.height, dungeon_theme, floor_level)]
            encounter_idx: int = static_random.weighted_choice([e.weight for e in valid_encounters], rng)
            encounter = valid_encounters[encounter_idx]
            encounter.apply(game, section.room.get_rect(), dungeon_tilemap, tilemap, dungeon_palette, enemy_level, idx, rng)
    # Enemies
    _place_enemies(game, dungeon_theme, dungeon_tilemap, tilemap, enemy_level, enemy_budget, enemy_tag, rng)

ENCOUNTERS = [
    Empty,
    Treasure,
]
