from PyQt5.QtGui import QPixmap, QPainter, qRgb

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.terrain import Terrain

class WangEdge2Terrain(Terrain):
    terrain_like = ()

    def set_tileset(self):
        super().set_tileset()
        self.limits = {k: self._find_limit(k) for k in range(16)}
        print(self.nid, self.limits)

    def _find_limit(self, idx: int) -> int:
        bg_color = qRgb(0, 0, 0)
        img = self.tileset_pixmap.toImage()
        x = idx * TILEWIDTH//2
        for y in range(0, img.height(), TILEHEIGHT//2):
            current_color = img.pixel(x, y)
            if current_color == bg_color:
                return y // (TILEHEIGHT//2)
        return (img.height() // (TILEHEIGHT//2))

    def get_display_pixmap(self):
        if not self.display_pixmap:
            main_pix = QPixmap(16, 16)
            painter = QPainter()
            painter.begin(main_pix)
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 0 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(TILEWIDTH//2 * 15, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 6 + 1 * north_edge + 8 * west_edge
        index2 = 12 + 1 * north_edge + 2 * east_edge
        index3 = 9 + 4 * south_edge + 2 * east_edge
        index4 = 3 + 4 * south_edge + 8 * west_edge
        return index1, index2, index3, index4

    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        index1, index2, index3, index4 = self._determine_index(tilemap, pos)        
        new_coords1 = [(index1, k) for k in range(self.limits[index1])]
        new_coords2 = [(index2, k) for k in range(self.limits[index2])]
        new_coords3 = [(index3, k) for k in range(self.limits[index3])]
        new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        return new_coords1, new_coords2, new_coords3, new_coords4

class WangCorner2Terrain(WangEdge2Terrain):
    terrain_like = ()

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        north_edge = bool(not north or north in self.terrain_like)
        south_edge = bool(not south or south in self.terrain_like)
        east_edge = bool(not east or east in self.terrain_like)
        west_edge = bool(not west or west in self.terrain_like)
        index1 = 1 * north_edge + \
            2 * True + \
            4 * west_edge + \
            8 * (bool(not northwest or northwest in self.terrain_like) and north_edge and west_edge)
        index2 = 1 * (bool(not northeast or northeast in self.terrain_like) and north_edge and east_edge) + \
            2 * east_edge + \
            4 * True + \
            8 * north_edge
        index3 = 1 * east_edge + \
            2 * (bool(not southeast or southeast in self.terrain_like) and south_edge and east_edge) + \
            4 * south_edge + \
            8 * True
        index4 = 1 * True + \
            2 * south_edge + \
            4 * (bool(not southwest or southwest in self.terrain_like) and south_edge and west_edge) + \
            8 * west_edge
        return index1, index2, index3, index4
