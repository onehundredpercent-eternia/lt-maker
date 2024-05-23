from typing import Dict, Set

from app.constants import TILEWIDTH, TILEHEIGHT
from app.utilities.typing import Pos
from app.dungeon_maker.terrain_generation import generate_terrain, Terrain, DungeonTileMap
from app.dungeon_maker.palette_maker import get_palette, PaletteDatabase

from app.engine.objects.tilemap import TileMapObject
from app.engine import engine
from app.engine.game_state import game

def build_surface(dungeon_tilemap: DungeonTileMap, db_palette: PaletteDatabase) -> TileMapObject:
    im_width, im_height = dungeon_tilemap.width * TILEWIDTH, dungeon_tilemap.height * TILEHEIGHT

    surf = engine.create_surface((im_width, im_height))
    engine.fill(surf, (0, 0, 0))

    # Handle the single process
    processed_terrains: Set[Terrain] = set()
    for position, terrain_type in dungeon_tilemap.terrain_grid.items():
        if terrain_type not in processed_terrains:
            palette = db_palette.get(terrain_type)
            palette.single_process(dungeon_tilemap)
            processed_terrains.add(terrain_type)

    sprite_grid: Dict[Pos, engine.Surface] = {}
    # Determine what sprite to use
    for position, terrain_type in dungeon_tilemap.terrain_grid.items():
        palette = db_palette.get(terrain_type)
        sprite = palette.determine_sprite(dungeon_tilemap, position, db_palette)
        sprite_grid[position] = sprite

    # Draw the sprite grid to the surface
    for pos, pix in sprite_grid.items():
        surf.blit(pix, (pos[0] * TILEWIDTH, pos[1] * TILEHEIGHT))

def generate_map(theme: str = 'default', palette_name: str = 'dungeon', size: Pos = (30, 18), seed: int = -1):
    dungeon_tilemap = generate_terrain(theme, size, seed)
    db_palette = get_palette(palette_name)
    surf = build_surface(dungeon_tilemap, db_palette)

    # Now we have the surface to use as a real tilemap
    scratch_data = {
        'theme': theme,
        'palette_name': palette_name,
        'size': size,
        'seed': seed,
    }
    tilemap = TileMapObject.build_from_scratch(dungeon_tilemap, surf, scratch_data)

    game.build_level_from_scratch(tilemap)
    game.tilemap.save_screenshot()

if __name__ == '__main__':
    generate_map(seed=-1)
