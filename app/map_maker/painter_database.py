from app.map_maker.terrain import Terrain
from app.map_maker.painters import \
    GrassPainter

PAINTERS = {}

PAINTERS[Terrain.GRASS] = GrassPainter()
