import os
from typing import Dict
from app.utilities.typing import Pos

from app.dungeon_maker.terrain_generation import DungeonTileMap
from app.dungeon_maker.painter_utils import Painter
from app.dungeon_maker.pygame_renderers.renderer_utils import find_limit8, find_limit16, get_image8, get_image16
from app.engine import engine

class SimpleShadingRenderer:
    def __init__(self, painter: Painter, image_fn: str):
        self.painter = painter
        self.image = engine.image_load(image_fn)
        limit: int = find_limit16(self.image, 0)
        self.painter.set_limit({0: limit})

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos) -> engine.Surface:
        coord, shading_coord = self.painter.get_coord(dungeon_tilemap, position)

        base_image = get_image16(self.image, coord)

        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.image, shading_coord)

        if shading_image:
            base_image.blit(shading_image, (0, 0))
        return base_image

class FloorShadingRenderer:
    def __init__(self, painter: Painter, main_image_fn: str, shading_image_fn: str):
        self.painter = painter
        self.main_image = engine.image_load(main_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        limit: int = find_limit16(self.main_image, 0)
        self.painter.set_limit({0: limit})

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap,
                         position: Pos) -> engine.Surface:
        coord = self.painter.get_coord(dungeon_tilemap, position)
        shading_coord = self.painter.get_shading_coord(dungeon_tilemap, position)

        base_image = get_image16(self.main_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.shading_image, shading_coord)

        extra_image = None
        pillar_coord = self.painter.get_pillar_coord(dungeon_tilemap, position)
        if pillar_coord:
            extra_image = get_image16(self.shading_image, pillar_coord)
        elif self.painter.is_column_bottom(dungeon_tilemap, position):
            extra_image = get_image16(self.shading_image, (7, 0))

        if shading_image:
            base_image.blit(shading_image, (0, 0))
        if extra_image:
            base_image.blit(extra_image, (0, 0))

        return base_image

class CheckerboardFloorShadingRenderer:
    def __init__(self, painter: Painter, 
                 main_alpha_image_fn: str, shading_alpha_image_fn: str,
                 main_beta_image_fn: str, shading_beta_image_fn: str):
        self.painter = painter
        self.main_alpha_image = engine.image_load(main_alpha_image_fn)
        self.shading_alpha_image = engine.image_load(shading_alpha_image_fn)
        if not os.path.exists(main_beta_image_fn):
            return
        self.main_beta_image = engine.image_load(main_beta_image_fn)
        self.shading_beta_image = engine.image_load(shading_beta_image_fn)
        alpha_limit: int = find_limit16(self.main_alpha_image, 0)
        beta_limit: int = find_limit16(self.main_beta_image, 0)
        self.painter.set_limit({0: min(alpha_limit, beta_limit)})

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap,
                         position: Pos) -> engine.Surface:
        coord = self.painter.get_coord(dungeon_tilemap, position)
        shading_coord = self.painter.get_shading_coord(dungeon_tilemap, position)

        if (position[0] + position[1]) % 2 == 1:
            main_image = self.main_beta_image
            shadow_image = self.shading_beta_image
        else:
            main_image = self.main_alpha_image
            shadow_image = self.shading_alpha_image

        base_image = get_image16(main_image, coord)
        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(shadow_image, shading_coord)

        extra_image = None
        pillar_coord = self.painter.get_pillar_coord(dungeon_tilemap, position)
        if pillar_coord:
            extra_image = get_image16(shadow_image, pillar_coord)
        elif self.painter.is_column_bottom(dungeon_tilemap, position):
            extra_image = get_image16(shadow_image, (7, 0))

        if shading_image:
            base_image.blit(shading_image, (0, 0))
        if extra_image:
            base_image.blit(extra_image, (0, 0))

        return base_image

class Limit8ShadingRenderer(FloorShadingRenderer):
    def __init__(self, painter: Painter, main_image_fn: str, shading_image_fn: str):
        self.painter = painter
        self.main_image = engine.image_load(main_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        limit: Dict[int, int] = {k: find_limit8(self.main_image, k) for k in range(self.main_image.get_width() // 8)}
        self.painter.set_limit(limit)

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos) -> engine.Surface:
        regular_coords, shading_coord = self.painter.get_coord(dungeon_tilemap, position)
        coord1, coord2, coord3, coord4 = regular_coords

        base_image = engine.create_surface((16, 16))
        base_image.blit(get_image8(self.main_image, coord1), (0, 0))
        base_image.blit(get_image8(self.main_image, coord2), (8, 0))
        base_image.blit(get_image8(self.main_image, coord3), (8, 8))
        base_image.blit(get_image8(self.main_image, coord4), (0, 8))

        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.shading_image, shading_coord)

        extra_image = None
        pillar_coord = self.painter.get_pillar_coord(dungeon_tilemap, position)
        if pillar_coord:
            extra_image = get_image16(self.shading_image, pillar_coord)
        elif self.painter.is_column_bottom(dungeon_tilemap, position):
            extra_image = get_image16(self.shading_image, (7, 0))

        if shading_image:
            base_image.blit(shading_image, (0, 0))
        if extra_image:
            base_image.blit(extra_image, (0, 0))

        return base_image

class Limit16ShadingRenderer(FloorShadingRenderer):
    def __init__(self, painter: Painter, main_image_fn: str, shading_image_fn: str):
        self.painter = painter
        self.main_image = engine.image_load(main_image_fn)
        self.shading_image = engine.image_load(shading_image_fn)
        limit: Dict[int, int] = {k: find_limit16(self.main_image, k) for k in range(self.main_image.get_width() // 16)}
        self.painter.set_limit(limit)

    def determine_sprite(self, dungeon_tilemap: DungeonTileMap, 
                         position: Pos) -> engine.Surface:
        coord, shading_coord = self.painter.get_coord(dungeon_tilemap, position)

        base_image = get_image16(self.main_image, coord)

        shading_image = None
        if shading_coord is not None:
            shading_image = get_image16(self.shading_image, shading_coord)

        extra_image = None
        pillar_coord = self.painter.get_pillar_coord(dungeon_tilemap, position)
        if pillar_coord:
            extra_image = get_image16(self.shading_image, pillar_coord)
        elif self.painter.is_column_bottom(dungeon_tilemap, position):
            extra_image = get_image16(self.shading_image, (7, 0))

        if shading_image:
            base_image.blit(shading_image, (0, 0))
        if extra_image:
            base_image.blit(extra_image, (0, 0))

        return base_image
