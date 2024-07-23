from typing import Dict

import os

from app.dungeon_maker.terrain_generation import Terrain
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.painters import FloorPainter, WallTopPainter, WallBottomPainter
from app.dungeon_maker.pygame_renderers import LimitRenderer, ShadingRenderer, SimpleRenderer

RendererDatabase = Dict[Terrain, object]

def get_renderers(palette: str) -> RendererDatabase:
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + "dungeon"

    return {
        Terrain.VOID: SimpleRenderer(Painter(), os.path.join(palette_dir, 'void.png')),
        Terrain.FLOOR_LOWER: ShadingRenderer(FloorPainter(), os.path.join(palette_dir, 'floor1.png'), os.path.join(palette_dir, 'floor1_shading.png')),
        Terrain.FLOOR_UPPER: ShadingRenderer(FloorPainter(), os.path.join(palette_dir, 'floor2.png'), os.path.join(palette_dir, 'floor2_shading.png')),
        Terrain.WALL_TOP: LimitRenderer(WallTopPainter(), os.path.join(palette_dir, 'wall_top.png')),
        Terrain.WALL_BOTTOM: SimpleRenderer(WallBottomPainter(), os.path.join(palette_dir, 'wall_bottom.png')),
        Terrain.START: SimpleRenderer(Painter(), os.path.join(palette_dir, 'stairs_updown.png')),
        Terrain.END: SimpleRenderer(Painter(), os.path.join(palette_dir, 'stairs_updown.png')),
    }
