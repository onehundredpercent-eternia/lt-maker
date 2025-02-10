from app.map_maker.terrain import Terrain
from app.map_maker.painter_utils import Painter
from app.map_maker.painters import (
    GrassPainter, 
    LightGrassPainter,
    NoisyGrassPainter,
    SandPainter,
    WangEdge8Painter,
    RiverPainter,
    SeaPainter,
    ForestPainter,
    Random8Painter,
    HillPainter,
    MountainPainter,
    CliffPainter,
    WangEdge16Painter,
    CastlePainter,
    HousePainter,
    RuinsPainter,
    FloorPainter,
    WallTopPainter,
    WallBottomPainter,
    StairsUpDownPainter,
    StairsLeftPainter,
    StairsRightPainter,
)

PAINTERS = {}

# Outdoor
PAINTERS[Terrain.GRASS] = GrassPainter()
PAINTERS[Terrain.LIGHT_GRASS] = LightGrassPainter()
PAINTERS[Terrain.NOISY_GRASS] = NoisyGrassPainter()
PAINTERS[Terrain.SAND] = SandPainter()
PAINTERS[Terrain.ROAD] = WangEdge8Painter()
PAINTERS[Terrain.ROAD].terrain_like = (Terrain.ROAD, Terrain.SAND, Terrain.BRIDGEH, Terrain.BRIDGEV)
PAINTERS[Terrain.ROAD].base_coord = (15, 0)
PAINTERS[Terrain.RIVER] = RiverPainter()
PAINTERS[Terrain.SEA] = SeaPainter()
PAINTERS[Terrain.FOREST] = ForestPainter()
PAINTERS[Terrain.THICKET] = Random8Painter()
PAINTERS[Terrain.THICKET].data = [
   (17, 22), (18, 22), (19, 22), (17, 23), (18, 23), (19, 23), (18, 24), (19, 24), (18, 25)
]
PAINTERS[Terrain.THICKET].base_coord = (17 * 2, 22 * 2)
PAINTERS[Terrain.HILL] = HillPainter()
PAINTERS[Terrain.MOUNTAIN] = MountainPainter()
PAINTERS[Terrain.CLIFF] = CliffPainter()
PAINTERS[Terrain.BRIDGEH] = WangEdge16Painter()
PAINTERS[Terrain.BRIDGEH].terrain_like = (Terrain.BRIDGEH, )
PAINTERS[Terrain.BRIDGEV] = WangEdge16Painter()
PAINTERS[Terrain.BRIDGEV].terrain_like = (Terrain.BRIDGEV, )
PAINTERS[Terrain.CASTLE] = CastlePainter()
PAINTERS[Terrain.HOUSE] = HousePainter()
PAINTERS[Terrain.RUINS] = RuinsPainter()

# Indoor
PAINTERS[Terrain.VOID] = Painter()
PAINTERS[Terrain.WALL_TOP] = WallTopPainter()
PAINTERS[Terrain.WALL_BOTTOM] = WallBottomPainter()
PAINTERS[Terrain.FLOOR_1] = FloorPainter()
PAINTERS[Terrain.FLOOR_2] = FloorPainter()
PAINTERS[Terrain.STAIRS_UPDOWN] = StairsUpDownPainter()
PAINTERS[Terrain.STAIRS_LEFT] = StairsLeftPainter()
PAINTERS[Terrain.STAIRS_RIGHT] = StairsRightPainter()
PAINTERS[Terrain.PILLAR] = Painter()
