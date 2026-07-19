"""Renders an app.map_maker.map_prefab.MapPrefab (a RESOURCES.map_prefabs
entry) to a QPixmap for editor-side display -- the level editor's main map
view, unit placement, event preview, and the level list, wherever a level's
LevelPrefab.map_prefab is set instead of a tilemap nid.

Deliberately does NOT use the module-level RENDERERS/PAINTERS singletons in
app.map_maker.qt_renderers / app.map_maker.painter_database -- those are
reserved for the map_maker editor itself (see the long comment at the top of
app/map_maker/pygame_renderers/renderer_database.py for why sharing painter
state across frontends is a hazard). Renderers here are built per-prefab via
create_renderers() with a fresh, dedicated painter set.
"""
from typing import Dict, Optional, Tuple

from PyQt5.QtGui import QPixmap

from app.utilities.typing import NID, Pos

from app.data.database.database import DB

from app.map_maker.map_prefab import MapPrefab
from app.map_maker.terrain import Terrain
from app.map_maker.palette_collection import PALETTES, PaletteCollection
from app.map_maker.qt_renderers import SimpleRenderer
from app.map_maker.qt_renderers.renderer_database import create_renderers
from app.map_maker.editor.draw_tilemap import draw_tilemap_with_renderers

# prefab nid -> (outdoor_palette nid used to build renderers, indoor_palette
# nid used to build renderers, the renderers dict itself). Rebuilt whenever
# the prefab's current palette selection no longer matches what's cached.
_renderer_cache: Dict[NID, Tuple[Optional[NID], Optional[NID], Dict[Terrain, SimpleRenderer]]] = {}


def _resolve_palette(collection, nid: Optional[NID]) -> PaletteCollection:
    """project override -> the requested nid if it still exists -> index 0.

    Mirrors app.engine.objects.prefab_tilemap._resolve_palette."""
    if nid:
        found = collection.get(nid)
        if found is not None:
            return found
    return collection[0]


def get_map_prefab_pixmap(prefab: MapPrefab) -> QPixmap:
    """Static render (autotile frame 0) of `prefab`, honoring its saved
    palettes. Renderers are cached per prefab nid and rebuilt only when the
    prefab's palette selection changes."""
    cached = _renderer_cache.get(prefab.nid)
    if cached is None or cached[0] != prefab.current_outdoor_palette or cached[1] != prefab.current_indoor_palette:
        outdoor_palette = _resolve_palette(PALETTES.outdoor_palettes(), prefab.current_outdoor_palette)
        indoor_palette = _resolve_palette(PALETTES.indoor_palettes(), prefab.current_indoor_palette)
        renderers = create_renderers(outdoor_palette, indoor_palette)
        # Qt MountainRenderer.__init__ flips its painter to background
        # QThread solving (gui_processing=True) for the live map_maker
        # editor. This is a one-shot static render with no repaint hook when
        # a thread finishes, so mountains must solve synchronously inside
        # single_process instead -- same as the engine's pygame
        # MountainRenderer. Safe: these painters are this module's own
        # dedicated set, not the shared PAINTERS singleton.
        renderers[Terrain.MOUNTAIN].painter.gui_processing = False
        _renderer_cache[prefab.nid] = (prefab.current_outdoor_palette, prefab.current_indoor_palette, renderers)
        # The prefab's tile_grid sprites (if any) were rendered by different
        # renderers/palettes, or -- for a freshly loaded prefab -- never at
        # all: MapPrefab.restore leaves terrain_grid_to_update empty, so
        # without this the render below would draw blank.
        prefab.reset_all()
    else:
        renderers = cached[2]
        if not prefab.tile_grid and prefab.terrain_grid:
            # Same nid, different object: a project reload rebuilds
            # RESOURCES.map_prefabs with fresh MapPrefab instances (empty
            # tile_grid, empty terrain_grid_to_update), but the cache still
            # hits on the nid -- without this the render below draws blank.
            prefab.reset_all()

    return QPixmap.fromImage(draw_tilemap_with_renderers(prefab, renderers, autotile_num=0))


def get_map_prefab_terrain_nid(prefab: MapPrefab, pos: Pos) -> Optional[NID]:
    """DB terrain nid at `pos`, via the project's Terrain -> DB terrain
    association table. None if `pos` has no terrain."""
    terrain = prefab.get_terrain(pos)
    if terrain is None:
        return None
    return DB.map_terrain_associations.get(terrain)
