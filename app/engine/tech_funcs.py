"""
Runtime helpers for the renown / tech ("unlock") system.

A team's unlocked techs live in `TeamObject.research` (list of tech nids); its
renown currency lives in `TeamObject.renown`. Techs own no logic — each is a bag
of `TechEffect`s (see `app/data/database/techs.py`). This module interprets the
flag components of a team's unlocked techs into a single precomputed lookup
dict (`TeamObject._tech_flag_cache`), so an engine call site reads a combined flag
value in O(1).

The cache is rebuilt lazily on first read and invalidated (set to None) whenever
the unlocked set changes (the `UnlockTech` action, do/reverse). `grant_skill`
components are handled elsewhere (the unlock action + `get_tech_skills` on unit-add),
not here.
"""

from typing import Any, List, Set, TYPE_CHECKING

from app.data.database.database import DB
from app.data.database.tech_components import Combine, GrantTarget
from app.engine import evaluate, item_funcs
from app.engine.game_state import game
from app.engine.objects.team import TeamObject
from app.utilities.typing import NID

import logging

if TYPE_CHECKING:
    from app.engine.objects.skill import SkillObject
    from app.engine.objects.unit import UnitObject


def _rebuild_flag_cache(team: TeamObject) -> dict:
    """Precompute {key: combined_value} from every flag-bearing component of the team's
    unlocked techs. A component contributes zero or more (key, value, combine) triples;
    the key and the policy are the component's own, not the designer's."""
    cache: dict = {}
    for tech_nid in team.research:
        tech = DB.techs.get(tech_nid)
        if not tech:
            continue
        for component in tech.components:
            for key, value, combine in component.flags():
                if combine == Combine.SET:
                    # A set flag's value is a list of nids, not a single one
                    cache.setdefault(key, set()).update(value if isinstance(value, list) else [value])
                elif combine == Combine.SUM:
                    cache[key] = cache.get(key, 0) + value
                elif combine == Combine.MAX:
                    cache[key] = max(cache[key], value) if key in cache else value
                else:  # Combine.OR
                    cache[key] = bool(cache.get(key, False)) or bool(value)
    team._tech_flag_cache = cache
    return cache


def invalidate_flag_cache(team: TeamObject) -> None:
    team._tech_flag_cache = None


def _get_cache(team: TeamObject) -> dict:
    if team._tech_flag_cache is None:
        return _rebuild_flag_cache(team)
    return team._tech_flag_cache


def has_tech(team: TeamObject, tech_nid: NID) -> bool:
    """Whether the team has unlocked the given tech."""
    return tech_nid in team.research


def get_tech_value(team: TeamObject, key: NID, default: Any = 0) -> Any:
    """Combined value of every unlocked flag component writing `key` (sum/max/or). O(1)."""
    return _get_cache(team).get(key, default)


def get_tech_set(team: TeamObject, key: NID) -> Set:
    """Accumulated set of every `combine=set` flag component writing `key`. O(1)."""
    val = _get_cache(team).get(key)
    if isinstance(val, set):
        return val.copy()
    return set()


def unit_matches_grant_target(unit: 'UnitObject', team: TeamObject,
                              grant_target: GrantTarget, grant_target_arg: str = '') -> bool:
    """Whether `unit` is a subject of a grant component's grant_target for `team`.
    Only unit-bearing targets match; TEAM_CITIES / SELF_TEAM never grant to a unit."""
    if unit.team != team.nid:
        return False
    if grant_target == GrantTarget.TEAM_UNITS:
        return True
    if grant_target == GrantTarget.UNITS_WITH_TAG:
        return grant_target_arg in unit.tags
    return False


def get_grant_target_units(team: TeamObject, grant_target: GrantTarget,
                           grant_target_arg: str = '') -> List['UnitObject']:
    """All current units that are subjects of a grant component's grant_target."""
    return [unit for unit in game.get_all_units(only_on_field=False)
            if unit_matches_grant_target(unit, team, grant_target, grant_target_arg)]


def get_tech_skills(unit: 'UnitObject') -> List['SkillObject']:
    """Skills a newly-created unit should receive from its team's unlocked grant_skill
    techs (skills it doesn't already have). Sibling of unit_funcs.get_global_skills:
    re-derived on unit creation, no per-unit tracking. Existing units instead get these
    at unlock time via the UnlockTech action."""
    team = game.teams.get(unit.team)
    if not team:
        return []
    current = {skill.nid for skill in unit.skills}
    skill_nids: List[NID] = []
    for tech_nid in team.research:
        tech = DB.techs.get(tech_nid)
        if not tech:
            continue
        for component in tech.components:
            if component.nid != 'grant_skill':
                continue
            if not unit_matches_grant_target(unit, team, component.grant_target, component.grant_target_arg):
                continue
            for skill_nid in component.skills:
                if skill_nid not in current and skill_nid not in skill_nids:
                    skill_nids.append(skill_nid)
    return item_funcs.create_skills(unit, skill_nids)


def can_unlock(team: TeamObject, tech_nid: NID) -> bool:
    """Whether the team may unlock `tech_nid` right now: exists, not owned, all
    prerequisites owned, all conditions pass, and enough renown."""
    tech = DB.techs.get(tech_nid)
    if not tech:
        return False
    if has_tech(team, tech_nid):
        return False
    if not all(has_tech(team, req) for req in tech.requires):
        return False
    for condition in tech.conditions:
        try:
            if not evaluate.evaluate(condition, local_args={'team': team}):
                return False
        except Exception as e:
            logging.error("Could not evaluate tech condition %s (%s)", condition, e)
            return False
    return team.renown >= tech.renown_cost
