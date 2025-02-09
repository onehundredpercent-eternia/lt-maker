from app.map_maker.terrain import Terrain
from app.map_maker.qt_renderers import (
    SimpleRenderer,
    SimpleRenderer8,
    SeaRenderer,
    DisplayRenderer8,
    LimitRenderer8,
    LimitRenderer16,
    CliffRenderer,
)
from app.map_maker.palette_collection import \
    get_current_palette_collection
from app.map_maker.painter_database import PAINTERS

pc = get_current_palette_collection

RENDERERS = {}

RENDERERS[Terrain.GRASS] = \
    SimpleRenderer8(PAINTERS[Terrain.GRASS], 
                    pc().get(Terrain.GRASS))
RENDERERS[Terrain.LIGHT_GRASS] = \
    LimitRenderer8(PAINTERS[Terrain.LIGHT_GRASS], 
                   pc().get(Terrain.LIGHT_GRASS))
RENDERERS[Terrain.NOISY_GRASS] = \
    LimitRenderer8(PAINTERS[Terrain.NOISY_GRASS], 
                   pc().get(Terrain.NOISY_GRASS))
RENDERERS[Terrain.SAND] = \
    LimitRenderer8(PAINTERS[Terrain.SAND],
                   pc().get(Terrain.SAND))
RENDERERS[Terrain.ROAD] = \
    LimitRenderer8(PAINTERS[Terrain.ROAD],
                   pc().get(Terrain.ROAD))
RENDERERS[Terrain.RIVER] = \
    LimitRenderer8(PAINTERS[Terrain.RIVER],
                   pc().get(Terrain.RIVER))
RENDERERS[Terrain.SEA] = \
    SeaRenderer(PAINTERS[Terrain.SEA],
                pc().get(Terrain.SEA))
RENDERERS[Terrain.FOREST] = \
    DisplayRenderer8(PAINTERS[Terrain.FOREST],
                     pc().get(Terrain.FOREST))
RENDERERS[Terrain.THICKET] = \
    DisplayRenderer8(PAINTERS[Terrain.THICKET],
                     pc().get(Terrain.THICKET))
RENDERERS[Terrain.HILL] = \
    SimpleRenderer(PAINTERS[Terrain.HILL],
                   pc().get(Terrain.HILL))
RENDERERS[Terrain.MOUNTAIN] = \
    SimpleRenderer(PAINTERS[Terrain.MOUNTAIN],
                   pc().get(Terrain.MOUNTAIN))
RENDERERS[Terrain.CLIFF] = \
    CliffRenderer(PAINTERS[Terrain.CLIFF],
                  pc().get(Terrain.CLIFF))
RENDERERS[Terrain.BRIDGEH] = \
    LimitRenderer16(PAINTERS[Terrain.BRIDGEH],
                    pc().get(Terrain.BRIDGEH))
RENDERERS[Terrain.BRIDGEV] = \
    LimitRenderer16(PAINTERS[Terrain.BRIDGEV],
                    pc().get(Terrain.BRIDGEV))
RENDERERS[Terrain.CASTLE] = \
    SimpleRenderer(PAINTERS[Terrain.CASTLE],
                   pc().get(Terrain.CASTLE))
RENDERERS[Terrain.RUINS] = \
    SimpleRenderer(PAINTERS[Terrain.RUINS],
                   pc().get(Terrain.RUINS))
RENDERERS[Terrain.HOUSE] = \
    SimpleRenderer(PAINTERS[Terrain.HOUSE],
                   pc().get(Terrain.HOUSE))
