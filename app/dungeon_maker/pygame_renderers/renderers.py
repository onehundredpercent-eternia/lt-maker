from typing import Any, Dict
from functools import lru_cache

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
    WaterPainter,
    WaterBridgePainter,
)
from app.dungeon_maker.pygame_renderers import (
    SimpleRenderer,
    SimpleLimitRenderer, 
    SimpleLimitShadingRenderer, 
    LimitRenderer, 
    SimpleShadingRenderer,
    FloorShadingRenderer,
    CheckerboardFloorShadingRenderer,
    Limit8ShadingRenderer,
    Limit16ShadingRenderer,
)

class RendererDatabase:
    """RendererDatabase = Dict[Terrain, Renderer]"""

    def __init__(self, palette_dir: str):
        self.palette_dir = palette_dir

    @lru_cache(64)
    def get(self, terrain: Terrain) -> Any:
        match terrain:
            case Terrain.VOID: 
                return SimpleRenderer(Painter(), os.path.join(self.palette_dir, 'void.png'))
            case Terrain.FLOOR_LOWER: 
                return FloorShadingRenderer(FloorPainter(), os.path.join(self.palette_dir, 'floor1.png'), os.path.join(self.palette_dir, 'floor1_shading.png'))
            case Terrain.FLOOR_UPPER: 
                return FloorShadingRenderer(FloorPainter(), os.path.join(self.palette_dir, 'floor2.png'), os.path.join(self.palette_dir, 'floor2_shading.png'))
            case Terrain.WALL_TOP: 
                return LimitRenderer(WallTopPainter(), os.path.join(self.palette_dir, 'wall_top.png'))
            case Terrain.WALL_BOTTOM: 
                return SimpleRenderer(WallBottomPainter(), os.path.join(self.palette_dir, 'wall_bottom.png'))
            case Terrain.STAIRS_UP: 
                return SimpleRenderer(StairsUpDownPainter(), os.path.join(self.palette_dir, 'stairs_updown.png'))
            case Terrain.STAIRS_DOWN: 
                return SimpleRenderer(StairsUpDownPainter(), os.path.join(self.palette_dir, 'stairs_updown.png'))
            case Terrain.STAIRS_LEFT: 
                return SimpleRenderer(StairsLeftPainter(), os.path.join(self.palette_dir, 'stairs_left.png'))
            case Terrain.STAIRS_RIGHT: 
                return SimpleRenderer(StairsRightPainter(), os.path.join(self.palette_dir, 'stairs_right.png'))
            case Terrain.PILLAR: 
                return SimpleRenderer(Painter(), os.path.join(self.palette_dir, 'pillar.png'))
            case Terrain.SPARSE_FOREST: 
                return SimpleLimitShadingRenderer(RandomShadingPainter(), os.path.join(self.palette_dir, 'forest.png'))
            case Terrain.GRASS: 
                return Limit8ShadingRenderer(GrassPainter(), os.path.join(self.palette_dir, 'floor1.png'), os.path.join(self.palette_dir, 'floor1_shading.png'))
            case Terrain.RUINS_LOWER: 
                return Limit16ShadingRenderer(RuinsPainter(), os.path.join(self.palette_dir, 'floor1.png'), os.path.join(self.palette_dir, 'floor1_shading.png'))
            case Terrain.RUINS_UPPER: 
                return Limit16ShadingRenderer(RuinsPainter(), os.path.join(self.palette_dir, 'floor2.png'), os.path.join(self.palette_dir, 'floor2_shading.png'))
            case Terrain.CHECKERBOARD_LOWER: 
                return CheckerboardFloorShadingRenderer(FloorPainter(), os.path.join(self.palette_dir, 'floor1.png'), os.path.join(self.palette_dir, 'floor1_shading.png'), os.path.join(self.palette_dir, 'floor1_beta.png'), os.path.join(self.palette_dir, 'floor1_shading_beta.png'))
            case Terrain.CHECKERBOARD_UPPER: 
                return CheckerboardFloorShadingRenderer(FloorPainter(), os.path.join(self.palette_dir, 'floor2.png'), os.path.join(self.palette_dir, 'floor2_shading.png'), os.path.join(self.palette_dir, 'floor2_beta.png'), os.path.join(self.palette_dir, 'floor2_shading_beta.png'))
            case Terrain.WATER: 
                return FloorShadingRenderer(WaterPainter(), os.path.join(self.palette_dir, 'water.png'), os.path.join(self.palette_dir, 'water_shading.png'))
            case Terrain.WATERBRIDGE: 
                return SimpleShadingRenderer(WaterBridgePainter(), os.path.join(self.palette_dir, 'bridge.png'))
            case Terrain.START: 
                return SimpleRenderer(Painter(), os.path.join(self.palette_dir, 'start_end.png'))
            case Terrain.END: 
                return SimpleRenderer(Painter(), os.path.join(self.palette_dir, 'start_end.png'))

def get_renderers(palette: str) -> RendererDatabase:
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + "dungeon"
    return RendererDatabase(palette_dir)
