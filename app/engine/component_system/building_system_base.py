from __future__ import annotations

from typing import TYPE_CHECKING

from app.engine.utils.ltcache import ltcached

if TYPE_CHECKING:
    from app.engine.objects.city import CityObject
    from app.engine.objects.building import BuildingObject

class Defaults():
    pass

@ltcached
def condition(building: BuildingObject, city: CityObject) -> bool:
    for component in building.components:
        if component.defines('condition'):
            if not component.condition(city):
                return False
    return True

def init(building):
    """
    Initializes any data on the parent building if necessary
    """
    for component in building.components:
        if component.defines('init'):
            component.init(building)

def after_add(city, building):
    for component in building.components:
        if component.defines('after_add'):
            component.after_add(city, building)

def after_remove(city, building):
    for component in building.components:
        if component.defines('after_remove'):
            component.after_remove(city, building)
