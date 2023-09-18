from typing import Dict, Tuple

from app.utilities import utils

class DungeonTileMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.terrain_grid: Dict[Tuple[int, int], str] = {}
        self.tile_grid = {}  # pos -> engine.Surface
        self.layer_grid: Dict[Tuple[int, int], int] = {}

    def get_terrain(self, pos: Tuple[int, int]) -> str:
        return self.terrain_grid.get(pos, None)

    def get_true_terrain_grid(self) -> Dict[Tuple[int, int], str]:
        conversion_dict = \
            {'Floor2': 'Floor',
             'StairsUpDown': 'Stairs',
             'StairsLeft': 'Stairs',
             'StairsRight': 'Stairs',
             'Pillar2': 'Pillar',
             }
        return {pos: conversion_dict.get(terrain, terrain) for pos, terrain in self.terrain_grid.items()}

    def set_terrain(self, x: int, y: int, terrain: str):
        self.terrain_grid[(x, y)] = terrain

    def get_layer(self, pos: Tuple[int, int]) -> int:
        return self.layer_grid.get(pos, None)

    def calc_layer(self, pos: Tuple[int, int]) -> int:
        def south(pos: Tuple):
            return pos[0], pos[1] + 1

        while pos[1] < self.height:
            if self.get_layer(pos):
                return self.get_layer(pos)
            pos = south(pos)
        return None
    
    def set_layer(self, x: int, y: int, layer: int):
        self.layer_grid[(x, y)] = layer

    def reset_grid(self, terrain: str):
        self.layer_grid.clear()
        for x in range(self.width):
            for y in range(self.height):
                self.terrain_grid[(x, y)] = terrain
                self.layer_grid[(x, y)] = 1      

    def print_grid(self):
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                terrain = self.get_terrain((x, y))
                if terrain == 'Floor' or terrain == 'Floor2':
                    print("_", end='')
                elif terrain == 'Wall':
                    print("#", end='')
                elif terrain == 'Void':
                    print(" ", end='')
                elif terrain == 'Pillar' or terrain == 'Pillar2':
                    print("%", end='')
                elif terrain == 'StairsUpDown':
                    print("^", end='')
                elif terrain == 'StairsLeft':
                    print("<", end='')
                elif terrain == 'StairsRight':
                    print(">", end='')
                else:
                    print("S", end='')
            print("\n", end='')

    def print_layer_grid(self):
        for y in range(self.height):
            print("%02d " % y, end='')
            for x in range(self.width):
                layer = self.get_layer((x, y))
                print("%d" % layer, end='')
            print("\n", end='')

    def get_bounds(self):
        return (0, 0, self.width, self.height)

    def check_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cardinal_terrain(self, pos: tuple) -> tuple:
        return tuple([self.get_terrain(adj) for adj in utils.get_cardinal_positions(pos)])

    def get_diagonal_terrain(self, pos: tuple) -> tuple:
        return tuple([self.get_terrain(adj) for adj in utils.get_diagonal_positions(pos)])

    def get_cardinal_layers(self, pos: tuple) -> tuple:
        return tuple([self.get_layer(adj) for adj in utils.get_cardinal_positions(pos)])
