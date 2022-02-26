from PyQt5.QtGui import QPixmap, QPainter

from app.constants import TILEWIDTH, TILEHEIGHT
from app.map_maker.wang_terrain import WangCorner2Terrain
from app.map_maker.utilities import flood_fill
from app.map_maker.value_noise import get_noise_map

class GrassTerrain(WangCorner2Terrain):
    terrain_like = ('Plains')
    cliff_data = [(13, 9), (13, 10), (14, 9), (14, 10)]  # Topright, Bottomright, Bottomleft, Topleft
    corner_chance = 0.6
    edge_chance = 0.4
    light_grass_chance = 0.4
    min_group_size = 6
    vertices: dict = {}
    potential_light_positions: set = set()

    @property
    def check_flood_fill(self):
        return True

    def get_display_pixmap(self):
        if not self.display_pixmap:
            main_pix = QPixmap(16, 16)
            painter = QPainter()
            painter.begin(main_pix)
            painter.drawPixmap(0, 0, self.tileset_pixmap.copy(0, 0, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(0, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 1 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, 0, self.tileset_pixmap.copy(0, 2 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.drawPixmap(TILEWIDTH//2, TILEHEIGHT//2, self.tileset_pixmap.copy(0, 3 * TILEHEIGHT//2, TILEWIDTH//2, TILEHEIGHT//2))
            painter.end()
            self.display_pixmap = main_pix
        return self.display_pixmap

    def single_process(self, tilemap):
        positions: set = tilemap.get_all_terrain(self.nid)
        self.vertices.clear()
        noise_map = get_noise_map(tilemap.width, tilemap.height)
        self.potential_light_positions = {pos for pos in positions if noise_map.get(*pos) > (1 - self.light_grass_chance)}

        # Remove any positions that are adjacent to 2 or more non-grass tiles
        for pos in list(self.potential_light_positions):
            north, east, south, west = tilemap.get_cardinal_terrain(pos)
            north_is_grass = bool(not north or north in self.terrain_like)
            east_is_grass = bool(not east or east in self.terrain_like)
            south_is_grass = bool(not south or south in self.terrain_like)
            west_is_grass = bool(not west or west in self.terrain_like)
            if sum((north_is_grass, east_is_grass, west_is_grass, south_is_grass)) < 3:
                self.potential_light_positions.discard(pos)

        # Remove small groups
        positions = set(self.potential_light_positions)
        counter: int = 0
        groupings: list = []
        while positions and counter < int(1e6):
            pos = positions.pop()
            near_positions: set = flood_fill(tilemap, pos, match_set=self.potential_light_positions)
            positions -= near_positions
            groupings.append(near_positions)
            counter += 1
        for group in groupings:
            if len(group) < self.min_group_size:
                self.potential_light_positions -= group

        for pos in self.potential_light_positions:
            self.determine_vertex(tilemap, pos)

    def get_edges(self, tilemap, pos):
        north_pos = (pos[0], pos[1] - 1)
        south_pos = (pos[0], pos[1] + 1)
        east_pos = (pos[0] + 1, pos[1])
        west_pos = (pos[0] - 1, pos[1])
        northeast_pos = (pos[0] + 1, pos[1] - 1)
        northwest_pos = (pos[0] - 1, pos[1] - 1)
        southeast_pos = (pos[0] + 1, pos[1] + 1)
        southwest_pos = (pos[0] - 1, pos[1] + 1)
        north_edge = not tilemap.get_terrain(north_pos) or north_pos in self.potential_light_positions
        south_edge = not tilemap.get_terrain(south_pos) or south_pos in self.potential_light_positions
        east_edge = not tilemap.get_terrain(east_pos) or east_pos in self.potential_light_positions
        west_edge = not tilemap.get_terrain(west_pos) or west_pos in self.potential_light_positions
        northeast_edge = not tilemap.get_terrain(northeast_pos) or northeast_pos in self.potential_light_positions
        northwest_edge = not tilemap.get_terrain(northwest_pos) or northwest_pos in self.potential_light_positions
        southeast_edge = not tilemap.get_terrain(southeast_pos) or southeast_pos in self.potential_light_positions
        southwest_edge = not tilemap.get_terrain(southwest_pos) or southwest_pos in self.potential_light_positions
        return north_edge, south_edge, east_edge, west_edge, northeast_edge, northwest_edge, southeast_edge, southwest_edge

    def _determine_index(self, tilemap, pos: tuple) -> tuple:
        center, left, right, top, bottom, topleft, topright, bottomleft, bottomright = self._pos_to_vertices(pos)
        center_edge = True
        left_edge = bool(self.vertices[left][0])
        right_edge = bool(self.vertices[right][0])
        top_edge = bool(self.vertices[top][0])
        bottom_edge = bool(self.vertices[bottom][0])
        topleft_edge = bool(self.vertices[topleft][0])
        topright_edge = bool(self.vertices[topright][0])
        bottomleft_edge = bool(self.vertices[bottomleft][0])
        bottomright_edge = bool(self.vertices[bottomright][0])

        # Randomly determine some to remove
        if self.vertices[center][0] == 3 and self.vertices[center][1] < self.edge_chance:
            center_edge = False
        if self.vertices[center][0] == 2 and self.vertices[center][1] < self.corner_chance:
            center_edge = False
        if self.vertices[left][0] in (2, 3) and self.vertices[left][1] < self.edge_chance:
            left_edge = False
        if self.vertices[right][0] in (2, 3) and self.vertices[right][1] < self.edge_chance:
            right_edge = False
        if self.vertices[top][0] in (2, 3) and self.vertices[top][1] < self.edge_chance:
            top_edge = False
        if self.vertices[bottom][0] in (2, 3) and self.vertices[bottom][1] < self.edge_chance:
            bottom_edge = False

        index1 = 1 * top_edge + \
            2 * center_edge + \
            4 * left_edge + \
            8 * topleft_edge
        index2 = 1 * topright_edge + \
            2 * right_edge + \
            4 * center_edge + \
            8 * top_edge
        index3 = 1 * right_edge + \
            2 * bottomright_edge + \
            4 * bottom_edge + \
            8 * center_edge
        index4 = 1 * center_edge + \
            2 * bottom_edge + \
            4 * bottomleft_edge + \
            8 * left_edge
        return index1, index2, index3, index4
            
    def determine_sprite_coords(self, tilemap, pos: tuple) -> tuple:
        if pos in self.potential_light_positions:
            index1, index2, index3, index4 = self._determine_index(tilemap, pos)
            new_coords1 = [(index1, k) for k in range(self.limits[index1])]
            new_coords2 = [(index2, k) for k in range(self.limits[index2])]
            new_coords3 = [(index3, k) for k in range(self.limits[index3])]
            new_coords4 = [(index4, k) for k in range(self.limits[index4])]
        else:
            new_coords1 = [(0, k) for k in range(self.limits[0])]
            new_coords2 = [(0, k) for k in range(self.limits[0])]
            new_coords3 = [(0, k) for k in range(self.limits[0])]
            new_coords4 = [(0, k) for k in range(self.limits[0])]

        # Handle cliffs
        north, east, south, west = tilemap.get_cardinal_terrain(pos)
        northeast, southeast, southwest, northwest = tilemap.get_diagonal_terrain(pos)
        if north and north == 'Cliff' and east and east == 'Cliff' and not (northeast and northeast == 'Cliff'):
            new_coords2 = [self.cliff_data[1]]
        elif north and north == 'Cliff' and west and west == 'Cliff' and not (northwest and northwest == 'Cliff'):
            new_coords1 = [self.cliff_data[3]]
        elif south and south == 'Cliff' and east and east == 'Cliff' and not (southeast and southeast == 'Cliff'):
            new_coords3 = [self.cliff_data[0]]
        elif south and south == 'Cliff' and west and west == 'Cliff' and not (southwest and southwest == 'Cliff'):
            new_coords4 = [self.cliff_data[2]]
        # Handle seacliffs
        elif north and north == 'Sea' and east and east == 'Sea' and northeast and northeast == 'Sea':
            new_coords2 = [self.cliff_data[1]]
        elif north and north == 'Sea' and west and west == 'Sea' and northwest and northwest == 'Sea':
            new_coords1 = [self.cliff_data[3]]
        elif south and south == 'Sea' and east and east == 'Sea' and southeast and southeast == 'Sea':
            new_coords3 = [self.cliff_data[0]]
        elif south and south == 'Sea' and west and west == 'Sea' and southwest and southwest == 'Sea':
            new_coords4 = [self.cliff_data[2]]

        return new_coords1, new_coords2, new_coords3, new_coords4
