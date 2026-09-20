from app.data.database.building_components import (RESOURCE_BONUS_TAGS,
                                                    BuildingComponent,
                                                    BuildingTags)
from app.data.database.components import ComponentType

from app.events.regions import RegionType

from app.utilities import utils

from app.engine import action
from app.engine.objects.region import RegionObject
from app.engine.game_state import game

import logging


class BuildingTag(BuildingComponent):
    nid = 'building_tags'
    desc = 'Attach arbitrary tags to buildings. Useful for conditionals and resource bonuses.'
    tag = BuildingTags.BASE

    expose = (ComponentType.List, ComponentType.Tag)
    value = []


class Cost(BuildingComponent):
    nid = 'cost'
    desc = "Determines how much this building costs to produce or upgrade to"
    tag = BuildingTags.BASE

    expose = ComponentType.NewMultipleOptions

    options = {
        'base_production_cost': ComponentType.Int,
        'base_food_cost': ComponentType.Int,
        'base_gold_cost': ComponentType.Int,
        'reduced_production_cost': ComponentType.Int,
        'reduced_food_cost': ComponentType.Int,
        'reduced_gold_cost': ComponentType.Int,
        'cost_reduction': ComponentType.String,
    }

    def __init__(self, value=None):
        self.value = {
            'base_production_cost': 0,
            'base_food_cost': 0,
            'base_gold_cost': 0,
            'reduced_production_cost': 0,
            'reduced_food_cost': 0,
            'reduced_gold_cost': 0,
            'cost_reduction': "",
        }
        if value:
            self.value.update(value)

    def _get_eval_cost_reduction(self, city) -> bool:
        from app.engine import evaluate
        if self.value["cost_reduction"]:
            try:
                return bool(evaluate.evaluate(self.value["cost_reduction"], local_args={'city': city, 'building': self.building}))
            except:
                logging.error("Cost: Couldn't evaluate %s conditional" % self.value["cost_reduction"])
        return False

    def production_cost(self, city) -> int:
        return self.value["reduced_production_cost"] \
            if self._get_eval_cost_reduction(city) \
            else self.value["base_production_cost"]

    def food_cost(self, city) -> int:
        return self.value["reduced_food_cost"] \
            if self._get_eval_cost_reduction(city) \
            else self.value["base_food_cost"]

    def gold_cost(self, city) -> int:
        return self.value["reduced_gold_cost"] \
            if self._get_eval_cost_reduction(city) \
            else self.value["base_gold_cost"]


class Requires(BuildingComponent):
    nid = "requires"
    desc = "Evaluated to determine whether this building can be built at all"
    tag = BuildingTags.BASE

    expose = ComponentType.String
    value = ""

    def available(self, city) -> bool:
        from app.engine import evaluate
        try:
            ans = bool(evaluate.evaluate(self.value, local_args={'city': city, 'building': self.building}))
            return ans
        except:
            logging.error("Requires: Couldn't evaluate %s conditional" % self.value)
        return False


class Unique(BuildingComponent):
    nid = "unique"
    desc = "Building can only be built if no other building with the same nid already exists in the city"
    tag = BuildingTags.BASE

    def available(self, city) -> bool:
        return not any(building.nid == self.building.nid for building in city.buildings)


class LevelIncrease(BuildingComponent):
    nid = "level_increase"
    desc = "Units with the tag/tags start with their level increased"
    tag = BuildingTags.BASE

    expose = ComponentType.NewMultipleOptions

    options = {
        "tags": (ComponentType.List, ComponentType.Tag),
        "level_increase": ComponentType.Int,
    }

    def __init__(self, value=None):
        self.value = {
            "tags": [],
            "level_increase": 0,
        }
        if value:
            self.value.update(value)

    def starting_level_modification(self, city, unit) -> int:
        if any(tag in unit.tags for tag in self.value["tags"]):
            return self.value["level_increase"]
        return 0


class UpgradesTo(BuildingComponent):
    nid = "upgrades_to"
    desc = "Building can be upgraded to these options"
    tag = BuildingTags.BASE

    expose = (ComponentType.List, ComponentType.Building)

    def upgrades_to(self, city):
        return self.value


class RequiresTerrain(BuildingComponent):
    nid = "requires_terrain"
    desc = "Building requires specific terrain"
    tag = BuildingTags.BASE

    expose = (ComponentType.List, ComponentType.Terrain)

    def target_restrict(self, city, position) -> bool:
        # Every tile of the footprint must qualify, not just the anchor.
        # Underlying terrain (ignore_buildings=True): a building override must not
        # satisfy/block the requirement, so replacing one building with another still
        # validates against the real terrain it sits on.
        for tile in self.building.positions_at(position):
            terrain_nid = game.get_terrain_nid(game.tilemap, tile, ignore_buildings=True)
            if terrain_nid not in self.value:
                return False
        return True


class RequiresAdjacency(BuildingComponent):
    nid = "requires_adjacency"
    desc = "Building must be placed adjacent to the city's town hall or another adjacency-requiring building"
    tag = BuildingTags.BASE

    def target_restrict(self, city, position) -> bool:
        # Any tile of the footprint being adjacent is enough, so compare footprints
        # rather than anchors.
        footprint = self.building.positions_at(position)
        # Adjacent to the city's own position (the town hall)
        if city.position and self._is_adjacent(footprint, [city.position]):
            return True
        # Adjacent to another building in the city that also requires adjacency
        for building in city.buildings:
            if building.position and building.requires_adjacency \
                    and self._is_adjacent(footprint, building.occupied_positions):
                return True
        return False

    def _is_adjacent(self, footprint, other_positions) -> bool:
        return any(utils.calculate_distance(tile, other) == 1
                   for tile in footprint for other in other_positions)


class StatChange(BuildingComponent):
    nid = "stat_change"
    desc = "Gives stat bonuses to units built in this city"
    tag = BuildingTags.BASE

    expose = (ComponentType.Dict, ComponentType.Stat)
    value = []

    def stat_change(self, city, unit):
        return {stat[0]: stat[1] for stat in self.value}


class ResourcePerTurn(BuildingComponent):
    nid = "resource_per_turn"
    desc = "Gives resources to the city each turn"
    tag = BuildingTags.BASE

    expose = ComponentType.NewMultipleOptions

    options = {
        "food": ComponentType.Int,
        "production": ComponentType.Int,
        "gold": ComponentType.Int,
    }

    def __init__(self, value=None):
        self.value = {
            "food": 0,
            "production": 0,
            "gold": 0,
        }
        if value:
            self.value.update(value)

    def get_output(self, city) -> dict:
        """Effective per-turn output: the base food/production/gold plus any
        `{tag}_resource_bonus` tech bonus for the building's tags (see RESOURCE_BONUS_TAGS).
        Shared by on_upkeep (income) and city_funcs.get_building_output (display) so they
        never diverge."""
        out = self.value.copy()
        tags = self.building.tags
        for tag, resource in RESOURCE_BONUS_TAGS.items():
            if tag in tags:
                out[resource] += game.get_tech_value(city.team, tag.lower() + '_resource_bonus')
        return out

    def on_upkeep(self, city):
        team = game.teams[city.team]
        out = self.get_output(city)
        if out["food"]:
            action.do(action.ChangeCityFood(city, out["food"]))
        if out["production"]:
            action.do(action.ChangeCityProduction(city, out["production"]))
        if out["gold"]:
            action.do(action.ChangeTeamGold(team, out["gold"]))


class ProducesUnits(BuildingComponent):
    nid = "produces_units"
    desc = "Units of these classes can be drafted from the city while this building is present"
    tag = BuildingTags.BASE

    expose = ComponentType.UnitDraftList

    def __init__(self, value=None):
        # value is a list of [class_nid, level, gold_cost, food_cost, production_cost] rows
        self.value = [self._pad(row) for row in value] if value else []

    @staticmethod
    def _pad(row) -> list:
        """A four-column row on disk is [class, level, gold, production] and has no food
        cost; food belongs at index 3."""
        row = list(row)
        if len(row) == 4:
            row.insert(3, 0)
        return row

    def produces_units(self, city):
        specs = []
        for row in self.value:
            klass, level, gold_cost, food_cost, production_cost = row
            specs.append({
                "klass": klass,
                "level": level,
                "gold_cost": gold_cost,
                "food_cost": food_cost,
                "production_cost": production_cost,
            })
        return specs


class InfluenceBonus(BuildingComponent):
    nid = 'influence_bonus'
    desc = "City gains a bonus to influence range"
    tag = BuildingTags.BASE

    expose = ComponentType.Int
    value = 1

    def influence_range_modification(self, city):
        return self.value


class HasEventRegion(BuildingComponent):
    nid = 'has_event_region'
    desc = "Building has an event region attached to it"
    tag = BuildingTags.BASE

    expose = ComponentType.Event
    value = None

    def after_add(self, city, building):
        position = self.building.position

        new_region = RegionObject(self.nid, RegionType.EVENT)
        new_region.position = position
        new_region.size = (1, 1)
        new_region.sub_nid = self.value

        game.register_region(new_region)
        action.do(action.AddRegion(new_region))

    def after_remove(self, city, building):
        if self.nid in self.game.level.regions:
            region = self.game.level.regions.get(self.nid)
            action.do(action.RemoveRegion(region))
        else:
            self.logger.error(f"HasEventRegion: Could not find region with nid {self.nid}")


class HasSkillRegion(BuildingComponent):
    nid = 'has_skill_region'
    desc = "Building has a skill region attached to it"
    tag = BuildingTags.BASE

    expose = ComponentType.Skill
    value = None

    def after_add(self, city, building):
        position = self.building.position

        new_region = RegionObject(self.nid, RegionType.STATUS)
        new_region.position = position
        new_region.size = (1, 1)
        new_region.sub_nid = self.value

        game.register_region(new_region)
        action.do(action.AddRegion(new_region))

    def after_remove(self, city, building):
        if self.nid in self.game.level.regions:
            region = self.game.level.regions.get(self.nid)
            action.do(action.RemoveRegion(region))
        else:
            self.logger.error(f"HasSkillRegion: Could not find region with nid {self.nid}")
