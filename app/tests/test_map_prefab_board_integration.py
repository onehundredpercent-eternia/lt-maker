import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import unittest
from unittest.mock import MagicMock

import pygame

from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.data.database.database import DB
from app.data.database.levels import LevelPrefab
from app.data.database.map_terrain_associations import MapTerrainAssociations
from app.data.resources.resources import RESOURCES
from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.engine.game_board import GameBoard
from app.engine.objects.unit import UnitObject
from app.utilities import utils


def setUpModule():
    # engine.create_surface() calls Surface.convert()/.convert_alpha(),
    # which require an initialized display -- even the dummy SDL driver
    # needs a display mode set once.
    pygame.init()
    pygame.display.set_mode((1, 1))


def make_grid():
    """6x6, mostly GRASS, with one FOREST tile and one SEA tile.

    Deliberately no MOUNTAIN -- its Algorithm-X solve is slow and would
    make this integration test sluggish (see plan's "Risks" section)."""
    grid = {}
    for x in range(6):
        for y in range(6):
            grid[(x, y)] = Terrain.GRASS
    grid[(2, 2)] = Terrain.FOREST
    grid[(4, 4)] = Terrain.SEA
    return grid


def make_prefab(nid='test_board_integration_map', seed=5) -> MapPrefab:
    prefab = MapPrefab(nid)
    prefab.set_new_terrain_grid((6, 6), make_grid())
    prefab.seed = seed
    return prefab


class MapPrefabBoardIntegrationTests(unittest.TestCase):
    """Phase 7 verification: does app.engine.game_board.GameBoard (movement
    grids, opacity grid, fog of war grids) and app.engine.minimap.MiniMap
    build correctly off a MapPrefabTileMapObject, purely through the public
    TileMapObject contract (get_terrain), the same way they would off a
    normal TileMapObject?

    Drives a real game.start_level() (see test_map_prefab_level_wiring.py's
    StartLevelMapPrefabWiringTests) rather than hand-assembling GameBoard,
    since GameBoard/fog/minimap all reach through the module-level `game`
    singleton internally (not a locally-injected one), and start_level
    already exercises the exact wiring the engine uses in play.
    """

    LEVEL_NID = 'test_board_integration_level'
    MAP_PREFAB_NID = 'test_board_integration_map'

    FOREST_POS = (2, 2)
    SEA_POS = (4, 4)
    GRASS_POS = (0, 0)
    FOG_RADIUS = 2

    def setUp(self):
        DB.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        RESOURCES.load('testing_proj.ltproj', CURRENT_SERIALIZATION_VERSION)
        DB.map_terrain_associations = MapTerrainAssociations()

        # RESOURCES.load() resets app.sprites.SPRITES to fresh BasicSprite
        # entries with image=None; mirror driver.start()'s post-load step so
        # engine-bundled sprites (cursor/arrow/minimap tiles) aren't None.
        from app.engine import sprites as engine_sprites
        engine_sprites.load_images()

        self.map_prefab = make_prefab(nid=self.MAP_PREFAB_NID)
        RESOURCES.map_prefabs.append(self.map_prefab)

        self.level_prefab = LevelPrefab(self.LEVEL_NID, 'Test Board Integration Level')
        self.level_prefab.map_prefab = self.MAP_PREFAB_NID
        self.level_prefab.party = DB.parties[0].nid if len(DB.parties) else None
        DB.levels.append(self.level_prefab)

        from app.engine.game_state import game
        game.build_new()
        # Fog must be active for in_vision()/fog_of_war_grids checks below
        # to mean anything -- level_vars is reset by build_new() (via
        # sweep()) and NOT touched again by start_level(), so this must be
        # set in between. testing_proj also has fog_los=True (game_data/
        # constants.json), which additionally gates in_vision() on
        # get_fog_of_war_radius(team) -- i.e. _fog_of_war_radius, not
        # whatever radius a caller happens to pass to board.update_fow --
        # so set that too, matching action.UpdateFogOfWar's real usage.
        game.level_vars['_fog_of_war'] = True
        game.level_vars['_fog_of_war_radius'] = self.FOG_RADIUS
        game.start_level(self.LEVEL_NID)
        self.game = game

    def tearDown(self):
        RESOURCES.map_prefabs.delete(self.map_prefab)
        DB.levels.delete(self.level_prefab)

    def _plain_tilemap_equivalent_board(self) -> GameBoard:
        """A GameBoard built off a bare-bones stand-in tilemap whose
        get_terrain() returns the *same* nids the MapPrefabTileMapObject
        resolves via the association table, but without going through a
        MapPrefab/painters at all -- i.e. what a normal TileMapObject-backed
        level would hand GameBoard for this exact layout. GameBoard only
        ever calls tilemap.get_terrain()/.width/.height/.check_bounds, so if
        the two boards match, the subclass really is interchangeable from
        GameBoard's point of view."""
        prefab = self.game.level.tilemap.prefab
        nids = {pos: DB.map_terrain_associations.get(terrain)
                for pos, terrain in prefab.terrain_grid.items()}
        plain_tilemap = MagicMock()
        plain_tilemap.width = self.game.level.tilemap.width
        plain_tilemap.height = self.game.level.tilemap.height
        plain_tilemap.get_terrain = lambda pos: nids.get(pos, '0')
        return GameBoard(plain_tilemap)

    # --- 1. Board terrain/opacity grids from associated terrain ---

    def test_terrain_and_opacity_grids_match_association_table(self):
        tilemap = self.game.level.tilemap
        board = self.game.board

        forest_nid = DB.map_terrain_associations.get(Terrain.FOREST)
        self.assertEqual('2', forest_nid)
        self.assertEqual(forest_nid, tilemap.get_terrain(self.FOREST_POS))
        forest_terrain = DB.terrain.get(forest_nid)
        self.assertEqual(forest_terrain.opaque, board.get_opacity(self.FOREST_POS))

        grass_nid = DB.map_terrain_associations.get(Terrain.GRASS)
        self.assertEqual('1', grass_nid)
        self.assertEqual(grass_nid, tilemap.get_terrain(self.GRASS_POS))
        grass_terrain = DB.terrain.get(grass_nid)
        self.assertEqual(grass_terrain.opaque, board.get_opacity(self.GRASS_POS))

        sea_nid = DB.map_terrain_associations.get(Terrain.SEA)
        self.assertEqual('11', sea_nid)
        self.assertEqual(sea_nid, tilemap.get_terrain(self.SEA_POS))
        sea_terrain = DB.terrain.get(sea_nid)
        self.assertEqual(sea_terrain.opaque, board.get_opacity(self.SEA_POS))

    def test_opacity_and_movement_grids_match_plain_tilemap_equivalent(self):
        """The core Phase 7 claim: swapping in MapPrefabTileMapObject must be
        invisible to GameBoard. Build a second board off a stand-in tilemap
        exposing the same resolved nids directly (no MapPrefab/painters
        involved) and check every grid GameBoard derives from get_terrain
        agrees, tile for tile."""
        real_board = self.game.board
        plain_board = self._plain_tilemap_equivalent_board()

        width = self.game.level.tilemap.width
        height = self.game.level.tilemap.height
        for x in range(width):
            for y in range(height):
                pos = (x, y)
                self.assertEqual(
                    plain_board.get_opacity(pos), real_board.get_opacity(pos),
                    "opacity_grid mismatch at %s" % (pos,))
                for movement_group in DB.mcost.unit_types:
                    real_node = real_board.get_movement_grid(movement_group).get(pos)
                    plain_node = plain_board.get_movement_grid(movement_group).get(pos)
                    self.assertEqual(
                        plain_node.cost, real_node.cost,
                        "mcost mismatch at %s for %s" % (pos, movement_group))
                    self.assertEqual(
                        plain_node.reachable, real_node.reachable,
                        "reachable mismatch at %s for %s" % (pos, movement_group))

    # --- 2. Fog of war grid build + basic visibility ---

    def test_fog_of_war_grid_builds_and_reflects_radius(self):
        from app.engine import action

        board = self.game.board
        self.assertTrue(self.game.get_current_fog_info().is_active)
        self.assertTrue(board.fog_of_war_grids)

        unit = UnitObject('board_integ_fog_unit')
        unit.team = 'player'
        # testing_proj has fog_los=True (see testing_proj.ltproj/game_data/
        # constants.json), so in_vision's line-of-sight check
        # (line_of_sight.simple_check) walks game.units looking for this
        # unit by team -- it must actually be registered, not just passed
        # locally to update_fow.
        self.game.register_unit(unit)

        vantage = (0, 0)
        unit.position = vantage
        # Drive the real action (as combat/movement code does) rather than
        # calling board.update_fow directly with an arbitrary radius: the
        # fog_los in_vision() gate re-derives its own radius from
        # get_fog_of_war_radius()/_fog_of_war_radius, independent of
        # whatever radius a caller passes to update_fow, so the two must
        # agree the way UpdateFogOfWar computes them for this to mean
        # anything.
        action.UpdateFogOfWar(unit).do()

        # In-radius tile (Manhattan distance == FOG_RADIUS) is visible...
        near_pos = (self.FOG_RADIUS, 0)
        self.assertLessEqual(utils.calculate_distance(vantage, near_pos), self.FOG_RADIUS)
        self.assertTrue(board.in_vision(near_pos, 'player'))

        # ...a tile well outside the radius (includes the SEA tile) is not.
        far_pos = self.SEA_POS
        self.assertGreater(utils.calculate_distance(vantage, far_pos), self.FOG_RADIUS)
        self.assertFalse(board.in_vision(far_pos, 'player'))

        # The unit's own vantage point is always visible.
        self.assertTrue(board.in_vision(vantage, 'player'))

        # Moving away clears the old vision and reveals the new area.
        unit.position = (5, 5)
        action.UpdateFogOfWar(unit).do()
        self.assertFalse(board.in_vision(near_pos, 'player'))
        self.assertTrue(board.in_vision((5, 5), 'player'))

    # --- 3. Minimap builds from a prefab tilemap ---

    def test_minimap_builds_from_prefab_tilemap(self):
        from app.engine.minimap import MiniMap
        tilemap = self.game.level.tilemap
        minimap = MiniMap(tilemap, self.game.units)

        expected_size = (tilemap.width * MiniMap.scale_factor, tilemap.height * MiniMap.scale_factor)
        self.assertEqual(expected_size, minimap.surf.get_size())
        self.assertEqual(expected_size, minimap.pin_surf.get_size())

        # Resolved a real minimap key for the FOREST position via the
        # terrain association -> DB.terrain.minimap lookup (not the
        # fallback 'Grass' used when terrain lookup fails).
        forest_nid = DB.map_terrain_associations.get(Terrain.FOREST)
        expected_minimap_key = DB.terrain.get(forest_nid).minimap
        self.assertEqual(expected_minimap_key, minimap.get_minimap_key(self.FOREST_POS))

        sea_nid = DB.map_terrain_associations.get(Terrain.SEA)
        expected_sea_key = DB.terrain.get(sea_nid).minimap
        self.assertEqual(expected_sea_key, minimap.get_minimap_key(self.SEA_POS))

    # --- 4. Movement cost flows through ---

    def test_movement_grid_reflects_db_mcost_for_associated_terrain(self):
        board = self.game.board
        sea_nid = DB.map_terrain_associations.get(Terrain.SEA)
        sea_terrain = DB.terrain.get(sea_nid)

        for movement_group in DB.mcost.unit_types:
            expected_cost = DB.mcost.get_mcost(movement_group, sea_terrain.mtype)
            node = board.get_movement_grid(movement_group).get(self.SEA_POS)
            self.assertEqual(expected_cost, node.cost,
                              "mcost mismatch for %s at Sea tile" % movement_group)
            self.assertEqual(expected_cost < 99, node.reachable)

        # Contrast with a foot-traversable Plains tile so the test can't
        # pass merely because everything happens to be equally (un)reachable.
        grass_nid = DB.map_terrain_associations.get(Terrain.GRASS)
        grass_terrain = DB.terrain.get(grass_nid)
        foot_group = DB.mcost.unit_types[0]
        grass_cost = DB.mcost.get_mcost(foot_group, grass_terrain.mtype)
        grass_node = board.get_movement_grid(foot_group).get(self.GRASS_POS)
        self.assertEqual(grass_cost, grass_node.cost)


if __name__ == '__main__':
    unittest.main()
