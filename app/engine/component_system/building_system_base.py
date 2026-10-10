from __future__ import annotations

from typing import TYPE_CHECKING

from app.engine.component_system import utils
from app.engine.utils.ltcache import ltcached

if TYPE_CHECKING:
    from app.engine.objects.city import CityObject
    from app.engine.objects.building import BuildingObject
    from app.engine.objects.unit import UnitObject

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

# Single-candidate-building hooks (the candidate building is not yet in the city, so it is
# passed explicitly and only its own components are consulted; mirrors condition() above).
def available(building, city) -> bool:
    """Whether this building is allowed to be built in this city at all."""
    for component in building.components:
        if component.defines('available'):
            if not component.available(city):
                return False
    return True

def outpost_buildable(building, city) -> bool:
    """Whether this building may be built in a city that is still an outpost."""
    for component in building.components:
        if component.defines('outpost_buildable'):
            if component.outpost_buildable(city):
                return True
    return False

def target_restrict(building, city, position) -> bool:
    """Whether this building may be placed at the given position in this city."""
    for component in building.components:
        if component.defines('target_restrict'):
            if not component.target_restrict(city, position):
                return False
    return True
