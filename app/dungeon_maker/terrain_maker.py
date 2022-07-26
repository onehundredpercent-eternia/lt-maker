import os
import random

from app.constants import TILEWIDTH, TILEHEIGHT
from app.engine import engine, static_random

def random_choice(choices: list, pos: tuple, seed: int = None, offset: int = 0):
    if seed is None:
        seed = static_random.get_seed()
    random.seed(seed + pos[0] * 1024**2 + pos[1] * 1024 + offset)
    return random.choice(choices)

class Terrain():
    base_coord = (0, 0)

    def __init__(self, tileset_image_fn):
        self.tileset_image = engine.image_load(tileset_image_fn)

    def _find_limit(self, idx: int, width: int = TILEWIDTH, height: int = TILEHEIGHT) -> int:
        bg_color = (0, 0, 0)
        x = idx * width
        for y in range(0, self.tileset_image.get_height(), height):
            current_color = self.tileset_image.get_at((x, y))
            if current_color[:3] == bg_color[:3]:
                return y // TILEHEIGHT
        return self.tileset_image.get_height() // TILEHEIGHT

    def single_process(self, tilemap) -> None:
        pass

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        new_coords1 = [(self.base_coord[0]*2, self.base_coord[1]*2)]
        new_coords2 = [(self.base_coord[0]*2 + 1, self.base_coord[1]*2)]
        new_coords3 = [(self.base_coord[0]*2 + 1, self.base_coord[1]*2 + 1)]
        new_coords4 = [(self.base_coord[0]*2, self.base_coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

    def get_image(self, tile_coord) -> engine.Surface:
        im = engine.subsurface(self.tileset_image, (
            tile_coord[0] * TILEWIDTH//2,
            tile_coord[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2))
        return im

class WangEdge2Terrain16(Terrain):
    def __init__(self, tileset_image_fn):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(16)}

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index = self._determine_index(tilemap, pos)
        coord = random_choice([(index, k) for k in range(self.limits[index])], pos)
        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class FloorTerrain(Terrain):
    terrain_like = ('Floor', )

    def __init__(self, tileset_image_fn):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(6)}

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, _, _, west = tilemap.get_cardinal_terrain(pos)
        _, _, _, northwest = tilemap.get_diagonal_terrain(pos)
        top, left, corner = False, False, False

        if north == 'Wall':
            top = True
        if west == 'Wall':
            left = True
        if northwest == 'Pillar':
            corner = True
        if west == 'Pillar':
            left = True

        if top and left:
            coord = (4, 0)
        elif top and corner:
            coord = (5, 0)
        elif left:
            coord = (1, 0)
        elif corner:
            coord = (3, 0)
        elif top:
            coord = random_choice([(2, k) for k in range(self.limits[2])], pos)
        else:
            coord = random_choice([(0, k) for k in range(self.limits[0])], pos)

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]

        if north == 'Pillar':
            coord = (0, 3)
            new_coords1 = [(coord[0]*2, coord[1]*2)]
            new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]

        return new_coords1, new_coords2, new_coords3, new_coords4

class WallTerrain(WangEdge2Terrain16):
    terrain_like = ('Wall', )

    def _determine_index(self, tilemap, pos: tuple, ignore_south: bool = False) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        # Edge is true when we have an adjacent walllike
        north_edge = bool(north in self.terrain_like)
        south_edge = bool(south in self.terrain_like) and not ignore_south
        east_edge = bool(east in self.terrain_like)
        west_edge = bool(west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)

        # Check if we are in a layer 1 room and need to display the lower portion of the wall
        if north in self.terrain_like and tilemap.get_layer(pos) == 1 and south not in self.terrain_like:
            left, right, shadow = True, True, False
            if west in self.terrain_like and southwest not in self.terrain_like:
                left = False
            if east in self.terrain_like and southeast not in self.terrain_like:
                right = False
            if southwest in self.terrain_like or southwest == 'Pillar':
                shadow = True

            if left and right:
                coord = (0, 4)
            elif left:
                coord = (1, 4)
            elif right:
                coord = (2, 4)
            else:
                coord = (3, 4)

        else: # Display the normal upper portion of the wall
            ignore_south = south in self.terrain_like and tilemap.get_layer(pos[0], pos[1] + 1) != 1
            index = self._determine_index(tilemap, pos, ignore_south)
            coord = random_choice([(index, k) for k in range(self.limits[index])], pos)

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class StairsUpDownTerrain(Terrain):
    terrain_like = ('StairsUpDown', )

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, _, south, _ = tilemap.get_cardinal_terrain(pos)
        top, bottom = False, False
        if north not in self.terrain_like:
            top = True
        if south not in self.terrain_like:
            bottom = True

        if top and bottom:
            coord = 0, 0
        elif top:
            coord = 1, 0
        elif bottom:
            coord = 2, 0
        else:
            coord = 3, 0 

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class StairsLeftTerrain(Terrain):
    terrain_like = ('StairsLeft', )

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        _, east, _, west = tilemap.get_cardinal_terrain(pos)
        left, right = False, False
        if east not in self.terrain_like:
            right = True
        if west not in self.terrain_like:
            left = True

        if left and right:
            coord = 0, 0
        elif left:
            coord = 1, 0
        elif right:
            coord = 2, 0
        else:
            coord = 3, 0 

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class StairsRightTerrain(StairsLeftTerrain):
    terrain_like = ('StairsRight', )

class PillarTerrain(Terrain):
    terrain_like = ('Pillar', )

class VoidTerrain(Terrain):
    terrain_like = ('Void', )

def get_terrain(theme: str):
    # Right now, there is only one theme
    theme_dir = 'app/dungeon_maker/palettes/dungeon/'
    return {'Floor': FloorTerrain(os.path.join(theme_dir, 'floor.png')),
            'Wall': WallTerrain(os.path.join(theme_dir, 'wall.png')),
            'Pillar': PillarTerrain(os.path.join(theme_dir, 'pillar.png')),
            'Void': VoidTerrain(os.path.join(theme_dir, 'void.png')),
            'StairsUpDown': StairsUpDownTerrain(os.path.join(theme_dir, 'stairs_updown.png')),
            'StairsLeft': StairsLeftTerrain(os.path.join(theme_dir, 'stairs_left.png')),
            'StairsRight': StairsRightTerrain(os.path.join(theme_dir, 'stairs_right.png')),
            }
