import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import unittest
from unittest import mock
from unittest.mock import MagicMock

import pygame

from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.data.database.database import DB
from app.data.database.levels import LevelPrefab
from app.data.database.map_terrain_associations import MapTerrainAssociations
from app.data.resources.resources import RESOURCES
from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.engine.objects.level import LevelObject
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.prefab_tilemap import MapPrefabTileMapObject
from app.utilities.data import Data
from app.events import event_functions
from app.engine import action


def setUpModule():
    # engine.create_surface() calls Surface.convert()/.convert_alpha(),
    # which require an initialized display -- even the dummy SDL driver
    # needs a display mode set once.
    pygame.init()
    pygame.display.set_mode((1, 1))


def make_small_grid():
    grid = {}
    for x in range(4):
        for y in range(4):
            grid[(x, y)] = Terrain.GRASS
    grid[(1, 1)] = Terrain.SEA
    return grid


def make_small_prefab(nid='test_wiring_map', seed=5) -> MapPrefab:
    prefab = MapPrefab(nid)
    prefab.set_new_terrain_grid((4, 4), make_small_grid())
    prefab.seed = seed
    return prefab


class LevelPrefabMapPrefabFieldTests(unittest.TestCase):
    """Deliverable 6a: LevelPrefab.map_prefab save/restore round-trip."""

    def test_round_trip_with_map_prefab_set(self):
        level = LevelPrefab('lvl1', 'Test Level')
        level.map_prefab = 'some_map_prefab_nid'

        s_dict = level.save()
        self.assertEqual('some_map_prefab_nid', s_dict['map_prefab'])

        restored = LevelPrefab.restore(s_dict)
        self.assertEqual('some_map_prefab_nid', restored.map_prefab)

    def test_round_trip_with_map_prefab_unset(self):
        level = LevelPrefab('lvl2', 'Test Level 2')
        self.assertIsNone(level.map_prefab)

        s_dict = level.save()
        self.assertIsNone(s_dict['map_prefab'])

        restored = LevelPrefab.restore(s_dict)
        self.assertIsNone(restored.map_prefab)

    def test_restore_legacy_dict_missing_key_defaults_to_none(self):
        level = LevelPrefab('lvl3', 'Test Level 3')
        level.map_prefab = 'should_not_survive'
        s_dict = level.save()
        # Simulate an old project's on-disk dict, saved before this field
        # existed.
        del s_dict['map_prefab']

        restored = LevelPrefab.restore(s_dict)
        self.assertIsNone(restored.map_prefab)


class LevelObjectSaveRestoreDispatchTests(unittest.TestCase):
    """Deliverable 6b: LevelObject save/restore dispatches on the tilemap's
    'kind' tag to the right TileMapObject subclass."""

    def setUp(self):
        # Global DB singleton -- reset so no other test's overrides leak in
        # (MapPrefabTileMapObject.get_terrain reads DB.map_terrain_associations).
        DB.map_terrain_associations = MapTerrainAssociations()

    def _make_bare_level(self, nid, tilemap):
        level = LevelObject()
        level.nid = nid
        level.name = nid
        level.tilemap = tilemap
        level.bg_tilemap = None
        level.party = None
        level.music = {}
        level.objective = {}
        level.units = Data()
        level.regions = Data()
        level.unit_groups = Data()
        level.ai_groups = Data()
        return level

    def test_save_restore_dispatches_to_map_prefab_tilemap(self):
        prefab = make_small_prefab()
        tilemap = MapPrefabTileMapObject.from_prefab(prefab)
        level = self._make_bare_level('lvl_prefab', tilemap)

        s_dict = level.save()
        self.assertEqual('map_prefab', s_dict['tilemap']['kind'])

        game_stub = MagicMock()
        restored = LevelObject.restore(s_dict, game_stub)

        self.assertIsInstance(restored.tilemap, MapPrefabTileMapObject)
        self.assertEqual(tilemap.prefab.terrain_grid, restored.tilemap.prefab.terrain_grid)
        self.assertEqual(tilemap.prefab.autotile_set, restored.tilemap.prefab.autotile_set)

    def test_save_restore_dispatches_to_plain_tilemap(self):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        tilemap_prefab = RESOURCES.tilemaps.get('Prologue')
        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        level = self._make_bare_level('lvl_plain', tilemap)

        s_dict = level.save()
        self.assertEqual('tilemap', s_dict['tilemap']['kind'])

        game_stub = MagicMock()
        restored = LevelObject.restore(s_dict, game_stub)

        self.assertIsInstance(restored.tilemap, TileMapObject)
        self.assertNotIsInstance(restored.tilemap, MapPrefabTileMapObject)
        self.assertEqual(tilemap.nid, restored.tilemap.nid)

    def test_old_save_dict_without_kind_key_still_restores_as_plain_tilemap(self):
        """Verification checklist item 3: an OLD save dict (no 'kind' key,
        as every save made before Phase 4) must still restore correctly."""
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        tilemap_prefab = RESOURCES.tilemaps.get('Prologue')
        tilemap = TileMapObject.from_prefab(tilemap_prefab)
        level = self._make_bare_level('lvl_legacy', tilemap)

        s_dict = level.save()
        del s_dict['tilemap']['kind']  # Simulate a pre-Phase-4 save
        self.assertNotIn('kind', s_dict['tilemap'])

        game_stub = MagicMock()
        restored = LevelObject.restore(s_dict, game_stub)

        self.assertIsInstance(restored.tilemap, TileMapObject)
        self.assertNotIsInstance(restored.tilemap, MapPrefabTileMapObject)
        self.assertEqual(tilemap.nid, restored.tilemap.nid)


class ShowHideLayerMapPrefabGuardTests(unittest.TestCase):
    """Deliverable 4: show_layer/hide_layer must no-op (with a warning) on
    a map_prefab level instead of reaching action.py's _leave(), which
    reads layer.terrain -- always empty on this tilemap type."""

    def setUp(self):
        DB.map_terrain_associations = MapTerrainAssociations()
        prefab = make_small_prefab()
        self.tilemap = MapPrefabTileMapObject.from_prefab(prefab)

    def _make_fake_event(self):
        fake_event = MagicMock()
        fake_event.game.level.tilemap = self.tilemap
        fake_event.logger = MagicMock()
        return fake_event

    def test_show_layer_no_ops_on_map_prefab_tilemap(self):
        fake_event = self._make_fake_event()
        with mock.patch.object(action, 'do') as mock_do:
            event_functions.show_layer(fake_event, 'base')
        mock_do.assert_not_called()
        fake_event.logger.warning.assert_called_once()

    def test_hide_layer_no_ops_on_map_prefab_tilemap(self):
        fake_event = self._make_fake_event()
        with mock.patch.object(action, 'do') as mock_do:
            event_functions.hide_layer(fake_event, 'base')
        mock_do.assert_not_called()
        fake_event.logger.warning.assert_called_once()


class StartLevelMapPrefabWiringTests(unittest.TestCase):
    """Deliverable 6c: end-to-end game.start_level() with a map_prefab
    level, using the real GameState (not the mocked one other tests use --
    start_level needs a fully functional game to build camera/cursor/board)."""

    LEVEL_NID = 'test_wiring_start_level'
    MAP_PREFAB_NID = 'test_wiring_start_level_map'

    def setUp(self):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        DB.map_terrain_associations = MapTerrainAssociations()

        # RESOURCES.load() resets app.sprites.SPRITES (fresh BasicSprite
        # entries with image=None); normally app.engine.driver.start()
        # reloads the actual pygame Surfaces right after RESOURCES.load()
        # during real startup. Mirror that one step here, or the (engine-
        # bundled, project-independent) cursor/arrow sprites LevelCursor
        # needs stay unloaded and it crashes on a None Surface.
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

        # Inject a small MapPrefab resource and a level that opts into it,
        # in-memory only -- nothing touches disk.
        self.map_prefab = make_small_prefab(nid=self.MAP_PREFAB_NID)
        RESOURCES.map_prefabs.append(self.map_prefab)

        self.level_prefab = LevelPrefab(self.LEVEL_NID, 'Test Wiring Level')
        self.level_prefab.map_prefab = self.MAP_PREFAB_NID
        self.level_prefab.party = DB.parties[0].nid if len(DB.parties) else None
        DB.levels.append(self.level_prefab)

        self.game = None

    def tearDown(self):
        RESOURCES.map_prefabs.delete(self.map_prefab)
        DB.levels.delete(self.level_prefab)

    def test_start_level_builds_map_prefab_tilemap_and_board(self):
        # Must drive the module-level singleton, not a fresh GameState():
        # engine consumers (minimap, fog of war, etc.) import `game`
        # directly, so a local instance would leave them unexercised.
        from app.engine.game_state import game
        game.build_new()
        self.game = game
        game.start_level(self.LEVEL_NID)

        self.assertIsInstance(game.level.tilemap, MapPrefabTileMapObject)
        self.assertEqual(self.MAP_PREFAB_NID, game.level.tilemap.nid)
        self.assertIsNotNone(game.board)
        # get_terrain works at a position -- board built successfully off
        # the MapPrefabTileMapObject's terrain association lookup.
        self.assertEqual('1', game.level.tilemap.get_terrain((0, 0)))  # GRASS -> Plains

        # Consumer smoke: these all read the global game singleton and
        # consume the tilemap only through its public contract.
        for unit_type in DB.mcost.unit_types:
            self.assertIsNotNone(game.board.get_movement_grid(unit_type))
        self.assertTrue(game.board.fog_of_war_grids)
        from app.engine.minimap import MiniMap
        minimap = MiniMap(game.level.tilemap, game.units)
        self.assertIsNotNone(minimap.surf)


if __name__ == '__main__':
    unittest.main()
