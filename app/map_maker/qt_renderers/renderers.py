from typing import Any, Dict

import os

from app.map_maker.terrain import Terrain
from app.map_maker.qt_renderers import (
    SimpleRenderer)
from app.map_maker.palette_collection import PaletteCollection

class RendererDatabase:
    """RendererDatabase = Dict[Terrain, Renderer]"""

    def __init__(self, palette_collection: PaletteCollection):
        self.palette_collection = palette_collection

    def get(self, terrain: Terrain) -> Any:
        match terrain:
            case Terrain.CASTLE:
                return SimpleRenderer(CastlePainter(), self.palette_collection.get_palette(terrain))

def get_renderers(palette_dir: str) -> RendererDatabase:
    palette_collection_dir = 'app/map_maker/palettes/'
    if os.path.isdir(palette_collection_dir + palette_dir):
        palette_dir = palette_collection_dir + palette_dir
    else:
        raise KeyError(f"No directory {palette_collection_dir + palette_dir} located to load palette from.")
    return RendererDatabase(palette_dir)
