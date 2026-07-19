from typing import Dict

from app.map_maker.terrain import Terrain
from app.map_maker.painter_utils import Painter
from app.map_maker.painters import (
    WangEdge16Painter,
    WangEdge8Painter,
    GrassPainter,
    LightGrassPainter,
    NoisyGrassPainter,
    SandPainter,
    RiverPainter,
    SeaPainter,
    ForestPainter,
    RandomPainter,
    Random8Painter,
    HillPainter,
    MountainPainter,
    CliffPainter,
    DesertPainter,
    DesertRockPainter,
    CastlePainter,
    HousePainter,
    RuinsPainter,
    FloorPainter,
    WallTopPainter,
    WallBottomPainter,
    ColumnPainter,
    StairsUpDownPainter,
    StairsLeftPainter,
    StairsRightPainter,
    PoolPainter,
    PoolBridgePainter,
)


def create_painters() -> Dict[Terrain, Painter]:
    """Builds a fresh set of Painter instances, one per Terrain.

    Used both for the process-wide PAINTERS singleton below (the Qt editor
    and the standalone map_maker tool) and, separately, by the engine's
    MapPrefabTileMapObject to get its own independent painters instead of
    reusing the shared singleton -- see painter-singleton discussion in
    map_prefab_engine_plan.md Phase 3."""
    painters: Dict[Terrain, Painter] = {}

    # Outdoor
    painters[Terrain.GRASS] = GrassPainter()
    painters[Terrain.LIGHT_GRASS] = LightGrassPainter()
    painters[Terrain.NOISY_GRASS] = NoisyGrassPainter()
    painters[Terrain.SAND] = SandPainter()
    painters[Terrain.ROAD] = WangEdge8Painter()
    painters[Terrain.ROAD].terrain_like = \
       (Terrain.ROAD, Terrain.SAND, Terrain.BRIDGEH, Terrain.BRIDGEV,
        Terrain.HOUSE, Terrain.CASTLE,
        Terrain.FLOOR_1, Terrain.FLOOR_2, Terrain.FLOOR_3,
        Terrain.STAIRS_LEFT, Terrain.STAIRS_RIGHT, Terrain.STAIRS_UPDOWN
        )
    painters[Terrain.ROAD].base_coord = (15, 0)
    painters[Terrain.RIVER] = RiverPainter()
    painters[Terrain.SEA] = SeaPainter()
    painters[Terrain.SPARSE_FOREST] = RandomPainter()
    painters[Terrain.SPARSE_FOREST].data = [(0, 0), (0, 1), (0, 2)]
    painters[Terrain.FOREST] = ForestPainter()
    painters[Terrain.THICKET] = Random8Painter()
    painters[Terrain.THICKET].data = [
       (x, y) for x in range(3) for y in range(3)
    ]
    painters[Terrain.HILL] = HillPainter()
    painters[Terrain.MOUNTAIN] = MountainPainter()
    painters[Terrain.CLIFF] = CliffPainter()
    painters[Terrain.DESERT] = DesertPainter()
    painters[Terrain.DESERT_CLIFF] = CliffPainter()
    painters[Terrain.DESERT_ROCK] = DesertRockPainter()
    painters[Terrain.BRIDGEH] = WangEdge16Painter()
    painters[Terrain.BRIDGEH].terrain_like = (Terrain.BRIDGEH, )
    painters[Terrain.BRIDGEV] = WangEdge16Painter()
    painters[Terrain.BRIDGEV].terrain_like = (Terrain.BRIDGEV, )
    painters[Terrain.CASTLE] = CastlePainter()
    painters[Terrain.HOUSE] = HousePainter()
    painters[Terrain.RUINS] = RuinsPainter()

    # Indoor
    painters[Terrain.VOID] = Painter()
    painters[Terrain.WALL_TOP] = WallTopPainter()
    painters[Terrain.WALL_BOTTOM] = WallBottomPainter()
    painters[Terrain.COLUMN] = ColumnPainter()
    painters[Terrain.FLOOR_1] = FloorPainter()
    painters[Terrain.FLOOR_2] = FloorPainter()
    painters[Terrain.FLOOR_3] = FloorPainter()
    painters[Terrain.STAIRS_UPDOWN] = StairsUpDownPainter()
    painters[Terrain.STAIRS_LEFT] = StairsLeftPainter()
    painters[Terrain.STAIRS_RIGHT] = StairsRightPainter()
    painters[Terrain.STAIRS_CENTER] = RandomPainter()
    painters[Terrain.STAIRS_CENTER].data = [(0, 0), (1, 0)]
    painters[Terrain.PILLAR] = Painter()
    painters[Terrain.POOL] = PoolPainter()
    painters[Terrain.POOL_BRIDGE] = PoolBridgePainter()
    painters[Terrain.TREASURE] = Painter()

    return painters


PAINTERS = create_painters()
