from __future__ import annotations

from typing import List

from app.data.database.database import DB
from app.data.database.teams import Team
from app.utilities.typing import NID
from app.utilities.data import Prefab

class TeamObject(Prefab):
    def __init__(self, nid: NID = None, map_sprite_palette: NID = None, 
                 combat_variant_palette: str = None, combat_color: str = None,
                 name: str = "", gold: int = 0, research: List[str] = None):
        self.nid = nid
        self.map_sprite_palette = map_sprite_palette            # Used for map sprites
        self.combat_variant_palette = combat_variant_palette    # Used for battle animations
        self.combat_color = combat_color                        # Used for misc. ui (rescue icons, combat displays, etc.)

        self.name: str = name
        self.gold: int = gold
        self.research: List[str] = research or []

    def save(self):
        return {'nid': self.nid,
                'map_sprite_palette': self.map_sprite_palette,
                'combat_variant_palette': self.combat_variant_palette,
                'combat_color': self.combat_color,
                'name': self.name,
                'gold': self.gold,
                'research': self.research,
                }

    @classmethod
    def restore(cls, s_dict):
        team = cls(s_dict['nid'], s_dict.get('map_sprite_palette'), 
                   s_dict.get('combat_variant_palette'), s_dict.get('combat_color', 'red'),
                   s_dict.get('name'), "", s_dict.get('gold', 0), s_dict.get('research', []))
        return team

    @classmethod
    def from_prefab(cls, prefab: Team) -> TeamObject:
        team = cls(prefab.nid, prefab.map_sprite_palette, 
                   prefab.combat_variant_palette, prefab.combat_color,
                   prefab.name)
        return team

    def change_palettes(self, map_sprite_palette=None, combat_variant_palette=None, combat_color = None):
        if map_sprite_palette:
            self.map_sprite_palette = map_sprite_palette
        if combat_variant_palette:
            self.combat_variant_palette = combat_variant_palette
        if combat_color:
            self.combat_color = combat_color

    # check if combat_color has been changed
    # to switch to using new colored sprites
    def combat_color_diverged(self) -> bool:
        return DB.teams.get(self.nid).combat_color != self.combat_color
