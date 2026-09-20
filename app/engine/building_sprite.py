from typing import Optional

from app.constants import COLORKEY
from app.data.resources.building_palettes import get_conversion_dict
from app.data.resources.resources import RESOURCES
from app.engine import engine, image_mods
from app.engine.game_state import game
from app.utilities.typing import NID


def get_building_sprite(building) -> Optional[engine.Surface]:
    """The building's map sprite, recolored for the map's style and its owning team.

    Buildings neither move nor animate, so the result is cached for the life of
    the level under (sprite nid, style nid, team nid).
    """
    res = RESOURCES.building_sprites.get(building.map_sprite_nid)
    if not res:
        return None

    style_nid: NID = game.tilemap.building_style_nid if game.tilemap else None
    # `owner_nid` is the owning *city*; the team colors come from that city's team
    city = game.get_city(building.owner_nid)
    team_nid: NID = city.team if city else None

    key = (res.nid, style_nid, team_nid)
    sprite = game.building_sprite_registry.get(key)
    if sprite:
        return sprite

    if not res.image:
        res.image = engine.image_load(res.full_path)
    sprite = image_mods.color_convert(res.image, get_conversion_dict(style_nid, team_nid))
    engine.set_colorkey(sprite, COLORKEY, rleaccel=True)
    game.building_sprite_registry[key] = sprite
    return sprite
