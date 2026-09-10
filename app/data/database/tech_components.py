from __future__ import annotations

import enum
from enum import Enum
from typing import Any, List, Optional, Tuple

from app.data.database.components import Component, ComponentType, get_objs_using


class GrantTarget(enum.Enum):
    """Who a GrantSkillEffect / UpgradeItemsEffect materializes onto."""
    TEAM_UNITS     = 'team_units'       # every unit on the tech's team
    TEAM_CITIES    = 'team_cities'      # every city the team owns
    UNITS_WITH_TAG = 'units_with_tag'   # team units whose class carries grant_target_arg
    SELF_TEAM      = 'self_team'        # the team object itself


class Combine(enum.Enum):
    """How multiple unlocked techs writing the same flag key combine."""
    SUM = 'sum'     # additive stacks (exp +10% x3, pop-cap +5 x3)
    MAX = 'max'     # tiered replace (weapon tier 1->2->3)
    SET = 'set'     # accumulate a set (draftable classes, buildable buildings)
    OR  = 'or'      # boolean any (a plain on/off flag)


class TechTags(Enum):
    ECONOMY = 'economy'
    MILITARY = 'military'
    UNLOCK = 'unlock'
    EXPLORATION = 'exploration'
    ADVANCED = 'advanced'

    CUSTOM = 'custom'
    HIDDEN = 'hidden'
    DEPRECATED = 'deprecated'


class TechComponent(Component):
    """A single effect of a tech.

    Unlike item/skill/building components, tech components are never hook-dispatched --
    there is no generated tech_system.py. They are read declaratively by tech_funcs and
    action.UnlockTech, so this base carries data rather than behavior.

    Most components are *flags*: a key/value the engine reads at one call site via
    game.get_tech_value(team, key). Such a component declares `flag_key` and `combine` as
    class attributes, which is the whole point of modelling effects this way -- the engine
    read site dictates the combine policy, so a designer cannot pick a wrong one. A
    component whose key depends on its own value (upkeep_cost_<tag>) overrides `flags()`.

    Components that materialize something at unlock instead (GrantSkillEffect,
    UpgradeItemsEffect) leave `flag_key` None and are matched by nid in action.UnlockTech.
    """
    flag_key: Optional[str] = None
    combine: Combine = Combine.OR

    def flags(self) -> List[Tuple[str, Any, Combine]]:
        """The (key, value, combine) triples this component contributes to the team's
        flag cache. Empty for materialize-at-unlock components."""
        if self.flag_key is None:
            return []
        return [(self.flag_key, self.value, self.combine)]


def get_techs_using(expose: ComponentType, value, db) -> list:
    return get_objs_using(db.techs.values(), expose, value)
