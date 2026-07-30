from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, List, Union

from app.data.category import CategorizedCatalog
from app.utilities import str_utils
from app.utilities.data import Prefab
from app.utilities.typing import NID


class GrantTarget(enum.Enum):
    """Who a GrantSkill effect materializes its skill onto. Only meaningful for GrantSkill."""
    TEAM_UNITS     = 'team_units'       # every unit on the tech's team
    TEAM_CITIES    = 'team_cities'      # every city the team owns
    UNITS_WITH_TAG = 'units_with_tag'   # team units whose class carries collection_arg
    SELF_TEAM      = 'self_team'        # the team object itself


class Combine(enum.Enum):
    """How multiple unlocked techs writing the same TechFlag key combine."""
    SUM = 'sum'     # additive stacks (exp +10% x3, pop-cap +5 x3)
    MAX = 'max'     # tiered replace (weapon tier 1->2->3)
    SET = 'set'     # accumulate a set (draftable classes, buildable buildings)
    OR  = 'or'      # boolean any (a plain on/off flag)


@dataclass
class TechFlag:
    """A named key/value the engine reads at a single call site (O(1) lookup)."""
    key: NID = ''
    value: Any = True
    combine: Combine = Combine.OR
    kind: str = 'flag'

    def save(self) -> dict:
        return {'kind': 'flag',
                'key': self.key,
                'value': self.value,
                'combine': self.combine.value,
                }

    @classmethod
    def restore(cls, dat: dict) -> TechFlag:
        return cls(key=dat['key'],
                   value=dat['value'],
                   combine=Combine(dat.get('combine', 'or')))


@dataclass
class GrantSkill:
    """Materialize an existing skill onto a collection of units at unlock."""
    skill_nid: NID = ''
    grant_target: GrantTarget = GrantTarget.TEAM_UNITS
    grant_target_arg: str = ''    # e.g. tag name for UNITS_WITH_TAG
    kind: str = 'grant_skill'

    def save(self) -> dict:
        return {'kind': 'grant_skill',
                'skill_nid': self.skill_nid,
                'grant_target': self.grant_target.value,
                'grant_target_arg': self.grant_target_arg,
                }

    @classmethod
    def restore(cls, dat: dict) -> GrantSkill:
        return cls(skill_nid=dat['skill_nid'],
                   grant_target=GrantTarget(dat.get('grant_target', 'team_units')),
                   grant_target_arg=dat.get('grant_target_arg', ''))


@dataclass
class UpgradeItems:
    """Materialize effect: on unlock, physically upgrade every item in the target units'
    inventories to its `UpgradesTo` chain endpoint for the team's current `weapon_tier`
    (see action.UnlockTech / item_funcs.resolve_upgrade_nid). Pair with a
    `TechFlag('weapon_tier', N, combine=max)` on the same tech to raise the tier first."""
    grant_target: GrantTarget = GrantTarget.TEAM_UNITS
    grant_target_arg: str = ''
    kind: str = 'upgrade_items'

    def save(self) -> dict:
        return {'kind': 'upgrade_items',
                'grant_target': self.grant_target.value,
                'grant_target_arg': self.grant_target_arg,
                }

    @classmethod
    def restore(cls, dat: dict) -> UpgradeItems:
        return cls(grant_target=GrantTarget(dat.get('grant_target', 'team_units')),
                   grant_target_arg=dat.get('grant_target_arg', ''))


TechEffect = Union[TechFlag, GrantSkill, UpgradeItems]   # tagged by .kind on (de)serialize


def restore_effect(dat: dict) -> TechEffect:
    if dat['kind'] == 'grant_skill':
        return GrantSkill.restore(dat)
    if dat['kind'] == 'upgrade_items':
        return UpgradeItems.restore(dat)
    return TechFlag.restore(dat)


class TechPrefab(Prefab):
    nid: NID
    name: str
    desc: str
    icon_nid: NID
    icon_index: tuple
    renown_cost: int
    requires: List[NID]         # prerequisite tech nids (ALL)
    conditions: List[str]       # optional extra eval predicates (ALL)
    effects: List[TechEffect]

    def __init__(self, nid, name='', desc='', icon_nid=None, icon_index=(0, 0),
                 renown_cost=0, requires=None, conditions=None, effects=None):
        self.nid = nid
        self.name = name
        self.desc = desc
        self.icon_nid = icon_nid
        self.icon_index = icon_index
        self.renown_cost = renown_cost
        self.requires = requires or []
        self.conditions = conditions or []
        self.effects = effects or []

    def save(self):
        return {'nid': self.nid,
                'name': self.name,
                'desc': self.desc,
                'icon_nid': self.icon_nid,
                'icon_index': self.icon_index,
                'renown_cost': self.renown_cost,
                'requires': self.requires,
                'conditions': self.conditions,
                'effects': [e.save() for e in self.effects],
                }

    @classmethod
    def restore(cls, dat):
        icon_index = dat.get('icon_index', (0, 0))
        if icon_index is not None:
            icon_index = tuple(icon_index)   # JSON has no tuples
        effects = [restore_effect(e) for e in dat.get('effects', [])]
        return cls(dat['nid'], dat.get('name', ''), dat.get('desc', ''),
                   dat.get('icon_nid'), icon_index,
                   dat.get('renown_cost', 0), dat.get('requires', []),
                   dat.get('conditions', []), effects)


class TechCatalog(CategorizedCatalog[TechPrefab]):
    datatype = TechPrefab

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Tech", nids)
        new_tech = TechPrefab(nid, name)
        self.append(new_tech)
        return new_tech
