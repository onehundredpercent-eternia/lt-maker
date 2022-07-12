from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.terrain import Terrain
from app.map_maker.wang_terrain import WangEdge2Terrain16
from app.map_maker.utilities import random_choice

class FloorTerrain(Terrain):
    terrain_like = ()

    def set_tileset(self):
        super().set_tileset()
        self.limits = {k: self._find_limit(k) for k in range(6)}
        print(self.nid, self.limits)

    def _find_limit(self, idx: int) -> int:
        bg_color = qRgb(0, 0, 0)
        img = self.tileset_pixmap.toImage()
        x = idx * TILEWIDTH
        for y in range(0, img.height(), TILEHEIGHT):
            current_color = img.pixel(x, y)
            if current_color == bg_color:
                return y // TILEHEIGHT
        return (img.height() // TILEHEIGHT)

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
    terrain_like = ('Wall',)
    
    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        # Edge is true when we have an adjacent walllike
        north_edge = bool(north in self.terrain_like)
        south_edge = bool(south in self.terrain_like)
        east_edge = bool(east in self.terrain_like)
        west_edge = bool(west in self.terrain_like)
        index = 1 * north_edge + 2 * east_edge + 4 * south_edge + 8 * west_edge
        return index

class PillarTerrain(Terrain):
    pass
