from __future__ import annotations

from functools import lru_cache
from typing import Callable

from app.data.database import DB, Database
from app.engine import engine, icons
from app.engine.game_state import GameState
from app.engine.objects.unit import UnitObject
from app.resources.resources import RESOURCES, Resources
from app.utilities.typing import NID


def _resolve_to_nid(obj_or_nid) -> NID:
    try:
        return obj_or_nid.uid
    except:
        try:
            return obj_or_nid.nid
        except:
            return obj_or_nid

class SurfComponent():
    """
    General component, holds references
    """
    def __init__(self, create_surface=engine.create_surface, db: Database=DB, resources: Resources=RESOURCES, _game: GameState=None, **kwargs):
        self.create_surface: Callable = create_surface
        self._db = db
        self._resources = resources
        self._game = _game

class ChibiPortrait(SurfComponent):
    """
    Component prefab for drawing chibi portraits
    """
    def __init__(self, unit: UnitObject | NID=None, create_surface=engine.create_surface, db=DB, resources=RESOURCES):
        super().__init__(create_surface, db, resources)
        self.unit_nid: NID = _resolve_to_nid(unit)

    @lru_cache(1)
    def get_cached_surf(self, unit_nid: NID):
        chibi_dimensions = (32, 32)
        surf = self.create_surface(chibi_dimensions, transparent=True)

        if self._game and unit_nid in self._game.unit_registry:
            unit = self._game.unit_registry.get(unit_nid)
            if unit.generic:
                icons.draw_faction(surf, self._db.factions.get(unit.faction), (0, 0))
                return surf
            else:
                portrait_nid = self._game.unit_registry.get(unit_nid)
        else:
            portrait_nid = self._db.units.get(unit_nid).portrait_nid
        icons.draw_chibi(surf, portrait_nid, (0, 0))
        return surf

    def to_surf(self) -> engine.Surface:
        return self.get_cached_surf(self.unit_nid)
