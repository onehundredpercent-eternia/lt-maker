# Phase 7 tests for the Phase 6 editor-side MapPrefab display pipeline:
# app/map_maker/qt_renderers/renderer_database.py (create_renderers()
# factory + module-level RENDERERS), app/map_maker/editor/draw_tilemap.py
# (draw_tilemap_with_renderers), app/editor/map_prefab_display.py, and
# app/editor/map_view.py's resolve_level_map()/get_map_pixmap() helpers.
#
# These are Qt (PyQt5) tests, unlike the rest of app/tests -- QT_QPA_PLATFORM
# must be set to 'offscreen' before PyQt5 initializes a platform plugin, so
# that happens in setUpModule() before any PyQt5 or app.editor import runs.
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

import unittest


def setUpModule():
    # engine.create_surface() (pulled in transitively) calls
    # Surface.convert()/.convert_alpha(), which require an initialized
    # display -- even the dummy SDL driver needs a display mode set once.
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))

    # QT_QPA_PLATFORM must be set before PyQt5 initializes a platform
    # plugin -- do this before importing PyQt5/app.editor, then build (or
    # reuse) the one process-wide QApplication instance for the module.
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

    global QApplication, QImage
    global TILEWIDTH, TILEHEIGHT
    global DB, RESOURCES, LevelPrefab, MapTerrainAssociations
    global Terrain, MapPrefab, PALETTES, PAINTERS
    global create_renderers, RENDERERS, draw_tilemap_with_renderers
    global map_prefab_display, map_view
    global _qapp

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QImage

    # Must exist before anything constructs a QPixmap/QImage -- and
    # renderer_database.py builds real QPixmaps for its module-level
    # RENDERERS as an import-time side effect, so the QApplication has to
    # come before that import (and before map_prefab_display/map_view,
    # which import renderer_database transitively). Constructing pixmaps
    # with no QApplication yet alive crashes the interpreter outright
    # (no Python exception -- the process just dies).
    _qapp = QApplication.instance() or QApplication([])

    from app.constants import TILEWIDTH, TILEHEIGHT

    from app.data.database.database import DB
    from app.data.database.levels import LevelPrefab
    from app.data.database.map_terrain_associations import MapTerrainAssociations
    from app.data.resources.resources import RESOURCES

    from app.map_maker.terrain import Terrain
    from app.map_maker.map_prefab import MapPrefab
    from app.map_maker.palette_collection import PALETTES
    from app.map_maker.painter_database import PAINTERS
    from app.map_maker.qt_renderers.renderer_database import create_renderers, RENDERERS
    from app.map_maker.editor.draw_tilemap import draw_tilemap_with_renderers

    import app.editor.map_prefab_display as map_prefab_display
    import app.editor.map_view as map_view


def make_small_grid():
    """4x4 all GRASS, with a couple SEA tiles so autotile_set is non-empty."""
    grid = {}
    for x in range(4):
        for y in range(4):
            grid[(x, y)] = Terrain.GRASS
    grid[(1, 1)] = Terrain.SEA
    grid[(2, 1)] = Terrain.SEA
    return grid


def make_small_prefab(nid='test_map', seed=5):
    prefab = MapPrefab(nid)
    prefab.set_new_terrain_grid((4, 4), make_small_grid())
    prefab.seed = seed
    return prefab


def _image_has_nonzero_alpha(image) -> bool:
    for x in range(image.width()):
        for y in range(image.height()):
            if image.pixelColor(x, y).alpha() != 0:
                return True
    return False


class RendererFactoryTests(unittest.TestCase):
    """create_renderers() regression tests for the Phase 6 __init__ palette
    fixes (SimpleRenderer8, FloorShadingRenderer)."""

    def test_create_renderers_covers_every_terrain(self):
        outdoor = PALETTES.outdoor_palettes()[0]
        indoor = PALETTES.indoor_palettes()[0]
        renderers = create_renderers(outdoor, indoor)
        self.assertEqual(set(Terrain), set(renderers.keys()))

    def test_every_renderer_has_a_palette_attribute(self):
        # Regression: SimpleRenderer8.__init__ used to only set self.painter
        # and skip set_palette(), and FloorShadingRenderer.__init__ never
        # called set_palette() at all -- both left self.palette unset until
        # the Qt map_maker editor's startup *_palette_changed(0) call
        # papered over it. A renderer built via create_renderers() outside
        # that editor (e.g. this module's own callers) would crash with
        # AttributeError on first render. Both are fixed now (see
        # simple_renderer.py / shading_renderer.py comments); this guards
        # the regression.
        outdoor = PALETTES.outdoor_palettes()[0]
        indoor = PALETTES.indoor_palettes()[0]
        renderers = create_renderers(outdoor, indoor)
        for terrain, renderer in renderers.items():
            self.assertTrue(hasattr(renderer, 'palette'), "%s renderer missing .palette" % (terrain,))
            self.assertIsNotNone(renderer.palette, "%s renderer .palette is None" % (terrain,))

    def test_default_painters_are_not_the_shared_singleton(self):
        outdoor = PALETTES.outdoor_palettes()[0]
        indoor = PALETTES.indoor_palettes()[0]
        renderers = create_renderers(outdoor, indoor)
        self.assertIsNot(renderers[Terrain.GRASS].painter, PAINTERS[Terrain.GRASS])

    def test_module_level_renderers_share_the_singleton_painters(self):
        # Unlike the default painters=None case above, the module-level
        # RENDERERS deliberately shares PAINTERS with the Qt map_maker
        # editor (see the long comment at the top of renderer_database.py).
        self.assertIs(RENDERERS[Terrain.GRASS].painter, PAINTERS[Terrain.GRASS])


class DrawTilemapWithRenderersTests(unittest.TestCase):
    def test_render_produces_full_image_and_updates_tile_grid(self):
        prefab = make_small_prefab(nid='draw_test_map')
        outdoor = PALETTES.outdoor_palettes()[0]
        indoor = PALETTES.indoor_palettes()[0]
        renderers = create_renderers(outdoor, indoor)

        prefab.reset_all()
        image = draw_tilemap_with_renderers(prefab, renderers, autotile_num=0)

        self.assertEqual(prefab.width * TILEWIDTH, image.width())
        self.assertEqual(prefab.height * TILEHEIGHT, image.height())

        for pos in prefab.terrain_grid:
            self.assertIn(pos, prefab.tile_grid)

        self.assertEqual(set(), prefab.terrain_grid_to_update)
        self.assertTrue(_image_has_nonzero_alpha(image))


class MapPrefabDisplayTests(unittest.TestCase):
    def setUp(self):
        DB.map_terrain_associations = MapTerrainAssociations()
        map_prefab_display._renderer_cache.clear()

    def tearDown(self):
        map_prefab_display._renderer_cache.clear()

    def test_get_map_prefab_pixmap_size_and_cache_stability(self):
        prefab = make_small_prefab(nid='display_test_1')
        pixmap1 = map_prefab_display.get_map_prefab_pixmap(prefab)

        self.assertEqual(prefab.width * TILEWIDTH, pixmap1.width())
        self.assertEqual(prefab.height * TILEHEIGHT, pixmap1.height())

        cached_renderers = map_prefab_display._renderer_cache[prefab.nid][2]
        pixmap2 = map_prefab_display.get_map_prefab_pixmap(prefab)

        self.assertEqual(pixmap1.toImage(), pixmap2.toImage())
        self.assertIs(cached_renderers, map_prefab_display._renderer_cache[prefab.nid][2])

    def test_reload_guard_fresh_object_same_nid_still_renders(self):
        # A project reload rebuilds RESOURCES.map_prefabs with fresh
        # MapPrefab instances -- same nid, empty tile_grid, AND (unlike
        # set_new_terrain_grid, which calls reset_all()) empty
        # terrain_grid_to_update, since MapPrefab.restore() never calls
        # reset_all(). The cache still hits on the nid; without the
        # `if not prefab.tile_grid and prefab.terrain_grid: reset_all()`
        # guard in get_map_prefab_pixmap the second render would be blank.
        prefab = make_small_prefab(nid='display_test_2')
        image1 = map_prefab_display.get_map_prefab_pixmap(prefab).toImage()
        self.assertTrue(_image_has_nonzero_alpha(image1))

        prefab2 = make_small_prefab(nid='display_test_2')
        prefab2.terrain_grid_to_update.clear()
        self.assertEqual({}, prefab2.tile_grid)

        image2 = map_prefab_display.get_map_prefab_pixmap(prefab2).toImage()
        self.assertEqual(image1, image2)

    def test_palette_change_rebuilds_renderers(self):
        outdoor_palettes = PALETTES.outdoor_palettes()
        if len(outdoor_palettes) < 2:
            self.skipTest("Need at least 2 outdoor palettes to test a palette change")

        prefab = make_small_prefab(nid='display_test_3')
        map_prefab_display.get_map_prefab_pixmap(prefab)
        old_renderers = map_prefab_display._renderer_cache[prefab.nid][2]

        prefab.current_outdoor_palette = outdoor_palettes[1].nid
        map_prefab_display.get_map_prefab_pixmap(prefab)
        new_entry = map_prefab_display._renderer_cache[prefab.nid]

        self.assertIsNot(old_renderers, new_entry[2])
        self.assertEqual(outdoor_palettes[1].nid, new_entry[0])

    def test_mountain_render_isolated_from_shared_painter_and_solves_synchronously(self):
        grid = {(x, y): Terrain.GRASS for x in range(4) for y in range(4)}
        grid[(1, 1)] = Terrain.MOUNTAIN
        grid[(2, 1)] = Terrain.MOUNTAIN
        grid[(1, 2)] = Terrain.MOUNTAIN
        grid[(2, 2)] = Terrain.MOUNTAIN
        prefab = MapPrefab('display_test_mountain')
        prefab.set_new_terrain_grid((4, 4), grid)
        prefab.seed = 5

        shared_gui_processing_before = PAINTERS[Terrain.MOUNTAIN].gui_processing

        map_prefab_display.get_map_prefab_pixmap(prefab)

        cached_renderers = map_prefab_display._renderer_cache[prefab.nid][2]
        # Qt MountainRenderer.__init__ flips its own painter to background
        # QThread solving (gui_processing=True); a one-shot static render
        # must flip that back or mountains bake unsolved.
        self.assertFalse(cached_renderers[Terrain.MOUNTAIN].painter.gui_processing)
        # And it must be flipped back on this render's own dedicated
        # painter, never on the process-wide PAINTERS singleton the Qt
        # map_maker editor depends on.
        self.assertEqual(shared_gui_processing_before, PAINTERS[Terrain.MOUNTAIN].gui_processing)

        for pos in ((1, 1), (2, 1), (1, 2), (2, 2)):
            self.assertIn(pos, prefab.tile_grid)

    def test_get_map_prefab_terrain_nid_populated_position(self):
        prefab = make_small_prefab(nid='display_test_4')
        self.assertEqual('1', map_prefab_display.get_map_prefab_terrain_nid(prefab, (0, 0)))   # GRASS -> Plains
        self.assertEqual('11', map_prefab_display.get_map_prefab_terrain_nid(prefab, (1, 1)))  # SEA -> Sea

    def test_get_map_prefab_terrain_nid_empty_or_out_of_grid_position(self):
        prefab = make_small_prefab(nid='display_test_5')
        self.assertIsNone(map_prefab_display.get_map_prefab_terrain_nid(prefab, (10, 10)))


class MapViewHelperTests(unittest.TestCase):
    def setUp(self):
        DB.map_terrain_associations = MapTerrainAssociations()
        map_prefab_display._renderer_cache.clear()
        self._added_prefabs = []

    def tearDown(self):
        for prefab in self._added_prefabs:
            RESOURCES.map_prefabs.delete(prefab)
        map_prefab_display._renderer_cache.clear()

    def _register_prefab(self, prefab):
        RESOURCES.map_prefabs.append(prefab)
        self._added_prefabs.append(prefab)

    def test_resolve_level_map_prefers_registered_map_prefab(self):
        prefab = make_small_prefab(nid='mapview_test_prefab')
        self._register_prefab(prefab)
        level = LevelPrefab('mapview_lvl1', 'Test Level')
        level.map_prefab = 'mapview_test_prefab'

        result = map_view.resolve_level_map(level)
        self.assertIs(prefab, result)

    def test_resolve_level_map_falls_back_to_tilemap_for_nonexistent_prefab_nid(self):
        level = LevelPrefab('mapview_lvl2', 'Test Level')
        level.map_prefab = 'does_not_exist_prefab_nid'

        result = map_view.resolve_level_map(level)
        self.assertEqual(RESOURCES.tilemaps.get(level.tilemap), result)

    def test_resolve_level_map_uses_tilemap_when_map_prefab_is_none(self):
        level = LevelPrefab('mapview_lvl3', 'Test Level')
        self.assertIsNone(level.map_prefab)

        result = map_view.resolve_level_map(level)
        self.assertEqual(RESOURCES.tilemaps.get(level.tilemap), result)

    def test_get_map_pixmap_routes_map_prefab_to_prefab_renderer(self):
        prefab = make_small_prefab(nid='mapview_test_pixmap')
        self._register_prefab(prefab)

        pixmap = map_view.get_map_pixmap(prefab)

        self.assertEqual(prefab.width * TILEWIDTH, pixmap.width())
        self.assertEqual(prefab.height * TILEHEIGHT, pixmap.height())
        self.assertTrue(_image_has_nonzero_alpha(pixmap.toImage()))


if __name__ == '__main__':
    unittest.main()
