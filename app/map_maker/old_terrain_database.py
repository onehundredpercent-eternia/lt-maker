from PyQt5.QtGui import QPixmap

import app.utilities as utils
from app.map_maker.utilities import random_choice, edge_random, flood_fill, find_bounds
from app.map_maker.terrain import Terrain, TerrainCatalog
from app.map_maker.wang_terrain import WangCorner2Terrain, WangEdge2Terrain, WangEdge2Terrain16
from app.map_maker.building_terrain import CastleTerrain, HouseTerrain, RuinsTerrain
from app.map_maker.cliff_terrain import CliffTerrain
from app.map_maker.sea_terrain import SeaTerrain
from app.map_maker.grass_terrain import GrassTerrain, LightGrassTerrain
from app.map_maker.floor_terrain import FloorTerrain, WallTerrain, PillarTerrain
from app.map_maker.mountain_terrain import MountainTerrain
                
original_palette = 'app/map_maker/palettes/westmarch'

Grass = GrassTerrain('Grass', 'Grass', original_palette, 'grass.png')
LightGrass = LightGrassTerrain('Light Grass', 'Light Grass', original_palette, 'grass.png')

Road = WangEdge2Terrain('Road', 'Road', original_palette, 'road.png')
Road.terrain_like = ('Sand', 'Road', 'BridgeH', 'BridgeV')

River = RiverTerrain('River', 'River', original_palette, 'river.png')
River.autotiles = \
    {(0, 8): 0, (0, 9): 1, (1, 6): 2, (1, 7): 3, (1, 8): 4, (1, 9): 5, (2, 6): 6, (2, 7): 7, (2, 8): 8, (2, 9): 9, (3, 0): 10, (3, 1): 11, (3, 2): 12,
     (3, 3): 13, (3, 8): 14, (3, 9): 15, (4, 6): 16, (4, 7): 17, (4, 8): 18, (4, 9): 19, (5, 8): 20, (5, 9): 21, (7, 0): 22, (7, 3): 23, (7, 4): 13, (7, 6): 24, 
     (7, 7): 25, (7, 8): 26, (7, 9): 27, (8, 6): 28, (8, 7): 29, (9, 0): 30, (9, 1): 31, (11, 1): 32, (11, 2): 33, (12, 0): 34, (12, 1): 35, (13, 6): 36, 
     (13, 7): 37, (13, 8): 38, (15, 0): 39, (15, 1): 39, (15, 2): 40, (15, 3): 40, (15, 4): 41, (15, 5): 41, (15, 6): 42, (15, 7): 42, (15, 8): 43, (15, 9): 43, 
     (1, 4): 44, (1, 5): 45, (2, 4): 46, (2, 5): 47, (4, 4): 48, (4, 5): 49, (8, 4): 50, (8, 5): 51}

Sand = SandTerrain('Sand', 'Sand', original_palette, 'sand.png')

Forest = ForestTerrain('Forest', 'Forest', original_palette, 'forest.png', (7, 0))

Thicket = RandomTerrain('Thicket', 'Thicket', original_palette, 'main.png', (17, 22))
Thicket.data = [(17, 22), (18, 22), (19, 22), (17, 23), (18, 23), (19, 23), (18, 24), (19, 24), (18, 25)]

Hill = HillTerrain('Hill', 'Hill', original_palette, 'main.png', (13, 21))

Mountain = MountainTerrain('Mountain', 'Mountain', original_palette, 'main.png', (8, 23))
Mountain.initial_process()

Cliff = CliffTerrain('Cliff', 'Cliff', original_palette, 'cliff.png', (15, 0))

Sea = SeaTerrain('Sea', 'Sea', original_palette, 'sea.png', (15, 0))
Sea.autotiles = \
    {(0, 4): 0, (0, 5): 1, (0, 6): 2, (0, 7): 2, (0, 8): 3, (0, 9): 3, (0, 10): 3, (0, 11): 2, (0, 12): 4, (0, 13): 2, (0, 14): 5, (0, 15): 3, (0, 16): 2,
     (0, 17): 4, (1, 0): 6, (1, 1): 7, (1, 4): 2, (1, 5): 3, (1, 6): 2, (1, 7): 2, (1, 8): 3, (1, 9): 3, (1, 10): 2, (1, 11): 3, (1, 12): 3, (1, 13): 3,
     (1, 14): 3, (1, 15): 3, (1, 16): 4, (1, 17): 2, (2, 1): 8, (2, 18): 9, (3, 0): 10, (3, 18): 11, (5, 18): 12, (6, 0): 13, (6, 2): 14, (6, 6): 15, 
     (6, 18): 9, (7, 1): 16, (7, 2): 17, (7, 3): 18, (7, 4): 19, (7, 6): 19, (7, 7): 20, (7, 18): 2, (7, 19): 21, (8, 1): 22, (9, 1): 23, (10, 0): 24, 
     (10, 1): 25, (10, 18): 26, (10, 19): 27, (10, 20): 28, (10, 21): 29, (11, 0): 30, (11, 1): 6, (12, 1): 31, (12, 3): 32, (12, 5): 33, (12, 7): 34, 
     (12, 19): 35, (13, 1): 36, (13, 2): 37, (13, 4): 38, (13, 5): 39, (13, 6): 40, (13, 7): 41, (13, 18): 42, (13, 19): 43, (14, 1): 44, (14, 2): 24, 
     (14, 3): 25, (14, 4): 45, (14, 5): 46, (14, 7): 25, (14, 18): 26, (14, 19): 27, (14, 20): 28, (14, 21): 29, (15, 2): 2, (15, 3): 43, (15, 4): 2, 
     (15, 5): 43, (15, 6): 2, (15, 7): 43, (15, 18): 2, (15, 19): 43, (15, 20): 2, (15, 21): 43, (16, 18): 47, (16, 19): 48, (18, 1): 49, (18, 3): 50, 
     (18, 4): 0, (18, 6): 0, (18, 7): 51, (18, 18): 0, (18, 19): 48, (19, 0): 52, (19, 6): 53, (19, 18): 11, (20, 18): 54, (20, 19): 55, (20, 20): 56, 
     (21, 18): 57, (21, 19): 58, (21, 20): 59, (22, 1): 60, (22, 2): 0, (22, 3): 61, (22, 5): 61, (22, 7): 60, (22, 10): 62, (22, 11): 53, (22, 18): 0, 
     (22, 19): 63, (22, 20): 0, (22, 21): 55, (23, 0): 2, (23, 1): 64, (23, 3): 64, (23, 4): 2, (23, 5): 65, (23, 7): 65, (23, 18): 2, (23, 19): 58, 
     (23, 20): 2, (23, 21): 58, (24, 1): 66, (24, 2): 67, (24, 4): 68, (24, 5): 69, (24, 6): 70, (24, 7): 71, (24, 18): 47, (24, 19): 62, (25, 1): 72, 
     (25, 3): 73, (25, 5): 74, (25, 7): 75, (25, 19): 76, (26, 2): 0, (26, 3): 62, (26, 4): 0, (26, 5): 62, (26, 6): 0, (26, 7): 62, (26, 18): 0, (26, 19): 62, 
     (26, 20): 0, (26, 21): 62, (27, 0): 10, (27, 2): 30, (27, 3): 6, (27, 4): 7, (27, 5): 77, (27, 6): 53, (27, 7): 68, (27, 18): 78, (27, 19): 79, 
     (27, 20): 80, (27, 21): 81, (28, 1): 82, (28, 18): 54, (28, 19): 62, (28, 20): 83, (28, 21): 62, (28, 22): 76, (28, 23): 43, (29, 18): 57, (29, 19): 43, 
     (29, 20): 57, (29, 21): 43, (29, 22): 35, (29, 23): 62, (30, 0): 0, (30, 1): 62, (30, 2): 0, (30, 3): 62, (30, 4): 0, (30, 5): 62, (30, 6): 0, (30, 7): 1, 
     (30, 8): 0, (30, 9): 62, (31, 0): 2, (31, 1): 43, (31, 2): 2, (31, 3): 43, (31, 4): 2, (31, 5): 3, (31, 6): 2, (31, 7): 43, (31, 8): 2, (31, 9): 43}

BridgeH = WangEdge2Terrain16('BridgeH', 'Bridge', original_palette, 'bridge_h.png', (0, 0))
BridgeH.terrain_like = ('BridgeH')
BridgeV = WangEdge2Terrain16('BridgeV', 'Bridge', original_palette, 'bridge_v.png', (0, 0))
BridgeV.terrain_like = ('BridgeV')

Castle = CastleTerrain('Castle', 'Castle', original_palette, 'main.png', (4, 27))
House = HouseTerrain('House', 'House', original_palette, 'main.png', (4, 25))
Ruins = RuinsTerrain('Ruins', 'Ruins', original_palette, 'main.png', (3, 28))

Floor = FloorTerrain('Floor', 'Floor', original_palette, 'floor.png', (0, 0))
Wall = WallTerrain('Wall', 'Wall', original_palette, 'wall.png', (0, 0))
Pillar = PillarTerrain('Pillar', 'Pillar', original_palette, 'pillar.png', (0, 0))

d = [Grass, LightGrass, Sand, Road, Forest, Thicket, Cliff, Hill, Mountain, River, Sea, BridgeH, BridgeV, House, Castle, Ruins, Floor, Wall, Pillar]
DB_terrain = TerrainCatalog(d)
