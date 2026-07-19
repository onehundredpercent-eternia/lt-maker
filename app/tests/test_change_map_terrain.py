import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import unittest
from unittest import mock
from unittest.mock import MagicMock

import pygame

from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FRAMES
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.data.database.database import DB
from app.data.database.levels import LevelPrefab
from app.data.database.map_terrain_associations import MapTerrainAssociations
from app.data.resources.resources import RESOURCES
from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.engine import action
from app.engine.objects.tilemap import TileMapObject
from app.engine.objects.prefab_tilemap import MapPrefabTileMapObject
from app.events import event_commands, event_functions, event_validators
from app.utilities import str_utils


def setUpModule():
    # engine.create_surface() calls Surface.convert()/.convert_alpha(),
    # which require an initialized display -- even the dummy SDL driver
    # needs a display mode set once.
    pygame.init()
    pygame.display.set_mode((1, 1))


SEED = 5


def make_small_grid():
    """4x4 all GRASS, with a 2-tile SEA blob so flood-fill re-render can be
    exercised (changing one SEA tile must redo the whole surviving blob)."""
    grid = {}
    for x in range(4):
        for y in range(4):
            grid[(x, y)] = Terrain.GRASS
    grid[(1, 1)] = Terrain.SEA
    grid[(2, 1)] = Terrain.SEA
    return grid


def make_small_prefab(nid) -> MapPrefab:
    prefab = MapPrefab(nid)
    prefab.set_new_terrain_grid((4, 4), make_small_grid())
    prefab.seed = SEED
    return prefab


def all_frame_bytes(tm):
    """RGBA bytes of the full image at every autotile frame index -- the
    same pixel-diff technique used in test_prefab_tilemap.py."""
    full_rect = (0, 0, tm.width * TILEWIDTH, tm.height * TILEHEIGHT)
    layer = tm.layers.get('base')
    frames = []
    for frame in range(AUTOTILE_FRAMES):
        layer.autotile_frame = frame
        frames.append(pygame.image.tobytes(tm.get_full_image(full_rect), 'RGBA'))
    return frames


class _PrefabLevelTestCaseMixin:
    """Shared scaffolding: a real running game singleton with a started
    map_prefab level, following the pattern in
    test_map_prefab_level_wiring.py's StartLevelMapPrefabWiringTests. Needed
    (rather than a bare MapPrefabTileMapObject) because
    ChangeMapMakerTerrain.do()/reverse() read/write the real global `game`
    (game.level.tilemap, game.board, game.boundary, game.action_log) --
    exactly like the turnwheel does."""

    LEVEL_NID: str
    MAP_PREFAB_NID: str

    @classmethod
    def setUpClass(cls):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        # RESOURCES.load() resets app.sprites.SPRITES (fresh BasicSprite
        # entries with image=None); normally app.engine.driver.start()
        # reloads the actual pygame Surfaces right after RESOURCES.load()
        # during real startup. Mirror that one step here.
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

    def setUp(self):
        # Global DB singleton -- reset so no other test's overrides leak in
        # (MapPrefabTileMapObject.get_terrain reads DB.map_terrain_associations).
        DB.map_terrain_associations = MapTerrainAssociations()

        self.map_prefab = make_small_prefab(self.MAP_PREFAB_NID)
        RESOURCES.map_prefabs.append(self.map_prefab)

        self.level_prefab = LevelPrefab(self.LEVEL_NID, 'Test Level')
        self.level_prefab.map_prefab = self.MAP_PREFAB_NID
        self.level_prefab.party = DB.parties[0].nid if len(DB.parties) else None
        DB.levels.append(self.level_prefab)

        # Drive the module-level singleton, not a fresh GameState(): both
        # action.py and event_functions.py import/reference this same `game`.
        from app.engine.game_state import game
        game.build_new()
        game.start_level(self.LEVEL_NID)
        self.game = game

    def tearDown(self):
        RESOURCES.map_prefabs.delete(self.map_prefab)
        DB.levels.delete(self.level_prefab)


class ChangeMapMakerTerrainActionTests(_PrefabLevelTestCaseMixin, unittest.TestCase):
    """Deliverable 1/2/4 (action-level): do/reverse/execute(redo) semantics
    on `action.ChangeMapMakerTerrain`."""

    LEVEL_NID = 'test_change_terrain_action_level'
    MAP_PREFAB_NID = 'test_change_terrain_action_map'

    def test_do_reverse_round_trip_simple_terrain_change(self):
        tm = self.game.level.tilemap
        self.assertIsInstance(tm, MapPrefabTileMapObject)

        before_terrain_grid = dict(tm.prefab.terrain_grid)
        before_autotile_set = set(tm.prefab.autotile_set)
        before_frames = all_frame_bytes(tm)

        act = action.ChangeMapMakerTerrain((3, 3), Terrain.FOREST)
        act.do()
        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(3, 3)])

        act.reverse()

        self.assertEqual(before_terrain_grid, tm.prefab.terrain_grid)
        self.assertEqual(before_autotile_set, tm.prefab.autotile_set)
        self.assertEqual(before_frames, all_frame_bytes(tm), "Pixels not byte-identical after reverse")

    def test_do_reverse_round_trip_erase(self):
        tm = self.game.level.tilemap

        before_terrain_grid = dict(tm.prefab.terrain_grid)
        before_frames = all_frame_bytes(tm)

        act = action.ChangeMapMakerTerrain((0, 0), None)
        act.do()
        self.assertNotIn((0, 0), tm.prefab.terrain_grid)

        act.reverse()

        self.assertEqual(before_terrain_grid, tm.prefab.terrain_grid)
        self.assertEqual(before_frames, all_frame_bytes(tm), "Pixels not byte-identical after reverse (erase case)")

    def test_do_reverse_round_trip_flood_fill_sea(self):
        tm = self.game.level.tilemap
        self.assertIn((2, 1), tm.prefab.autotile_set)

        before_terrain_grid = dict(tm.prefab.terrain_grid)
        before_autotile_set = set(tm.prefab.autotile_set)
        before_frames = all_frame_bytes(tm)

        # SEA is a flood-fill terrain -- changing one tile of the blob
        # must redo the whole surviving blob's rendering, not just this tile.
        act = action.ChangeMapMakerTerrain((2, 1), Terrain.GRASS)
        act.do()
        self.assertEqual(Terrain.GRASS, tm.prefab.terrain_grid[(2, 1)])

        act.reverse()

        self.assertEqual(before_terrain_grid, tm.prefab.terrain_grid)
        self.assertEqual(before_autotile_set, tm.prefab.autotile_set)
        self.assertEqual(before_frames, all_frame_bytes(tm), "Pixels not byte-identical after reverse (flood-fill case)")

    def test_unit_on_changed_tile_gets_terrain_status_refreshed(self):
        """Changing terrain under a standing unit must leave/arrive it (like
        AddRegion does for TERRAIN regions) so its terrain status skill is
        re-derived immediately: GRASS ('1' Plain, no status) -> FOREST
        ('2' Forest, 'Forest' status in testing_proj)."""
        from app.engine.objects.unit import UnitObject

        unit = UnitObject.from_prefab(DB.units.get('Artur'), self.game.current_mode)
        self.game.full_register(unit)
        self.game.arrive(unit, (3, 3))

        def unit_skill_nids():
            return {skill.nid for skill in unit.all_skills}

        self.assertNotIn('Forest', unit_skill_nids())

        act = action.ChangeMapMakerTerrain((3, 3), Terrain.FOREST)
        act.do()
        self.assertEqual('2', self.game.level.tilemap.get_terrain((3, 3)))
        self.assertIn('Forest', unit_skill_nids())
        # Unit stayed put and is still on the board
        self.assertEqual((3, 3), tuple(unit.position))
        self.assertIs(unit, self.game.board.get_unit((3, 3)))

        act.reverse()
        self.assertNotIn('Forest', unit_skill_nids())
        self.assertIs(unit, self.game.board.get_unit((3, 3)))

    def test_action_survives_action_log_serialization(self):
        """Regression: Terrain members must survive the pickle-based
        Action.save()/restore() path (turnwheel through a suspend save).
        The namedtuple+Enum mixin used to fail pickling; Action.save_obj's
        fallback then silently stored None -- this action's erase
        sentinel -- so turnwheel-through-a-save erased the tile."""
        import pickle

        tm = self.game.level.tilemap

        act = action.ChangeMapMakerTerrain((3, 3), Terrain.FOREST)
        act.do()

        class_name, ser_dict = act.save()
        self.assertEqual('ChangeMapMakerTerrain', class_name)
        # Suspend saves pickle the whole serialized action log to disk --
        # round-trip through actual pickle, not just save()/restore().
        ser_dict = pickle.loads(pickle.dumps(ser_dict))
        restored = getattr(action, class_name).restore(ser_dict)

        self.assertIs(Terrain.FOREST, restored.new_terrain)
        self.assertIs(Terrain.GRASS, restored.old_terrain)
        self.assertEqual((3, 3), tuple(restored.pos))

        restored.reverse()
        self.assertEqual(Terrain.GRASS, tm.prefab.terrain_grid[(3, 3)])

    def test_do_reverse_execute_redo_matches_from_scratch_render(self):
        tm = self.game.level.tilemap

        act = action.ChangeMapMakerTerrain((3, 3), Terrain.FOREST)
        act.do()
        act.reverse()
        act.execute()  # turnwheel-style redo -- base Action.execute() calls do()

        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(3, 3)])

        grid2 = make_small_grid()
        grid2[(3, 3)] = Terrain.FOREST
        prefab2 = MapPrefab(self.MAP_PREFAB_NID)
        prefab2.set_new_terrain_grid((4, 4), grid2)
        prefab2.seed = SEED
        tm2 = MapPrefabTileMapObject.from_prefab(prefab2)

        self.assertEqual(all_frame_bytes(tm2), all_frame_bytes(tm),
                          "Redone patch differs from a from-scratch render of the same grid")


class ChangeMapTerrainEventFunctionTests(_PrefabLevelTestCaseMixin, unittest.TestCase):
    """Deliverable 3/4 (event-function level): guards and the happy path
    for `event_functions.change_map_terrain`, and that a successful call
    lands an action.ChangeMapMakerTerrain in game.action_log."""

    LEVEL_NID = 'test_change_terrain_event_level'
    MAP_PREFAB_NID = 'test_change_terrain_event_map'

    def _make_fake_event(self):
        fake_event = MagicMock()
        fake_event.game = self.game  # the real singleton -- action.py reads it too
        fake_event.logger = MagicMock()
        # Real Event._parse_pos immediately returns tuples unchanged; stub
        # that behavior directly rather than dragging in a real Event.
        fake_event._parse_pos = lambda pos, is_float=False: pos
        return fake_event

    def test_change_map_terrain_applies_and_logs_action(self):
        fake_event = self._make_fake_event()
        tm = self.game.level.tilemap
        before_len = len(self.game.action_log.actions)

        event_functions.change_map_terrain(fake_event, (3, 3), 'FOREST')

        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(3, 3)])
        self.assertEqual(before_len + 1, len(self.game.action_log.actions))
        self.assertIsInstance(self.game.action_log.actions[-1], action.ChangeMapMakerTerrain)
        fake_event.logger.warning.assert_not_called()

    def test_change_map_terrain_erases_when_terrain_omitted(self):
        fake_event = self._make_fake_event()
        tm = self.game.level.tilemap

        event_functions.change_map_terrain(fake_event, (0, 0))

        self.assertNotIn((0, 0), tm.prefab.terrain_grid)
        fake_event.logger.warning.assert_not_called()

    def test_classic_parse_path_hands_function_a_string(self):
        # Regression: MapMakerTerrain.convert() used to return a live
        # Terrain member, so the classic parse path (.event scripts, debug
        # menu -- event.py's convert_parse + run_command) handed
        # change_map_terrain an enum and it crashed on .upper(). The
        # python-eventing wrapper never converts (plain Validator), so only
        # this path was affected. Mirror event.py exactly: parse the raw
        # command text, convert_parse it, snake-case the keys, call.
        command, _ = event_commands.parse_text_to_command('change_map_terrain;3,3;forest')
        parameters, flags = event_commands.convert_parse(command, None)
        parameters = {str_utils.camel_to_snake(k): v for k, v in parameters.items()}
        self.assertIsInstance(parameters['map_maker_terrain'], str)

        fake_event = self._make_fake_event()
        event_functions.change_map_terrain(fake_event, **parameters, flags=flags)

        tm = self.game.level.tilemap
        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(3, 3)])
        fake_event.logger.warning.assert_not_called()

    def test_change_map_terrain_accepts_lowercase_terrain_name(self):
        fake_event = self._make_fake_event()
        tm = self.game.level.tilemap

        event_functions.change_map_terrain(fake_event, (3, 3), 'forest')

        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(3, 3)])

    def test_non_prefab_level_is_a_no_op(self):
        tilemap_prefab = RESOURCES.tilemaps.get('Prologue')
        self.game.level.tilemap = TileMapObject.from_prefab(tilemap_prefab)
        fake_event = self._make_fake_event()

        with mock.patch.object(action, 'do') as mock_do:
            event_functions.change_map_terrain(fake_event, (0, 0), 'GRASS')

        mock_do.assert_not_called()
        fake_event.logger.warning.assert_called_once()

    def test_out_of_bounds_position_is_a_no_op(self):
        fake_event = self._make_fake_event()
        tm = self.game.level.tilemap
        before_terrain_grid = dict(tm.prefab.terrain_grid)

        with mock.patch.object(action, 'do') as mock_do:
            event_functions.change_map_terrain(fake_event, (100, 100), 'GRASS')

        mock_do.assert_not_called()
        fake_event.logger.warning.assert_called_once()
        self.assertEqual(before_terrain_grid, tm.prefab.terrain_grid)

    def test_bogus_terrain_name_is_a_no_op(self):
        fake_event = self._make_fake_event()
        tm = self.game.level.tilemap
        before_terrain_grid = dict(tm.prefab.terrain_grid)

        with mock.patch.object(action, 'do') as mock_do:
            event_functions.change_map_terrain(fake_event, (0, 0), 'NOT_A_REAL_TERRAIN')

        mock_do.assert_not_called()
        fake_event.logger.warning.assert_called_once()
        self.assertEqual(before_terrain_grid, tm.prefab.terrain_grid)


if __name__ == '__main__':
    unittest.main()
