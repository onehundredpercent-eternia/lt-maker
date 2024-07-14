from typing import Dict

import os

from app.dungeon_maker.terrain_generation import Terrain
from app.dungeon_maker.painters import FloorPainter, WallPainter
from app.dungeon_maker.pygame_renderers import LimitRenderer, ShadingRenderer

RendererDatabase = Dict[Terrain, object]

def get_renderers(palette: str) -> RendererDatabase:
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + "dungeon"

    return {
        Terrain.FLOOR_LOWER: ShadingRenderer(FloorPainter(), os.path.join(palette_dir, 'floor.png'), os.path.join(palette_dir, 'floor_shading.png')),
        Terrain.WALL: LimitRenderer(WallPainter(), os.path.join(palette_dir, 'wall.png')),
    }
