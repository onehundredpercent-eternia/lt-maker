import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import unittest

import pygame

from app.constants import TILEWIDTH, TILEHEIGHT, AUTOTILE_FRAMES
from app.data.database.database import DB
from app.data.database.map_terrain_associations import MapTerrainAssociations
from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.engine.objects.prefab_tilemap import MapPrefabTileMapObject


def setUpModule():
    # engine.create_surface() calls Surface.convert()/.convert_alpha(),
    # which require an initialized display -- even the dummy SDL driver
    # needs a display mode set once.
    pygame.init()
    pygame.display.set_mode((1, 1))


def make_small_grid():
    """4x4 all GRASS, with a couple SEA tiles so autotile_set is non-empty."""
    grid = {}
    for x in range(4):
        for y in range(4):
            grid[(x, y)] = Terrain.GRASS
    grid[(1, 1)] = Terrain.SEA
    grid[(2, 1)] = Terrain.SEA
    return grid


def make_small_prefab(nid='test_map', seed=5) -> MapPrefab:
    prefab = MapPrefab(nid)
    prefab.set_new_terrain_grid((4, 4), make_small_grid())
    prefab.seed = seed
    return prefab


class PrefabTileMapObjectTests(unittest.TestCase):
    def setUp(self):
        # Global DB singleton -- reset so no other test's overrides leak in
        # (get_terrain reads DB.map_terrain_associations).
        DB.map_terrain_associations = MapTerrainAssociations()

    def test_build_from_prefab_basic_contract(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)

        self.assertEqual(4, tm.width)
        self.assertEqual(4, tm.height)

        layer = tm.layers.get('base')
        self.assertIsNotNone(layer)
        self.assertTrue(layer.visible)
        self.assertFalse(layer.foreground)
        self.assertEqual((4 * TILEWIDTH, 4 * TILEHEIGHT), layer.image.get_size())
        for autotile_image in layer.autotile_images:
            self.assertEqual((4 * TILEWIDTH, 4 * TILEHEIGHT), autotile_image.get_size())

        # check_bounds / on_border behave like a normal TileMapObject
        self.assertTrue(tm.check_bounds((0, 0)))
        self.assertTrue(tm.check_bounds((3, 3)))
        self.assertFalse(tm.check_bounds((4, 0)))
        self.assertFalse(tm.check_bounds((-1, 0)))
        self.assertTrue(tm.on_border((0, 1)))
        self.assertTrue(tm.on_border((3, 1)))
        self.assertFalse(tm.on_border((1, 1)))

        # get_terrain maps through DB.map_terrain_associations (phase 2 defaults)
        self.assertEqual('1', tm.get_terrain((0, 0)))    # GRASS -> Plains
        self.assertEqual('11', tm.get_terrain((1, 1)))   # SEA -> Sea
        self.assertEqual('0', tm.get_terrain((10, 10)))  # not in grid -> fallback

        # get_layer
        self.assertEqual('base', tm.get_layer((0, 0)))
        self.assertIsNone(tm.get_layer((10, 10)))

    def test_from_prefab_deep_copies_and_does_not_mutate_resource(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        tm.change_terrain((0, 0), Terrain.FOREST)
        # The original prefab (standing in for a RESOURCES-owned one) must
        # be untouched.
        self.assertEqual(Terrain.GRASS, prefab.terrain_grid[(0, 0)])
        self.assertEqual(Terrain.FOREST, tm.prefab.terrain_grid[(0, 0)])
        self.assertIsNot(prefab, tm.prefab)

    def test_autotile_bake_present_when_autotile_positions_exist(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        layer = tm.layers.get('base')
        self.assertEqual(AUTOTILE_FRAMES, len(layer.autotile_images))

    def test_autotile_bake_empty_when_no_autotile_positions(self):
        prefab = MapPrefab('no_autotiles')
        grid = {(x, y): Terrain.GRASS for x in range(3) for y in range(3)}
        prefab.set_new_terrain_grid((3, 3), grid)
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        layer = tm.layers.get('base')
        self.assertEqual([], layer.autotile_images)

    def test_incremental_change_matches_from_scratch_render(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        tm.change_terrain((3, 3), Terrain.FOREST)

        grid2 = make_small_grid()
        grid2[(3, 3)] = Terrain.FOREST
        prefab2 = MapPrefab('test_map')
        prefab2.set_new_terrain_grid((4, 4), grid2)
        prefab2.seed = 5
        tm2 = MapPrefabTileMapObject.from_prefab(prefab2)

        full_rect = (0, 0, tm.width * TILEWIDTH, tm.height * TILEHEIGHT)

        base1 = pygame.image.tobytes(tm.get_full_image(full_rect), 'RGBA')
        base2 = pygame.image.tobytes(tm2.get_full_image(full_rect), 'RGBA')
        self.assertEqual(base2, base1, "Patched base image differs from a from-scratch render")

        # Force every autotile frame index and compare those too
        layer1 = tm.layers.get('base')
        layer2 = tm2.layers.get('base')
        for frame in range(AUTOTILE_FRAMES):
            layer1.autotile_frame = frame
            layer2.autotile_frame = frame
            img1 = pygame.image.tobytes(tm.get_full_image(full_rect), 'RGBA')
            img2 = pygame.image.tobytes(tm2.get_full_image(full_rect), 'RGBA')
            self.assertEqual(img2, img1, "Autotile frame %d differs from a from-scratch render" % frame)

    def test_incremental_flood_fill_change_matches_from_scratch_render(self):
        # SEA is a flood-fill terrain: changing one tile of a blob must
        # re-render the surviving blob correctly, not just the changed tile.
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        tm.change_terrain((2, 1), Terrain.GRASS)

        grid2 = make_small_grid()
        grid2[(2, 1)] = Terrain.GRASS
        prefab2 = MapPrefab('test_map')
        prefab2.set_new_terrain_grid((4, 4), grid2)
        prefab2.seed = 5
        tm2 = MapPrefabTileMapObject.from_prefab(prefab2)

        full_rect = (0, 0, tm.width * TILEWIDTH, tm.height * TILEHEIGHT)
        layer1 = tm.layers.get('base')
        layer2 = tm2.layers.get('base')
        for frame in range(AUTOTILE_FRAMES):
            layer1.autotile_frame = frame
            layer2.autotile_frame = frame
            img1 = pygame.image.tobytes(tm.get_full_image(full_rect), 'RGBA')
            img2 = pygame.image.tobytes(tm2.get_full_image(full_rect), 'RGBA')
            self.assertEqual(img2, img1, "Autotile frame %d differs from a from-scratch render" % frame)

    def test_autotile_images_dropped_when_last_autotile_removed(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        layer = tm.layers.get('base')
        self.assertEqual(AUTOTILE_FRAMES, len(layer.autotile_images))

        tm.change_terrain((1, 1), Terrain.GRASS)
        tm.change_terrain((2, 1), Terrain.GRASS)
        self.assertEqual(set(), tm.prefab.autotile_set)
        self.assertEqual([], layer.autotile_images)

        # And they come back if an autotile terrain is painted again
        tm.change_terrain((1, 1), Terrain.SEA)
        self.assertEqual(AUTOTILE_FRAMES, len(layer.autotile_images))

    def test_change_terrain_updates_autotile_set_membership(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        self.assertIn((1, 1), tm.prefab.autotile_set)

        # SEA -> GRASS: position must leave autotile_set and its old (sea)
        # pixels must be gone from every autotile frame.
        tm.change_terrain((1, 1), Terrain.GRASS)
        self.assertNotIn((1, 1), tm.prefab.autotile_set)
        self.assertEqual('1', tm.get_terrain((1, 1)))

        layer = tm.layers.get('base')
        rect = (1 * TILEWIDTH, 1 * TILEHEIGHT, TILEWIDTH, TILEHEIGHT)
        for autotile_image in layer.autotile_images:
            patch = autotile_image.subsurface(rect)
            self.assertTrue(_is_fully_transparent(patch), "Old autotile pixels were not cleared")

    def test_change_terrain_to_none_erases_and_clears_pixels(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)

        tm.change_terrain((0, 0), None)
        self.assertNotIn((0, 0), tm.prefab.terrain_grid)
        self.assertEqual('0', tm.get_terrain((0, 0)))
        self.assertIsNone(tm.get_layer((0, 0)))

        layer = tm.layers.get('base')
        rect = (0, 0, TILEWIDTH, TILEHEIGHT)
        patch = layer.image.subsurface(rect)
        self.assertTrue(_is_fully_transparent(patch), "Erased tile's base-image pixels were not cleared")

    def test_save_restore_round_trip_with_modified_grid(self):
        prefab = make_small_prefab()
        tm = MapPrefabTileMapObject.from_prefab(prefab)
        tm.change_terrain((3, 3), Terrain.FOREST)
        tm.change_terrain((0, 0), None)

        saved = tm.save()
        restored = MapPrefabTileMapObject.restore(saved)

        self.assertEqual(tm.prefab.terrain_grid, restored.prefab.terrain_grid)
        self.assertEqual(tm.prefab.autotile_set, restored.prefab.autotile_set)

        full_rect = (0, 0, tm.width * TILEWIDTH, tm.height * TILEHEIGHT)
        before = pygame.image.tobytes(tm.get_full_image(full_rect), 'RGBA')
        after = pygame.image.tobytes(restored.get_full_image(full_rect), 'RGBA')
        self.assertEqual(before, after)


def _is_fully_transparent(surf: pygame.Surface) -> bool:
    w, h = surf.get_size()
    for x in range(w):
        for y in range(h):
            if surf.get_at((x, y))[3] != 0:
                return False
    return True


if __name__ == '__main__':
    unittest.main()
