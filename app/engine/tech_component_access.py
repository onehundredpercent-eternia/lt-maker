from functools import lru_cache

from app.data.database.components import ComponentType
from app.data.database.tech_components import TechComponent, TechTags
from app.utilities.class_utils import recursive_subclasses
from app.utilities.data import Data


@lru_cache(1)
def get_cached_tech_components(proj_dir: str):
    from app.data.resources.resources import RESOURCES
    from app.engine import tech_components
    if RESOURCES.has_loaded_custom_components():
        # Necessary for get_tech_components to find the tech component subclasses
        # defined there
        import custom_components

    subclasses = recursive_subclasses(TechComponent)
    # Sort by tag
    subclasses = sorted(subclasses, key=lambda x: list(TechTags).index(x.tag) if x.tag in list(TechTags) else 100)
    return Data(subclasses)

def get_tech_components():
    from app.data.database.database import DB
    return get_cached_tech_components(DB.current_proj_dir)

def get_tech_tags():
    return list(TechTags)

def get_component(nid):
    _tech_components = get_tech_components()
    base_class = _tech_components.get(nid)
    if base_class:
        return base_class(base_class.value)
    return None

def restore_component(dat):
    nid, value = dat
    _tech_components = get_tech_components()
    base_class = _tech_components.get(nid)
    if not base_class:
        return None
    if isinstance(base_class.expose, tuple) and base_class.expose[0] == ComponentType.List:
        # Copy so the restored component doesn't alias the saved list
        return base_class(value.copy())
    if isinstance(base_class.expose, tuple) and \
            base_class.expose[0] in (ComponentType.Dict, ComponentType.FloatDict, ComponentType.StringDict):
        return base_class([v.copy() for v in value])
    # Everything else -- plain scalars, MultipleChoice, and NewMultipleOptions (whose
    # __init__ builds a fresh dict of defaults and updates it) -- restores directly.
    return base_class(value)

templates = {}

def get_templates():
    return templates.items()
