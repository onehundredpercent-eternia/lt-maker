from __future__ import annotations
from enum import Enum
from app.data.database.components import Component, ComponentType, get_objs_using

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.engine.objects.building import BuildingObject

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
