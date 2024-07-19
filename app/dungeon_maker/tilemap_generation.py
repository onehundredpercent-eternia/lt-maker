from typing import Dict, Set

from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.utilities.typing import Pos, NID
from app.dungeon_maker.terrain_generation import generate_terrain, Terrain, DungeonTileMap
from app.dungeon_maker.pygame_renderers.renderers import get_renderers, RendererDatabase

from app.engine.objects.tilemap import TileMapObject
from app.engine import engine

def build_surface(dungeon_tilemap: DungeonTileMap, renderers: RendererDatabase) -> TileMapObject:
    im_width, im_height = dungeon_tilemap.width * TILEWIDTH, dungeon_tilemap.height * TILEHEIGHT

    surf = engine.create_surface((im_width, im_height))
    engine.fill(surf, (0, 0, 0))

    # Handle the single process
    processed_terrains: Set[Terrain] = set()
    for position, terrain_type in dungeon_tilemap.terrain_grid.items():
        if terrain_type not in processed_terrains:
            renderer = renderers.get(terrain_type)
            renderer.painter.single_process(dungeon_tilemap)
            processed_terrains.add(terrain_type)

    sprite_grid: Dict[Pos, engine.Surface] = {}
    # Determine what sprite to use
    for position, terrain_type in dungeon_tilemap.terrain_grid.items():
        renderer = renderers.get(terrain_type)
        sprite = renderer.determine_sprite(dungeon_tilemap, position)
        sprite_grid[position] = sprite

    # Draw the sprite grid to the surface
    for pos, pix in sprite_grid.items():
        surf.blit(pix, (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT))

    return surf

def get_terrain_nid_from_dungeon_terrain(terrain: Terrain) -> NID:
    return {
        Terrain.VOID: 'Void',
        Terrain.WALL_TOP: 'Wall',
        Terrain.WALL_BOTTOM: 'Wall',
        Terrain.FLOOR_LOWER: 'Floor',
        Terrain.FLOOR_UPPER: 'Floor',
        Terrain.START: 'Stairs',
        Terrain.END: 'Stairs'
    }[terrain]

def generate_map(theme: str = 'default', palette_name: str = 'dungeon', 
                 size: Pos = (30, 18), seed: int = -1):
    dungeon_tilemap = generate_terrain(theme, size, seed)
    renderers = get_renderers(palette_name)
    surf: engine.Surface = build_surface(dungeon_tilemap, renderers)

    # Now we have the surface to use as a real tilemap
    scratch_data = {
        'theme': theme,
        'palette_name': palette_name,
        'size': size,
        'seed': seed,
    }

    true_terrain_grid = \
        {pos: get_terrain_nid_from_dungeon_terrain(terrain) for pos, terrain in dungeon_tilemap.terrain_grid.items()}
    tilemap = TileMapObject.build_from_scratch("sample", size, true_terrain_grid, surf, scratch_data)
    tilemap.save_screenshot()

# python -m app.dungeon_maker.tilemap_generation
# Puts the screenshot at the bottom of the screenshot directory
if __name__ == '__main__':
    engine.init()
    engine.build_display((WINWIDTH, WINHEIGHT))
    generate_map(seed=-1)
