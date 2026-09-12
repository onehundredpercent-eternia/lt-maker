from __future__ import annotations

from typing import List, Optional

import app.engine.tech_component_access as TCA
from app.data.category import CategorizedCatalog
from app.data.database.tech_components import Combine, GrantTarget, TechComponent
from app.utilities import str_utils
from app.utilities.data import Data, Prefab
from app.utilities.typing import NID

# Re-exported so `from app.data.database.techs import Combine, GrantTarget` keeps working;
# both now live with the component base, which is what needs them.
__all__ = ['Combine', 'GrantTarget', 'TechPrefab', 'TechCatalog']


class TechPrefab(Prefab):
    """A tech owns no logic: it is unlock gating (`renown_cost`, `requires`, `conditions`,
    all ALL-tested) plus a list of effects. Effects are TechComponents -- see
    app/engine/tech_components/base_components.py. Unlike items/skills/buildings there is
    no generated tech_system.py; tech components are read declaratively by tech_funcs and
    action.UnlockTech."""

    nid: NID
    name: str
    desc: str
    icon_nid: NID
    icon_index: tuple
    renown_cost: int
    requires: List[NID]         # prerequisite tech nids (ALL)
    conditions: List[str]       # optional extra eval predicates (ALL)
    components: Data[TechComponent]

    def __init__(self, nid, name='', desc='', icon_nid=None, icon_index=(0, 0),
                 renown_cost=0, requires=None, conditions=None, components=None):
        self.nid = nid
        self.name = name
        self.desc = desc
        self.icon_nid = icon_nid
        self.icon_index = icon_index
        self.renown_cost = renown_cost
        self.requires = requires or []
        self.conditions = conditions or []

        self.components = components or Data[TechComponent]()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value

    def add_component(self, component: TechComponent):
        self.components.append(component)
        self.__dict__[component.nid] = component

    def remove_component(self, component: TechComponent):
        self.components.delete(component)
        del self.__dict__[component.nid]

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __getitem__(self, key):
        return self.__dict__.get(key)

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def save(self):
        return {'nid': self.nid,
                'name': self.name,
                'desc': self.desc,
                'icon_nid': self.icon_nid,
                'icon_index': self.icon_index,
                'renown_cost': self.renown_cost,
                'requires': self.requires,
                'conditions': self.conditions,
                'components': [c.save() for c in self.components],
                }

    @classmethod
    def restore(cls, dat):
        icon_index = dat.get('icon_index', (0, 0))
        if icon_index is not None:
            icon_index = tuple(icon_index)   # JSON has no tuples
        if 'components' in dat:
            components = Data([TCA.restore_component(val) for val in dat['components']])
            components = Data([c for c in components if c])
        else:
            components = _restore_legacy_effects(dat.get('effects', []))
        return cls(dat['nid'], dat.get('name', ''), dat.get('desc', ''),
                   dat.get('icon_nid'), icon_index,
                   dat.get('renown_cost', 0), dat.get('requires', []),
                   dat.get('conditions', []), components)


# Techs originally stored `effects`: a list of tagged-union dicts
# ({kind: flag|grant_skill|upgrade_items, ...}) with a free-text flag `key` and a
# designer-chosen `combine`. Effects are now TechComponents, which carry the key and the
# combine policy as class attributes so neither can be authored wrong. A project written
# before that change still has `effects` on disk; map it forward on load and it rewrites
# in the new shape on the next save.
_LEGACY_FLAG_COMPONENTS = {
    'exp_mult_bonus': 'exp_mult_bonus',
    'city_pop_cap_bonus': 'city_pop_bonus',
    'road_move_bonus': 'road_move_bonus',
    'overworld_sight_bonus': 'overworld_sight_bonus',
    'weapon_tier': 'weapon_tier',
}
_LEGACY_SET_COMPONENTS = {
    'draft_unlock': 'draft_unlock',
    'build_unlock': 'build_unlock',
}
_LEGACY_RESOURCE_SUFFIX = '_resource_bonus'
_LEGACY_UPKEEP_PREFIX = 'upkeep_cost_'


def _restore_legacy_effects(effects: List[dict]) -> Data[TechComponent]:
    components: List[TechComponent] = []

    def _add(nid: NID, value):
        component = TCA.restore_component((nid, value))
        if component:
            components.append(component)

    for effect in effects:
        kind = effect.get('kind', 'flag')
        if kind == 'grant_skill':
            _add('grant_skill', {'skills': [effect['skill_nid']],
                                 'grant_target': effect.get('grant_target', 'team_units'),
                                 'grant_target_arg': effect.get('grant_target_arg') or None})
        elif kind == 'upgrade_items':
            _add('upgrade_items', {'grant_target': effect.get('grant_target', 'team_units'),
                                   'grant_target_arg': effect.get('grant_target_arg') or None})
        else:
            key, value = effect.get('key', ''), effect.get('value')
            if key in _LEGACY_FLAG_COMPONENTS:
                _add(_LEGACY_FLAG_COMPONENTS[key], value)
            elif key in _LEGACY_SET_COMPONENTS:
                # A set flag wrote one nid per effect; the component holds a list, and
                # repeated keys on one tech merge into that single component.
                existing = next((c for c in components if c.nid == _LEGACY_SET_COMPONENTS[key]), None)
                if existing:
                    existing.value.append(value)
                else:
                    _add(_LEGACY_SET_COMPONENTS[key], [value])
            elif key.endswith(_LEGACY_RESOURCE_SUFFIX):
                tag = key[:-len(_LEGACY_RESOURCE_SUFFIX)].capitalize()
                _add('resource_bonus', {'building_tag': tag, 'amount': value})
            elif key.startswith(_LEGACY_UPKEEP_PREFIX):
                _add('upkeep_cost_reduction', {'unit_tag': key[len(_LEGACY_UPKEEP_PREFIX):],
                                               'amount': value})
            elif key:
                _add('custom_flag', {'key': key, 'value': str(value),
                                     'combine': effect.get('combine', 'or')})
    return Data(components)


class TechCatalog(CategorizedCatalog[TechPrefab]):
    datatype = TechPrefab

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Tech", nids)
        new_tech = TechPrefab(nid, name)
        self.append(new_tech)
        return new_tech
