from __future__ import annotations
from enum import Enum
from app.data.database.components import Component, ComponentType, get_objs_using

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.engine.objects.building import BuildingObject

# 4X: a building carrying one of these tags gains `{tag}_resource_bonus` (a tech flag,
# combine=sum) to the mapped resource in its per-turn output. Lives here rather than in
# either engine package so the building side (ResourcePerTurn.get_output, which pays out
# the bonus) and the tech side (ResourceBonus, which offers the tags) can never drift.
RESOURCE_BONUS_TAGS = {'Farm': 'food', 'Mine': 'production', 'Artisan': 'gold'}


class BuildingTags(Enum):
    BASE = 'base'
    RESOURCE = 'resource'
    UNIT = 'unit'

    CUSTOM = 'custom'
    HIDDEN = 'hidden'
    DEPRECATED = 'deprecated'

class BuildingComponent(Component):
    building: Optional[BuildingObject] = None
    ignore_conditional: bool = False

def get_buildings_using(expose: ComponentType, value, db) -> list:
    return get_objs_using(db.buildings.values(), expose, value)
