# pygame mirror of app/map_maker/qt_renderers/renderer_database.py
#
# IMPORTANT: unlike the qt mirror, this module's own module-level RENDERERS
# (below) is built against its OWN dedicated painters, NOT the process-wide
# PAINTERS singleton in painter_database.py. That singleton is shared with
# app.map_maker.qt_renderers.renderer_database (the Qt editor), which wires
# painter-specific state onto it at import time -- e.g.
# MountainPainter.gui_processing (qt_renderers/mountain_renderer.py sets it
# True for background-QThread solving; this module's own MountainRenderer
# sets it False for synchronous solving). If this module's RENDERERS reused
# that same shared PAINTERS dict, merely importing this module in the same
# process as the Qt editor (e.g. via app.engine.objects.prefab_tilemap, which
# game_state.py -- always imported by the main editor for Test Chapter --
# will pull in) would silently flip the Qt editor's mountain solving from
# threaded to synchronous, or vice versa, purely based on import order.
# Confirmed empirically: importing this module previously flipped
# PAINTERS[Terrain.MOUNTAIN].gui_processing from True to False as a pure
# import side effect. Building dedicated painters here removes that hazard
# entirely: this module (and anyone downstream of it, including the engine)
# never touches painter_database.PAINTERS.
#
# create_renderers() itself still accepts an explicit `painters` dict (e.g.
# painter_database.PAINTERS itself, or another fresh app.engine
# per-MapPrefabTileMapObject set from create_painters()) for callers that
# want it -- only the module-level singleton below opts out of the shared
# one.
from typing import Dict, Optional

from app.map_maker.terrain import Terrain
from app.map_maker.painter_utils import Painter
from app.map_maker.pygame_renderers import (
    SimpleRenderer,
    SimpleRenderer8,
    SeaRenderer,
    DisplayRenderer8,
    LimitRenderer8,
    LimitRenderer16,
    CliffRenderer,
    MountainRenderer,
    SimpleShadingRenderer,
    PoolShadingRenderer,
    FloorShadingRenderer,
)
from app.map_maker.palette_collection import PALETTES, PaletteCollection
from app.map_maker.painter_database import create_painters


def create_renderers(outdoor_palette: PaletteCollection, indoor_palette: PaletteCollection,
                      painters: Optional[Dict[Terrain, Painter]] = None) -> Dict[Terrain, SimpleRenderer]:
    """Builds a Terrain -> renderer dict for the given palettes.

    `painters` defaults to a fresh, dedicated set from create_painters() --
    NOT the process-wide PAINTERS singleton in painter_database.py, which is
    shared with (and mutated by) the Qt editor's qt_renderers. Pass
    painter_database.PAINTERS explicitly if you specifically want that
    shared singleton."""
    if painters is None:
        painters = create_painters()

    renderers: Dict[Terrain, SimpleRenderer] = {}

    # Outdoor
    renderers[Terrain.GRASS] = \
        SimpleRenderer8(painters[Terrain.GRASS],
                        outdoor_palette.get(Terrain.GRASS))
    renderers[Terrain.LIGHT_GRASS] = \
        LimitRenderer8(painters[Terrain.LIGHT_GRASS],
                       outdoor_palette.get(Terrain.LIGHT_GRASS))
    renderers[Terrain.NOISY_GRASS] = \
        LimitRenderer8(painters[Terrain.NOISY_GRASS],
                       outdoor_palette.get(Terrain.NOISY_GRASS))
    renderers[Terrain.SAND] = \
        LimitRenderer8(painters[Terrain.SAND],
                       outdoor_palette.get(Terrain.SAND))
    renderers[Terrain.ROAD] = \
        LimitRenderer8(painters[Terrain.ROAD],
                       outdoor_palette.get(Terrain.ROAD))
    renderers[Terrain.RIVER] = \
        LimitRenderer8(painters[Terrain.RIVER],
                       outdoor_palette.get(Terrain.RIVER))
    renderers[Terrain.SEA] = \
        SeaRenderer(painters[Terrain.SEA],
                    outdoor_palette.get(Terrain.SEA))
    renderers[Terrain.SPARSE_FOREST] = \
        SimpleRenderer(painters[Terrain.SPARSE_FOREST],
                       outdoor_palette.get(Terrain.SPARSE_FOREST))
    renderers[Terrain.FOREST] = \
        DisplayRenderer8(painters[Terrain.FOREST],
                         outdoor_palette.get(Terrain.FOREST))
    renderers[Terrain.THICKET] = \
        DisplayRenderer8(painters[Terrain.THICKET],
                         outdoor_palette.get(Terrain.THICKET))
    renderers[Terrain.HILL] = \
        SimpleRenderer(painters[Terrain.HILL],
                       outdoor_palette.get(Terrain.HILL))
    renderers[Terrain.MOUNTAIN] = \
        MountainRenderer(painters[Terrain.MOUNTAIN],
                         outdoor_palette.get(Terrain.MOUNTAIN))
    renderers[Terrain.CLIFF] = \
        CliffRenderer(painters[Terrain.CLIFF],
                      outdoor_palette.get(Terrain.CLIFF))
    renderers[Terrain.DESERT] = \
        LimitRenderer16(painters[Terrain.DESERT],
                        outdoor_palette.get(Terrain.DESERT))
    renderers[Terrain.DESERT_CLIFF] = \
        CliffRenderer(painters[Terrain.DESERT_CLIFF],
                      outdoor_palette.get(Terrain.DESERT_CLIFF))
    renderers[Terrain.DESERT_ROCK] = \
        SimpleRenderer(painters[Terrain.DESERT_ROCK],
                       outdoor_palette.get(Terrain.DESERT_ROCK))
    renderers[Terrain.BRIDGEH] = \
        LimitRenderer16(painters[Terrain.BRIDGEH],
                        outdoor_palette.get(Terrain.BRIDGEH))
    renderers[Terrain.BRIDGEV] = \
        LimitRenderer16(painters[Terrain.BRIDGEV],
                        outdoor_palette.get(Terrain.BRIDGEV))
    renderers[Terrain.CASTLE] = \
        SimpleRenderer(painters[Terrain.CASTLE],
                       outdoor_palette.get(Terrain.CASTLE))
    renderers[Terrain.RUINS] = \
        SimpleRenderer(painters[Terrain.RUINS],
                       outdoor_palette.get(Terrain.RUINS))
    renderers[Terrain.HOUSE] = \
        SimpleRenderer(painters[Terrain.HOUSE],
                       outdoor_palette.get(Terrain.HOUSE))

    # Indoors
    renderers[Terrain.VOID] = \
        SimpleRenderer(painters[Terrain.VOID],
                       indoor_palette.get(Terrain.VOID))
    renderers[Terrain.FLOOR_1] = \
        FloorShadingRenderer('floor1',
                             indoor_palette.get(Terrain.FLOOR_1))
    renderers[Terrain.FLOOR_2] = \
        FloorShadingRenderer('floor2',
                             indoor_palette.get(Terrain.FLOOR_2))
    renderers[Terrain.FLOOR_3] = \
        FloorShadingRenderer('floor3',
                             indoor_palette.get(Terrain.FLOOR_3))
    renderers[Terrain.WALL_TOP] = \
        LimitRenderer16(painters[Terrain.WALL_TOP],
                        indoor_palette.get(Terrain.WALL_TOP))
    renderers[Terrain.WALL_BOTTOM] = \
        SimpleRenderer(painters[Terrain.WALL_BOTTOM],
                       indoor_palette.get(Terrain.WALL_BOTTOM))
    renderers[Terrain.COLUMN] = \
        SimpleRenderer(painters[Terrain.COLUMN],
                       indoor_palette.get(Terrain.COLUMN))
    renderers[Terrain.STAIRS_UPDOWN] = \
        SimpleRenderer(painters[Terrain.STAIRS_UPDOWN],
                       indoor_palette.get(Terrain.STAIRS_UPDOWN))
    renderers[Terrain.STAIRS_LEFT] = \
        SimpleRenderer(painters[Terrain.STAIRS_LEFT],
                       indoor_palette.get(Terrain.STAIRS_LEFT))
    renderers[Terrain.STAIRS_RIGHT] = \
        SimpleRenderer(painters[Terrain.STAIRS_RIGHT],
                       indoor_palette.get(Terrain.STAIRS_RIGHT))
    renderers[Terrain.STAIRS_CENTER] = \
        SimpleRenderer(painters[Terrain.STAIRS_CENTER],
                       indoor_palette.get(Terrain.STAIRS_CENTER))
    renderers[Terrain.PILLAR] = \
        SimpleRenderer(painters[Terrain.PILLAR],
                       indoor_palette.get(Terrain.PILLAR))
    renderers[Terrain.POOL] = \
        PoolShadingRenderer(painters[Terrain.POOL],
                            indoor_palette.get(Terrain.POOL))
    renderers[Terrain.POOL_BRIDGE] = \
        SimpleShadingRenderer(painters[Terrain.POOL_BRIDGE],
                              indoor_palette.get(Terrain.POOL_BRIDGE))
    renderers[Terrain.TREASURE] = \
        SimpleRenderer(painters[Terrain.TREASURE],
                       indoor_palette.get(Terrain.TREASURE))

    return renderers


RENDERERS = create_renderers(PALETTES.outdoor_palettes()[0], PALETTES.indoor_palettes()[0])
