from app.map_maker.terrain import Terrain
from app.map_maker.qt_renderers import (
    SimpleRenderer,
    SimpleRenderer8,
    SeaRenderer,
    DisplayRenderer8,
    LimitRenderer8,
    LimitRenderer16,
    CliffRenderer,
    MountainRenderer,
    FloorShadingRenderer,
)
from app.map_maker.palette_collection import \
    get_current_outdoor_palette_collection, get_current_indoor_palette_collection
from app.map_maker.painter_database import PAINTERS

pco = get_current_outdoor_palette_collection
pci = get_current_outdoor_palette_collection

RENDERERS = {}

# Outdoor
RENDERERS[Terrain.GRASS] = \
    SimpleRenderer8(PAINTERS[Terrain.GRASS], 
                    pco().get(Terrain.GRASS))
RENDERERS[Terrain.LIGHT_GRASS] = \
    LimitRenderer8(PAINTERS[Terrain.LIGHT_GRASS], 
                   pco().get(Terrain.LIGHT_GRASS))
RENDERERS[Terrain.NOISY_GRASS] = \
    LimitRenderer8(PAINTERS[Terrain.NOISY_GRASS], 
                   pco().get(Terrain.NOISY_GRASS))
RENDERERS[Terrain.SAND] = \
    LimitRenderer8(PAINTERS[Terrain.SAND],
                   pco().get(Terrain.SAND))
RENDERERS[Terrain.ROAD] = \
    LimitRenderer8(PAINTERS[Terrain.ROAD],
                   pco().get(Terrain.ROAD))
RENDERERS[Terrain.RIVER] = \
    LimitRenderer8(PAINTERS[Terrain.RIVER],
                   pco().get(Terrain.RIVER))
RENDERERS[Terrain.SEA] = \
    SeaRenderer(PAINTERS[Terrain.SEA],
                pco().get(Terrain.SEA))
RENDERERS[Terrain.FOREST] = \
    DisplayRenderer8(PAINTERS[Terrain.FOREST],
                     pco().get(Terrain.FOREST))
RENDERERS[Terrain.THICKET] = \
    DisplayRenderer8(PAINTERS[Terrain.THICKET],
                     pco().get(Terrain.THICKET))
RENDERERS[Terrain.HILL] = \
    SimpleRenderer(PAINTERS[Terrain.HILL],
                   pco().get(Terrain.HILL))
RENDERERS[Terrain.MOUNTAIN] = \
    MountainRenderer(PAINTERS[Terrain.MOUNTAIN],
                     pco().get(Terrain.MOUNTAIN))
RENDERERS[Terrain.CLIFF] = \
    CliffRenderer(PAINTERS[Terrain.CLIFF],
                  pco().get(Terrain.CLIFF))
RENDERERS[Terrain.BRIDGEH] = \
    LimitRenderer16(PAINTERS[Terrain.BRIDGEH],
                    pco().get(Terrain.BRIDGEH))
RENDERERS[Terrain.BRIDGEV] = \
    LimitRenderer16(PAINTERS[Terrain.BRIDGEV],
                    pco().get(Terrain.BRIDGEV))
RENDERERS[Terrain.CASTLE] = \
    SimpleRenderer(PAINTERS[Terrain.CASTLE],
                   pco().get(Terrain.CASTLE))
RENDERERS[Terrain.RUINS] = \
    SimpleRenderer(PAINTERS[Terrain.RUINS],
                   pco().get(Terrain.RUINS))
RENDERERS[Terrain.HOUSE] = \
    SimpleRenderer(PAINTERS[Terrain.HOUSE],
                   pco().get(Terrain.HOUSE))

# Indoors
RENDERERS[Terrain.VOID] = \
    SimpleRenderer(PAINTERS[Terrain.VOID],
                   pci().get(Terrain.VOID))
RENDERERS[Terrain.FLOOR] = \
    FloorShadingRenderer(PAINTERS[Terrain.FLOOR],
                         pci().get(Terrain.FLOOR))
RENDERERS[Terrain.WALL_TOP] = \
    SimpleRenderer(PAINTERS[Terrain.WALL_TOP],
                   pci().get(Terrain.WALL_TOP))
RENDERERS[Terrain.WALL_BOTTOM] = \
    SimpleRenderer(PAINTERS[Terrain.WALL_BOTTOM],
                   pci().get(Terrain.WALL_BOTTOM))
RENDERERS[Terrain.STAIRS_UPDOWN] = \
    SimpleRenderer(PAINTERS[Terrain.STAIRS_UPDOWN],
                   pci().get(Terrain.STAIRS_UPDOWN))
RENDERERS[Terrain.STAIRS_LEFT] = \
    SimpleRenderer(PAINTERS[Terrain.STAIRS_LEFT],
                   pci().get(Terrain.STAIRS_LEFT))
RENDERERS[Terrain.STAIRS_RIGHT] = \
    SimpleRenderer(PAINTERS[Terrain.STAIRS_RIGHT],
                   pci().get(Terrain.STAIRS_RIGHT))
RENDERERS[Terrain.PILLAR] = \
    SimpleRenderer(PAINTERS[Terrain.PILLAR],
                   pci().get(Terrain.PILLAR))
