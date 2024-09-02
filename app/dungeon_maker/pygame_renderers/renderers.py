from typing import Dict

import os

from app.dungeon_maker.terrain import Terrain
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.painters import (
    FloorPainter, 
    WallTopPainter, 
    WallBottomPainter,
    StairsUpDownPainter, 
    StairsLeftPainter, 
    StairsRightPainter, 
    RandomPainter,
    RandomShadingPainter,
    GrassPainter,
    RuinsPainter,
)
from app.dungeon_maker.pygame_renderers import (
    SimpleRenderer,
    SimpleLimitRenderer, 
    SimpleLimitShadingRenderer, 
    LimitRenderer, 
    FloorShadingRenderer,
    Limit8ShadingRenderer,
    Limit16ShadingRenderer,
)

RendererDatabase = Dict[Terrain, object]

def get_renderers(palette: str) -> RendererDatabase:
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + "dungeon"

    return {
        Terrain.VOID: SimpleRenderer(Painter(), os.path.join(palette_dir, 'void.png')),
        Terrain.FLOOR_LOWER: FloorShadingRenderer(FloorPainter(), os.path.join(palette_dir, 'floor1.png'), os.path.join(palette_dir, 'floor1_shading.png')),
        Terrain.FLOOR_UPPER: FloorShadingRenderer(FloorPainter(), os.path.join(palette_dir, 'floor2.png'), os.path.join(palette_dir, 'floor2_shading.png')),
        Terrain.WALL_TOP: LimitRenderer(WallTopPainter(), os.path.join(palette_dir, 'wall_top.png')),
        Terrain.WALL_BOTTOM: SimpleRenderer(WallBottomPainter(), os.path.join(palette_dir, 'wall_bottom.png')),
        Terrain.STAIRS_UP: SimpleRenderer(StairsUpDownPainter(), os.path.join(palette_dir, 'stairs_updown.png')),
        Terrain.STAIRS_DOWN: SimpleRenderer(StairsUpDownPainter(), os.path.join(palette_dir, 'stairs_updown.png')),
        Terrain.STAIRS_LEFT: SimpleRenderer(StairsLeftPainter(), os.path.join(palette_dir, 'stairs_left.png')),
        Terrain.STAIRS_RIGHT: SimpleRenderer(StairsRightPainter(), os.path.join(palette_dir, 'stairs_right.png')),
        Terrain.PILLAR: SimpleRenderer(Painter(), os.path.join(palette_dir, 'pillar.png')),
        Terrain.SPARSE_FOREST: SimpleLimitShadingRenderer(RandomShadingPainter(), os.path.join(palette_dir, 'forest.png')),
        Terrain.GRASS: Limit8ShadingRenderer(GrassPainter(), os.path.join(palette_dir, 'floor1.png'), os.path.join(palette_dir, 'floor1_shading.png')),
        Terrain.RUINS: Limit16ShadingRenderer(RuinsPainter(), os.path.join(palette_dir, 'floor2.png'), os.path.join(palette_dir, 'floor2_shading.png')),
        Terrain.START: SimpleRenderer(Painter(), os.path.join(palette_dir, 'start_end.png')),
        Terrain.END: SimpleRenderer(Painter(), os.path.join(palette_dir, 'start_end.png')),
    }
