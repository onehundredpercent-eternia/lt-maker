from typing import Dict, Set

from app.constants import TILEWIDTH, TILEHEIGHT, WINWIDTH, WINHEIGHT
from app.utilities.typing import Pos, NID
from app.dungeon_maker.terrain_generation import generate_terrain, Terrain, DungeonTileMap
from app.dungeon_maker import themes
from app.dungeon_maker.palette import Palette
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
        Terrain.WATER: 'Water',
        Terrain.STAIRS_UP: 'Stairs',
        Terrain.STAIRS_RIGHT: 'Stairs',
        Terrain.STAIRS_DOWN: 'Stairs',
        Terrain.STAIRS_LEFT: 'Stairs',
        Terrain.PILLAR: 'Pillar',
        Terrain.SPARSE_FOREST: 'Forest',
        Terrain.GRASS: 'Plain',
        Terrain.RUINS_LOWER: 'Floor',
        Terrain.RUINS_UPPER: 'Floor',
        Terrain.CHECKERBOARD_LOWER: 'Floor',
        Terrain.CHECKERBOARD_UPPER: 'Floor',
        Terrain.WATERBRIDGE: 'Floor',
        Terrain.START: 'Stairs',
        Terrain.END: 'Stairs'
    }[terrain]

def generate_map(theme: str = 'default', 
                 palette_name: str = 'dungeon', 
                 seed: int = -1,
                 save_screenshot: bool = False) -> TileMapObject:
    dungeon_tilemap = generate_terrain(theme, seed)
    size = dungeon_tilemap.width, dungeon_tilemap.height

    # Swap Terrains for the palette terrains if necessary
    palette = Palette.from_json(f'app/dungeon_maker/palettes/{palette_name}/metadata.json')
    if palette.floor1 == "grass":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_LOWER, Terrain.GRASS)
    if palette.floor2 == "grass":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_UPPER, Terrain.GRASS)
    if palette.floor1 == "ruins":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_LOWER, Terrain.RUINS_LOWER)
    if palette.floor2 == "ruins":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_UPPER, Terrain.RUINS_UPPER)
    if palette.floor1 == "checkerboard":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_LOWER, Terrain.CHECKERBOARD_LOWER)
    if palette.floor2 == "checkerboard":
        dungeon_tilemap.swap_terrain(Terrain.FLOOR_UPPER, Terrain.CHECKERBOARD_UPPER)

    renderers = get_renderers(palette_name)
    surf: engine.Surface = build_surface(dungeon_tilemap, renderers)
    theme_obj: themes.Theme = themes.themes[theme]

    # Now we have the surface to use as a real tilemap
    scratch_data = {
        'theme': theme_obj,
        'palette_name': palette_name,
        'size': size,
        'seed': seed,
    }

    true_terrain_grid = \
        {pos: get_terrain_nid_from_dungeon_terrain(terrain) for pos, terrain in dungeon_tilemap.terrain_grid.items()}
    tilemap = TileMapObject.build_from_scratch("sample", size, true_terrain_grid, surf, scratch_data)
    if save_screenshot:
        tilemap.save_screenshot(f'LT-{theme}-{palette_name}-{seed}.png')
    return tilemap, dungeon_tilemap

# python -m app.dungeon_maker.tilemap_generation
# Puts the screenshot at the bottom of the screenshot directory
if __name__ == '__main__':
    engine.init()
    engine.build_display((WINWIDTH, WINHEIGHT))
    for i in range(1):
        generate_map('castle', 'green_castle', seed=i)
    print("Done!")
