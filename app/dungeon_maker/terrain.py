from enum import Enum

class Terrain(Enum):
    VOID = 0
    WALL_TOP = 1
    WALL_BOTTOM = 2
    FLOOR_UPPER = 3
    FLOOR_LOWER = 4
    WATER = 5
    STAIRS_UP = 6
    STAIRS_RIGHT = 7
    STAIRS_DOWN = 8
    STAIRS_LEFT = 9
    PILLAR = 10
    SPARSE_FOREST = 11
    GRASS = 12
    RUINS_LOWER = 13
    RUINS_UPPER = 14
    CHECKERBOARD_LOWER = 15
    CHECKERBOARD_UPPER = 16
    WATERBRIDGE = 17
    START = 98
    END = 99

    def floor_terrain():
        return {
            Terrain.FLOOR_LOWER, 
            Terrain.FLOOR_UPPER, 
            Terrain.STAIRS_UP, 
            Terrain.STAIRS_RIGHT, 
            Terrain.STAIRS_DOWN, 
            Terrain.STAIRS_LEFT,
            Terrain.SPARSE_FOREST,
            Terrain.GRASS,
            Terrain.RUINS_LOWER,
            Terrain.RUINS_UPPER,
            Terrain.CHECKERBOARD_LOWER,
            Terrain.CHECKERBOARD_UPPER,
            Terrain.WATERBRIDGE,
            Terrain.PILLAR,
            Terrain.START,
            Terrain.END,
        }
