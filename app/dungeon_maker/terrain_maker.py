import os
import random

from app.constants import TILEWIDTH, TILEHEIGHT
from app.engine import engine, static_random
from app.utilities import utils

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
            coord = random_choice([(4, k) for k in range(self.limits[4])], pos)
        elif top and corner:
            coord = random_choice([(5, k) for k in range(self.limits[5])], pos)
        elif left:
            coord = random_choice([(1, k) for k in range(self.limits[1])], pos)
        elif corner:
            coord = random_choice([(3, k) for k in range(self.limits[3])], pos)
        elif top:
            coord = random_choice([(2, k) for k in range(self.limits[2])], pos)
        else:
            coord = random_choice([(0, k) for k in range(self.limits[0])], pos)

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]

        if north == 'Pillar':
            coord = (0, 5)
            new_coords1 = [(coord[0]*2, coord[1]*2)]
            new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]

        return new_coords1, new_coords2, new_coords3, new_coords4

class WallTerrain(WangEdge2Terrain16):
    terrain_like = ('Wall', )

    def __init__(self,tileset_image_fn):
        super().__init__(tileset_image_fn)
        self.wall_grid = {}

    def single_process(self, tilemap) -> None:
        all_walls = {pos for pos, terrain in tilemap.terrain_grid.items() if terrain == 'Wall'}

        for pos in all_walls.copy():
            north, east, south, west = tilemap.get_cardinal_terrain(pos)
            if east != 'Wall' and west != 'Wall' and south != 'Wall':
                if tilemap.calc_layer(pos) == 1 and north == 'Wall':
                    self.wall_grid[pos] = 'Bottom'
                else:
                    self.wall_grid[pos] = 'Top'
                all_walls.remove(pos)

        for pos in all_walls.copy():
            south = (pos[0], pos[1] + 1)
            if south in self.wall_grid:
                self.wall_grid[pos] = 'Top'
                all_walls.remove(pos)

        for pos in all_walls.copy():
            north = (pos[0], pos[1] - 1)
            south = (pos[0], pos[1] + 1)
            if tilemap.get_terrain(north) == 'Wall' and tilemap.get_terrain(south) != 'Wall' and \
                    (tilemap.get_layer(pos) == 1 or tilemap.get_layer(south) == 1):
                self.wall_grid[pos] = 'Bottom'
                all_walls.remove(pos)

        for pos in all_walls:
            self.wall_grid[pos] = 'Top'

        # Convert pieces that are surrounded to void
        convert_to_void = set()
        for pos in self.wall_grid.keys():
            if all(kind == 'Top' or not tilemap.check_bounds(*adj) for kind, adj in 
                   zip(self.get_cardinal_wallgrid(pos) + self.get_diagonal_wallgrid(pos),
                       utils.get_cardinal_positions(pos) + utils.get_diagonal_positions(pos))):
                convert_to_void.add(pos)

        for pos in convert_to_void:
            self.wall_grid[pos] = 'Void'

    def get_cardinal_wallgrid(self, pos: tuple) -> tuple:
        return list(self.wall_grid.get(adj, None) for adj in utils.get_cardinal_positions(pos))

    def get_diagonal_wallgrid(self, pos: tuple) -> tuple:
        return list(self.wall_grid.get(adj, None) for adj in utils.get_diagonal_positions(pos))

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)

        # Check if we are in a layer 1 room and need to display the lower portion of the wall
        if self.wall_grid[pos] == 'Bottom':
            left, right, shadow = True, True, False
            if west in self.terrain_like and southwest not in self.terrain_like:
                left = False
            if east in self.terrain_like and southeast not in self.terrain_like:
                right = False
            if southwest in self.terrain_like or southwest == 'Pillar':
                shadow = True

            if left and right:
                coord = (0, 5)
            elif left:
                if shadow:
                    coord = (4, 5)
                else:
                    coord = (1, 5)
            elif right:
                coord = (2, 5)
            else:
                coord = (3, 5)

        elif self.wall_grid[pos] == 'Top': # Display the normal upper portion of the wall
            nwall, ewall, swall, wwall = self.get_cardinal_wallgrid(pos)
            newall, sewall, swwall, nwwall = self.get_diagonal_wallgrid(pos)
            # Edge is true when we have an adjacent walllike
            north_edge = bool(north in self.terrain_like and nwall not in ('Bottom', 'Void'))
            south_edge = bool(south in self.terrain_like and swall not in ('Bottom', 'Void'))
            east_edge = bool(east in self.terrain_like and ewall not in ('Bottom', 'Void'))
            west_edge = bool(west in self.terrain_like and wwall not in ('Bottom', 'Void'))
            index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
            coord = random_choice([(index, k) for k in range(self.limits[index])], pos)

            if index in (12, 13) and swwall == 'Top':
                coord = (15, 5)
            elif index in (6, 7) and sewall == 'Top':
                coord = (15, 4)
            elif index in (14, 15) and sewall == 'Top' and swwall == 'Top':
                coord = (15, 3) 

        elif self.wall_grid[pos] == 'Void':
            coord = (15, 2)

        else:
            print("Wall was not correctly processed: ", pos)

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class StairsUpDownTerrain(Terrain):
    terrain_like = ('StairsUpDown', )

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

class StairsLeftTerrain(Terrain):
    terrain_like = ('StairsLeft', )

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        north, _, south, _ = tilemap.get_cardinal_terrain(pos)
        top = False
        if north not in self.terrain_like:
            top = True

        if top:
            coord = 0, 0
        else:
            coord = 1, 0

        new_coords1 = [(coord[0]*2, coord[1]*2)]
        new_coords2 = [(coord[0]*2 + 1, coord[1]*2)]
        new_coords3 = [(coord[0]*2 + 1, coord[1]*2 + 1)]
        new_coords4 = [(coord[0]*2, coord[1]*2 + 1)]
        return new_coords1, new_coords2, new_coords3, new_coords4

class StairsRightTerrain(StairsLeftTerrain):
    terrain_like = ('StairsRight', )

class PillarTerrain(Terrain):
    terrain_like = ('Pillar', )

def get_terrain(palette: str):
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + 'dungeon'
    return {'Floor': FloorTerrain(os.path.join(palette_dir, 'floor.png')),
            'Floor2': FloorTerrain(os.path.join(palette_dir, 'floor2.png')),
            'Wall': WallTerrain(os.path.join(palette_dir, 'wall.png')),
            'Pillar': PillarTerrain(os.path.join(palette_dir, 'pillar.png')),
            'StairsUpDown': StairsUpDownTerrain(os.path.join(palette_dir, 'stairs_updown.png')),
            'StairsLeft': StairsLeftTerrain(os.path.join(palette_dir, 'stairs_left.png')),
            'StairsRight': StairsRightTerrain(os.path.join(palette_dir, 'stairs_right.png')),
            }
