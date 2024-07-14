from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap, Terrain
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.utilities import random_choice

class FloorPainter(Painter):
    """
    Selects the correct painter coordinate for the tile by determining
    what kind of shading should be painted on the floor.
    For instance, if a wall is to the left of this floor tile, the painter
    will select a tile that has shading on the left to make the shadow appear
    """

    def get_coord(self, position: Pos) -> Pos:
        coord = random_choice([(0, k) for k in range(self.limit[0])], position)
        return coord

    def get_shading_coord(self, dungeon_tilemap: DungeonTileMap, pos: Pos) -> Pos:
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
        #         and self._is_column_bottom(tilemap, (pos[0] - 1, pos[1]), painter_database):
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
