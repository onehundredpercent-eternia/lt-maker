import json
import os
import random

from app.constants import TILEWIDTH, TILEHEIGHT
from app.engine import engine
from app.map_maker import simplex_noise
from app.utilities import utils, static_random

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
                return y // height
        return self.tileset_image.get_height() // height

    def single_process(self, tilemap) -> None:
        pass

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        return self.get_image16(self.tileset_image, self.base_coord)

    def get_image8(self, base_image, tile_coord) -> engine.Surface:
        im = engine.subsurface(base_image, (
            tile_coord[0] * TILEWIDTH//2,
            tile_coord[1] * TILEHEIGHT//2,
            TILEWIDTH//2, TILEHEIGHT//2))
        return im.copy()

    def get_image16(self, base_image, tile_coord) -> engine.Surface:
        im = engine.subsurface(base_image, (
            tile_coord[0] * TILEWIDTH,
            tile_coord[1] * TILEHEIGHT,
            TILEWIDTH, TILEHEIGHT))
        return im.copy()

class SimpleTerrain(Terrain):
    def __init__(self, tileset_image_fn):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(1)}

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        coord = random_choice([(0, k) for k in range(self.limits[0])], pos)
        return self.get_image16(self.tileset_image, coord)

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

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        index = self._determine_index(tilemap, pos)
        coord = random_choice([(index, k) for k in range(self.limits[index])], pos)
        return self.get_image16(self.tileset_image, coord)

class WangCorner2Terrain16(WangEdge2Terrain16):
    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        northeast_edge = bool(not northeast or northeast in self.terrain_like)
        southeast_edge = bool(not southeast or southeast in self.terrain_like)
        northwest_edge = bool(not northwest or northwest in self.terrain_like)
        southwest_edge = bool(not southwest or southwest in self.terrain_like)
        index = 1 * northeast_edge + \
            2 * southeast_edge + \
            4 * southwest_edge + \
            8 * northwest_edge
        return index

class FloorTerrain(Terrain):
    """
    # Implements default 16x16 Floor
    """
    terrain_like = ('Floor', )

    def __init__(self, tileset_image_fn, shading_image_fn, offset=0):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(1)}
        self.offset = offset

    def _get_floor_shading(self, tilemap, pos, database, pillar=True) -> tuple:
        north, _, _, west = tilemap.get_cardinal_terrain(pos)
        _, _, _, northwest = tilemap.get_diagonal_terrain(pos)
        top, left, corner = False, False, False

        if north == 'Wall':
            top = True
        if west == 'Wall':
            left = True
        if northwest == 'Pillar' and pillar:
            corner = True
        if west == 'Pillar' and pillar:
            left = True
        if west and west == 'StairsLeft' and northwest == 'Wall':
            corner = True
        if northwest == 'Wall' and west and west.startswith('Floor') \
                and self._is_column_bottom(tilemap, (pos[0] - 1, pos[1]), database):
            corner = True

        shading_coord = None
        if top and left:
            shading_coord = (3, 0)
        elif top and corner:
            shading_coord = (4, 0)
        elif left:
            shading_coord = (0, 0)
        elif corner:
            shading_coord = (2, 0)
        elif top:
            shading_coord = (1, 0)

        return shading_coord

    def _is_column_bottom(self, tilemap, pos: tuple, database) -> bool:
        north, _, _, _ = tilemap.get_cardinal_terrain(pos)
        if north and north == 'Wall':
            north_pos = (pos[0], pos[1] - 1)
            nn_pos = (pos[0], pos[1] - 2)
            terrain_nid = tilemap.get_terrain(north_pos)
            terrain = database.get(terrain_nid)
            return terrain.wall_grid.get(nn_pos) == 'Top' and \
                terrain.get_top_coord(tilemap, nn_pos)[0] == 0
        return False

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        coord = random_choice([(0, k) for k in range(self.limits[0])], pos)
        shading_coord = self._get_floor_shading(tilemap, pos, database)

        base_image = self.get_image16(self.tileset_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = self.get_image16(self.shading_image, shading_coord)

        extra_image = None
        north, _, _, _ = tilemap.get_cardinal_terrain(pos)
        if north and north.startswith('Pillar'):
            extra_image = self.get_image16(self.shading_image, (5, 0))
        # column bottom
        elif self._is_column_bottom(tilemap, pos, database):
            extra_image = self.get_image16(self.shading_image, (6, 0))

        if extra_image:
            base_image.blit(extra_image, (0, 0))
        if shading_image:
            base_image.blit(shading_image, (0, 0))

        return base_image

class FloorRuinsTerrain(FloorTerrain):
    """
    # Implements 16x16 Floor with Ruins
    """
    noise_vertices: dict = {}
    noise_threshold: float = 0.5

    def __init__(self, tileset_image_fn, shading_image_fn, offset=0):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(16)}
        self.offset = offset

    def single_process(self, tilemap):
        # Generate a noise map and use that to fill the noise_vertices with True or False
        # depending on threshold
        seed = static_random.get_seed()
        noise_map: dict = simplex_noise.gen_noise_map(
            (tilemap.width * 2 + 1, tilemap.height * 2 + 1), seed,
            starting_frequency=0.125)
        self.noise_vertices = {pos: value > self.noise_threshold for pos, value in noise_map.items()}

    def _determine_index(self, tilemap, pos):
        center = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = self.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

        topleft = center + north + west + northwest >= 3
        topright = center + north + east + northeast >= 3
        bottomleft = center + south + west + southwest >= 3
        bottomright = center + south + east + southeast >= 3

        index = 1 * topright + \
            2 * bottomright + \
            4 * bottomleft + \
            8 * topleft
        return index

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        index = self._determine_index(tilemap, pos)
        coord = random_choice([(index, k) for k in range(self.limits[index])], pos)
        
        shading_coord = self._get_floor_shading(tilemap, pos, database)

        base_image = self.get_image16(self.tileset_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = self.get_image16(self.shading_image, shading_coord)

        extra_image = None
        north, _, _, _ = tilemap.get_cardinal_terrain(pos)
        if north and north.startswith('Pillar'):
            extra_image = self.get_image16(self.shading_image, (5, 0))
        # column bottom
        elif self._is_column_bottom(tilemap, pos, database):
            extra_image = self.get_image16(self.shading_image, (6, 0))

        if extra_image:
            base_image.blit(extra_image, (0, 0))
        if shading_image:
            base_image.blit(shading_image, (0, 0))

        return base_image

class FloorGrassTerrain(FloorRuinsTerrain):
    """
    # Implements 8x8 Floor with Grass
    """
    noise_vertices: dict = {}
    noise_threshold: float = 0.55

    def __init__(self, tileset_image_fn, shading_image_fn, offset=0):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        self.limits = {k: self._find_limit(k, 8, 8) for k in range(16)}
        self.offset = offset

    def _determine_index(self, tilemap, pos):
        center = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 1), False) 
        north = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2), False)
        east = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 1), False)
        south = self.noise_vertices.get((pos[0]*2 + 1, pos[1]*2 + 2), False)
        west = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 1), False)
        northwest = self.noise_vertices.get((pos[0]*2, pos[1]*2), False)
        northeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2), False)
        southwest = self.noise_vertices.get((pos[0]*2, pos[1]*2 + 2), False)
        southeast = self.noise_vertices.get((pos[0]*2 + 2, pos[1]*2 + 2), False)

        # Topleft
        index1 = 1 * north + \
            2 * center + \
            4 * west + \
            8 * northwest
        # Topright
        index2 = 1 * northeast + \
            2 * east + \
            4 * center + \
            8 * north
        # Bottomright
        index3 = 1 * east + \
            2 * southeast + \
            4 * south + \
            8 * center
        # Bottomleft
        index4 = 1 * center + \
            2 * south + \
            4 * southwest + \
            8 * west
        return index1, index2, index3, index4

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        index1, index2, index3, index4 = self._determine_index(tilemap, pos)
        coord1 = random_choice([(index1, k) for k in range(self.limits[index1])], (pos[0] * 2, pos[1] * 2))
        coord2 = random_choice([(index2, k) for k in range(self.limits[index2])], (pos[0] * 2 + 1, pos[1] * 2))
        coord3 = random_choice([(index3, k) for k in range(self.limits[index3])], (pos[0] * 2 + 1, pos[1] * 2 + 1))
        coord4 = random_choice([(index4, k) for k in range(self.limits[index4])], (pos[0] * 2, pos[1] * 2 + 1))
        
        shading_coord = self._get_floor_shading(tilemap, pos, database, pillar=False)

        base_image = engine.create_surface((16, 16))
        base_image.blit(self.get_image8(self.tileset_image, coord1), (0, 0))
        base_image.blit(self.get_image8(self.tileset_image, coord2), (8, 0))
        base_image.blit(self.get_image8(self.tileset_image, coord3), (8, 8))
        base_image.blit(self.get_image8(self.tileset_image, coord4), (0, 8))

        shading_image = None
        if shading_coord is not None:
            shading_image = self.get_image16(self.shading_image, shading_coord)

        extra_image = None
        north, _, _, _ = tilemap.get_cardinal_terrain(pos)
        if north and north.startswith('Pillar'):
            extra_image = self.get_image16(self.shading_image, (5, 0))
        # column bottom
        elif self._is_column_bottom(tilemap, pos, database):
            extra_image = self.get_image16(self.shading_image, (6, 0))

        if extra_image:
            base_image.blit(extra_image, (0, 0))
        if shading_image:
            base_image.blit(shading_image, (0, 0))

        return base_image

class WallTerrain(WangEdge2Terrain16):
    terrain_like = ('Wall', )

    def __init__(self, tileset_image_fn):
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

    def get_top_coord(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
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
        return coord

    def _determine_sprite_coord(self, tilemap, pos: tuple) -> tuple:
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
                north_pos = (pos[0], pos[1] - 1)
                if self.wall_grid.get(north_pos) == 'Top' and self.get_top_coord(tilemap, north_pos)[0] == 0:
                    coord = (6, 5)
                elif shadow:
                    coord = (5, 5)
                else:
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
            coord = self.get_top_coord(tilemap, pos)

        elif self.wall_grid[pos] == 'Void':
            coord = (15, 2)

        else:
            raise Exception("Wall was not correctly processed: %s" % pos)
        return coord

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        coord = self._determine_sprite_coord(tilemap, pos)
        return self.get_image16(self.tileset_image, coord)

class StairsUpDownTerrain(Terrain):
    terrain_like = ('StairsUpDown', )

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
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

        return self.get_image16(self.tileset_image, coord)

class StairsLeftTerrain(Terrain):
    terrain_like = ('StairsLeft', )

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        north, _, south, _ = tilemap.get_cardinal_terrain(pos)
        top = False
        if north not in self.terrain_like:
            top = True

        if top:
            coord = 0, 0
        else:
            coord = 1, 0

        return self.get_image16(self.tileset_image, coord)

class StairsRightTerrain(StairsLeftTerrain):
    terrain_like = ('StairsRight', )

class PillarTerrain(Terrain):
    terrain_like = ('Pillar', )

    def __init__(self, tileset_image_fn, shading_image_fn):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        self.limits = {k: self._find_limit(k) for k in range(1)}

    def determine_sprite(self, tilemap, pos: tuple, database) -> engine.Surface:
        coord = random_choice([(0, k) for k in range(self.limits[0])], pos)
        base_image = self.get_image16(self.tileset_image, coord)

        north, _, _, west = tilemap.get_cardinal_terrain(pos)
        _, _, _, northwest = tilemap.get_diagonal_terrain(pos)
        top, left, corner = False, False, False

        if north == 'Wall':
            top = True
        if west == 'Wall':
            left = True
        if west and west.startswith('Stairs') and northwest == 'Wall':
            corner = True
        
        shading_coord = None
        if top and left:
            shading_coord = (3, 0)
        elif top and corner:
            shading_coord = (4, 0)
        elif left:
            shading_coord = (0, 0)
        elif corner:
            shading_coord = (2, 0)
        elif top:
            shading_coord = (1, 0)

        if shading_coord:
            shading_image = self.get_image16(self.shading_image, shading_coord)
            base_image.blit(shading_image, (0, 0))
        return base_image

def get_terrain(palette: str):
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + 'dungeon'
    # Interrogate palette data
    data = {}
    with open(os.path.join(palette_dir, 'metadata.json')) as load_file:
        data = json.load(load_file)

    floor1 = data.get('floor1', 'default')
    floor2 = data.get('floor2', 'default')
    water = data.get('water', False)

    if floor1 == 'ruins':
        floor1_terrain = FloorRuinsTerrain(os.path.join(palette_dir, 'floor1_ruins.png'), os.path.join(palette_dir, 'floor1_shading.png'))
    elif floor1 == 'grass':
        floor1_terrain = FloorGrassTerrain(os.path.join(palette_dir, 'floor1_grass.png'), os.path.join(palette_dir, 'floor1_shading.png'))
    else:
        floor1_terrain = FloorTerrain(os.path.join(palette_dir, 'floor1.png'), os.path.join(palette_dir, 'floor1_shading.png'))

    if floor2 == 'ruins':
        floor2_terrain = FloorRuinsTerrain(os.path.join(palette_dir, 'floor2_ruins.png'), os.path.join(palette_dir, 'floor2_shading.png'), 1)
    elif floor2 == 'grass':
        floor2_terrain = FloorGrassTerrain(os.path.join(palette_dir, 'floor2_grass.png'), os.path.join(palette_dir, 'floor2_shading.png'), 1)
    else:
        floor2_terrain = FloorTerrain(os.path.join(palette_dir, 'floor2.png'), os.path.join(palette_dir, 'floor2_shading.png'), 1)

    return {'Floor': floor1_terrain,
            'Floor2': floor2_terrain,
            'Wall': WallTerrain(os.path.join(palette_dir, 'wall.png')),
            'Pillar': PillarTerrain(os.path.join(palette_dir, 'pillar1.png'), os.path.join(palette_dir, 'floor1_shading.png')),
            'Pillar2': PillarTerrain(os.path.join(palette_dir, 'pillar2.png'), os.path.join(palette_dir, 'floor2_shading.png')),
            'StairsUpDown': StairsUpDownTerrain(os.path.join(palette_dir, 'stairs_updown.png')),
            'StairsLeft': StairsLeftTerrain(os.path.join(palette_dir, 'stairs_left.png')),
            'StairsRight': StairsRightTerrain(os.path.join(palette_dir, 'stairs_right.png')),
            }
