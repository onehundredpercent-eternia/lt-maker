from enum import Enum
import os
from typing import Dict, List, Optional, Tuple

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities import utils
from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain

from app.engine import engine

PaletteDatabase = Dict[Terrain, 'Palette']

def get_image16(base_image, coord) -> engine.Surface:
    im = engine.subsurface(base_image, (
        coord[0] * TILEWIDTH,
        coord[1] * TILEHEIGHT,
        TILEWIDTH, TILEHEIGHT))
    return im.copy()

def find_limit(image: engine.Surface, idx: int) -> int:
    bg_color = (0, 0, 0)
    x = idx * TILEWIDTH
    for y in range(0, image.get_height(), TILEHEIGHT):
        current_color = image.get_at((x, y))
        # If we've reached the bottom of the column in our image
        if current_color[:3] == bg_color[:3]:
            return y // TILEHEIGHT
    return image.get_height() // TILEHEIGHT

class Palette:
    base_coord: Pos = (0, 0)

    def __init__(self, tileset_image_fn: str):
        self.tileset_image = engine.image_load(tileset_image_fn)

    def single_process(self, dungeon_tilemap: DungeonTileMap) -> None:
        pass

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos, 
                         palette_database: PaletteDatabase) -> engine.Surface:
        return get_image16(self.tileset_image, self.base_coord)

class WangEdge2Palette(Palette):
    terrain_like: Tuple[Terrain] = tuple()

    def __init__(self, tileset_image_fn: str):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.limits = {k: find_limit(self.tileset_image, k) for k in range(16)}

    def _determine_index(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> int:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos, 
                         palette_database: PaletteDatabase) -> engine.Surface:
        idx = self._determine_index(dungeon_tilemap, position)
        coord = random_choice([(idx, k) for k in range(self.limits[idx])], position)
        return get_image16(self.tileset_image, coord)

class FloorPalette(Palette):
    def __init__(self, tileset_image_fn: str, shading_image_fn: str):
        self.tileset_image = engine.image_load(tileset_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        self.limit = find_limit(self.tileset_image, 0)

    def _get_floor_shading(self, dungeon_tilemap: DungeonTileMap, pos: Pos, palette_database: PaletteDatabase) -> Pos:
        north, _, _, west = dungeon_tilemap.get_cardinal_terrain(pos)
        _, _, _, northwest = dungeon_tilemap.get_diagonal_terrain(pos)
        top, left, corner = False, False, False

        if north == Terrain.WALL:
            top = True
        if west == Terrain.WALL:
            left = True
        # if northwest == 'Pillar' and pillar:
            # corner = True
        # if west == 'Pillar' and pillar:
            # left = True
        # if west and west == 'StairsLeft' and northwest == 'Wall':
            # corner = True
        # if northwest == Terrain.WALL and west and is_floor(west) \
        #         and self._is_column_bottom(tilemap, (pos[0] - 1, pos[1]), palette_database):
        #     corner = True

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

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap,
                         position: Pos,
                         palette_database: PaletteDatabase) -> engine.Surface:
        coord = random_choice([(0, k) for k in range(self.limit)], position)
        shading_coord = self._get_floor_shading(dungeon_tilemap, position, palette_database)

        base_image = get_image16(self.tileset_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.shading_image, shading_coord)

        if shading_image:
            base_image.blit(shading_image, (0, 0))

        return base_image

class WallPalette(WangEdge2Palette):
    terrain_like = (Terrain.WALL,)

    class WallKind(Enum):
        BOTTOM = 1
        TOP = 2

    def __init__(self, tileset_image_fn: str):
        super().__init__(tileset_image_fn)
        self.wall_grid = {}

    def single_process(self, dungeon_tilemap: DungeonTileMap) -> None:
        """
        Generates the wall grid, which is used to determine
        whether we need a TOP wall or a BOTTOM wall for this sprite
        """
        all_walls = {pos for pos, terrain in dungeon_tilemap.terrain_grid.items() if terrain == Terrain.WALL}

        # First, build standalone columns
        for pos in all_walls.copy():
            north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
            if east != Terrain.WALL and west != Terrain.WALL and south != Terrain.WALL:
                if dungeon_tilemap.calc_layer(pos) == 1 and north == Terrain.WALL:
                    self.wall_grid[pos] = self.WallKind.BOTTOM
                else:
                    self.wall_grid[pos] = self.WallKind.TOP
                all_walls.remove(pos)

        for pos in all_walls.copy():
            north, _, south, _ = dungeon_tilemap.get_cardinal_terrain(pos)
            if north == Terrain.WALL and south != Terrain.WALL:
                self.wall_grid[pos] = self.WallKind.BOTTOM
                all_walls.remove(pos)

        # All remaining walls are TOP walls
        for pos in all_walls:
            self.wall_grid[pos] = self.WallKind.TOP

    def _get_cardinal_wallgrid(self, pos: Pos) -> List[Optional[WallKind]]:
        return [self.wall_grid.get(adj, None) for adj in utils.get_cardinal_positions(pos)]

    def _get_diagonal_wallgrid(self, pos: Pos) -> List[Optional[WallKind]]:
        return [self.wall_grid.get(adj, None) for adj in utils.get_diagonal_positions(pos)]

    def _get_top_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        nwall, ewall, swall, wwall = self._get_cardinal_wallgrid(pos)
        newall, sewall, swwall, nwwall = self._get_diagonal_wallgrid(pos)
        # Edge is true when we have an adjacent walllike
        north_edge = bool(north in self.terrain_like and nwall != self.WallKind.BOTTOM)
        south_edge = bool(south in self.terrain_like and swall != self.WallKind.BOTTOM)
        east_edge = bool(east in self.terrain_like and ewall != self.WallKind.BOTTOM)
        west_edge = bool(west in self.terrain_like and wwall != self.WallKind.BOTTOM)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        coord = random_choice([(index, k) for k in range(self.limits[index])], pos)

        if index in (12, 13) and swwall == self.WallKind.TOP:
            coord = (15, 5)
        elif index in (6, 7) and sewall == self.WallKind.TOP:
            coord = (15, 4)
        elif index in (14, 15) and sewall == self.WallKind.TOP and swwall == self.WallKind.TOP:
            coord = (15, 3) 
        return coord

    def _determine_sprite_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
        north, east, south, west = dungeon_tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = dungeon_tilemap.get_diagonal_terrain(pos)

        if self.wall_grid[pos] == self.WallKind.BOTTOM:
            left, right, shadow = True, True, False
            if west in self.terrain_like and southwest not in self.terrain_like:
                left = False
            if east in self.terrain_like and southeast not in self.terrain_like:
                right = False
            if southwest in self.terrain_like: # or southwest == 'Pillar':
                shadow = True

            if left and right:
                north_pos = (pos[0], pos[1] - 1)
                if self.wall_grid.get(north_pos) == self.WallKind.TOP and self._get_top_coord(dungeon_tilemap, north_pos)[0] == 0:
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

        # Display the normal upper portion of the wall
        elif self.wall_grid[pos] == self.WallKind.TOP: 
            coord = self.get_top_coord(dungeon_tilemap, pos)

        else:
            raise Exception("Wall was not correctly processed: %s" % pos)
        return coord

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap,
                         position: Pos,
                         palette_database: PaletteDatabase) -> engine.Surface:
        coord = self._determine_sprite_coord(dungeon_tilemap,  position)
        return get_image16(self.tileset_image, coord)

def get_palette(palette: str) -> PaletteDatabase:
    palette_dir = 'app/dungeon_maker/palettes/'
    if os.path.isdir(palette_dir + palette):
        palette_dir = palette_dir + palette
    else:
        palette_dir = palette_dir + "dungeon"

    return {
        Terrain.FLOOR_LOWER: FloorPalette(os.path.join(palette_dir, 'floor1.png'), os.path.join(palette_dir, 'floor1_shading.png')),
        Terrain.WALL: WallPalette(os.path.join(palette_dir, 'wall.png')),
    }
