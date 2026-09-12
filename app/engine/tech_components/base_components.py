from __future__ import annotations

from typing import Any, List, Tuple

from app.data.database.building_components import RESOURCE_BONUS_TAGS
from app.data.database.components import ComponentType
from app.data.database.tech_components import (Combine, GrantTarget,
                                               TechComponent, TechTags)

# The building tags a ResourceBonus can boost. A ResourceBonus writes
# `{tag.lower()}_resource_bonus`, which ResourcePerTurn.get_output reads off the same map.
RESOURCE_TAGS = tuple(RESOURCE_BONUS_TAGS)

GRANT_TARGETS = tuple(t.value for t in GrantTarget)
COMBINES = tuple(c.value for c in Combine)


class ExpMultBonus(TechComponent):
    nid = 'exp_mult_bonus'
    desc = "Units on this team gain this much extra experience, as a fraction. " \
           "0.1 means +10%. Stacks additively with other techs."
    tag = TechTags.MILITARY

    expose = ComponentType.Float
    value = 0.1

    flag_key = 'exp_mult_bonus'
    combine = Combine.SUM


class CityPopBonus(TechComponent):
    nid = 'city_pop_bonus'
    desc = "Grants this much extra population to every city this team owns when the " \
           "tech unlocks, and to every city it founds or gains afterwards. Stacks " \
           "additively with other techs."
    tag = TechTags.ECONOMY

    expose = ComponentType.Int
    value = 5

    # The flag is what a city reads when it is created after the unlock; the population of
    # cities that already exist is topped up by UnlockTech (which matches on this nid).
    flag_key = 'city_pop_bonus'
    combine = Combine.SUM


class RoadMoveBonus(TechComponent):
    nid = 'road_move_bonus'
    desc = "Reduces the movement cost of entering a road tile by this much " \
           "(never below 1). Only the largest bonus applies."
    tag = TechTags.EXPLORATION

    expose = ComponentType.Int
    value = 1

    flag_key = 'road_move_bonus'
    combine = Combine.MAX


class OverworldSightBonus(TechComponent):
    nid = 'overworld_sight_bonus'
    desc = "This team's units see this many extra tiles through fog of war. " \
           "Only the largest bonus applies."
    tag = TechTags.EXPLORATION

    expose = ComponentType.Int
    value = 2

    flag_key = 'overworld_sight_bonus'
    combine = Combine.MAX


class WeaponTier(TechComponent):
    nid = 'weapon_tier'
    desc = "Raises this team's weapon tier. Items follow their `UpgradesTo` chain up to " \
           "the highest tier the team has unlocked. Only the largest tier applies. " \
           "Add an Upgrade Items component to also sweep weapons units already carry."
    tag = TechTags.MILITARY

    expose = ComponentType.Int
    value = 1

    flag_key = 'weapon_tier'
    combine = Combine.MAX


class DraftUnlock(TechComponent):
    nid = 'draft_unlock'
    desc = "Lets this team draft these classes in cities. A class named by any tech is " \
           "locked until a team unlocks it; classes no tech mentions stay available."
    tag = TechTags.UNLOCK

    expose = (ComponentType.List, ComponentType.Class)
    value = []

    flag_key = 'draft_unlock'
    combine = Combine.SET


class BuildUnlock(TechComponent):
    nid = 'build_unlock'
    desc = "Lets this team build these buildings in cities. A building named by any tech " \
           "is locked until a team unlocks it; buildings no tech mentions stay available."
    tag = TechTags.UNLOCK

    expose = (ComponentType.List, ComponentType.Building)
    value = []

    flag_key = 'build_unlock'
    combine = Combine.SET


class ResourceBonus(TechComponent):
    nid = 'resource_bonus'
    desc = "Buildings carrying the given tag produce this much more of their resource " \
           "each turn. Stacks additively with other techs."
    tag = TechTags.ECONOMY

    expose = ComponentType.NewMultipleOptions

    options = {
        'building_tag': (ComponentType.MultipleChoice, RESOURCE_TAGS),
        'amount': ComponentType.Int,
    }

    combine = Combine.SUM

    def __init__(self, value=None):
        self.value = {
            'building_tag': RESOURCE_TAGS[0],
            'amount': 1,
        }
        if value:
            self.value.update(value)

    def flags(self) -> List[Tuple[str, Any, Combine]]:
        tag = self.value['building_tag']
        if not tag:
            return []
        return [(tag.lower() + '_resource_bonus', self.value['amount'], self.combine)]


class UpkeepCostReduction(TechComponent):
    nid = 'upkeep_cost_reduction'
    desc = "Units carrying the given tag cost this much less gold in upkeep each turn " \
           "(a unit never costs less than 0). Stacks additively with other techs."
    tag = TechTags.ECONOMY

    expose = ComponentType.NewMultipleOptions

    options = {
        'unit_tag': ComponentType.Tag,
        'amount': ComponentType.Int,
    }

    combine = Combine.SUM

    def __init__(self, value=None):
        self.value = {
            'unit_tag': None,
            'amount': 1,
        }
        if value:
            self.value.update(value)

    def flags(self) -> List[Tuple[str, Any, Combine]]:
        tag = self.value['unit_tag']
        if not tag:
            return []
        return [('upkeep_cost_' + tag, self.value['amount'], self.combine)]


class GrantSkillEffect(TechComponent):
    nid = 'grant_skill'
    desc = "Gives these skills to the chosen units the moment the tech unlocks, and to " \
           "any qualifying unit created afterwards. Use only when the effect must ride " \
           "per-unit through the skill system; a flag component is cheaper. " \
           "`grant_target_arg` is the tag to match when the target is `units_with_tag`."
    tag = TechTags.ADVANCED

    expose = ComponentType.NewMultipleOptions

    options = {
        'skills': (ComponentType.List, ComponentType.Skill),
        'grant_target': (ComponentType.MultipleChoice, GRANT_TARGETS),
        'grant_target_arg': ComponentType.Tag,
    }

    def __init__(self, value=None):
        self.value = {
            'skills': [],
            'grant_target': GrantTarget.TEAM_UNITS.value,
            'grant_target_arg': None,
        }
        if value:
            self.value.update(value)

    @property
    def skills(self) -> List[str]:
        return self.value['skills']

    @property
    def grant_target(self) -> GrantTarget:
        return GrantTarget(self.value['grant_target'])

    @property
    def grant_target_arg(self) -> str:
        return self.value['grant_target_arg'] or ''


class UpgradeItemsEffect(TechComponent):
    nid = 'upgrade_items'
    desc = "Upgrades every item the chosen units carry along its `UpgradesTo` chain, as " \
           "far as this team's weapon tier allows. Pair with a Weapon Tier component on " \
           "the same tech to raise the tier first. Convoy and map loot are not swept."
    tag = TechTags.ADVANCED

    expose = ComponentType.NewMultipleOptions

    options = {
        'grant_target': (ComponentType.MultipleChoice, GRANT_TARGETS),
        'grant_target_arg': ComponentType.Tag,
    }

    def __init__(self, value=None):
        self.value = {
            'grant_target': GrantTarget.TEAM_UNITS.value,
            'grant_target_arg': None,
        }
        if value:
            self.value.update(value)

    @property
    def grant_target(self) -> GrantTarget:
        return GrantTarget(self.value['grant_target'])

    @property
    def grant_target_arg(self) -> str:
        return self.value['grant_target_arg'] or ''


class CustomFlag(TechComponent):
    nid = 'custom_flag'
    desc = "Writes an arbitrary flag key the engine can read with " \
           "`game.get_tech_value(team, key)`. The escape hatch for a read site that has " \
           "no component of its own yet -- prefer a real component once one exists, " \
           "since this cannot check the key or the combine policy for you."
    tag = TechTags.CUSTOM

    expose = ComponentType.NewMultipleOptions

    options = {
        'key': ComponentType.String,
        'value': ComponentType.String,
        'combine': (ComponentType.MultipleChoice, COMBINES),
    }

    def __init__(self, value=None):
        self.value = {
            'key': '',
            'value': '',
            'combine': Combine.OR.value,
        }
        if value:
            self.value.update(value)

    def flags(self) -> List[Tuple[str, Any, Combine]]:
        key = self.value['key']
        if not key:
            return []
        return [(key, _coerce(self.value['value']), Combine(self.value['combine']))]


def _coerce(raw: str) -> Any:
    """A CustomFlag value is typed as a string because its key is arbitrary, but the read
    sites expect numbers and bools. Interpret the text the way the designer meant it."""
    if isinstance(raw, str):
        text = raw.strip()
        if text.lower() in ('true', 'false'):
            return text.lower() == 'true'
        try:
            return int(text)
        except ValueError:
            pass
        try:
            return float(text)
        except ValueError:
            pass
    return raw
