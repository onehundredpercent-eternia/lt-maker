from app.map_maker.terrain import Terrain
from app.map_maker.qt_renderers import (
    SimpleRenderer)
from app.map_maker.palette_collection import \
    get_current_palette_collection
from app.map_maker.painter_database import PAINTERS

pc = get_current_palette_collection

RENDERERS = {}

RENDERERS[Terrain.GRASS] = \
    SimpleRenderer(PAINTERS[Terrain.GRASS], 
                   pc().get(Terrain.GRASS))
