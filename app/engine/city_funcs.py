"""
City helpers for the 4X city/building layer.

This module holds the city-level logic that sits on top of `building_system`
(the per-component dispatch): aggregating draftable units / buildable buildings,
computing valid placement, paying for a purchase, and running a city's per-turn
income.

Units and buildings are bought outright: the city menu pays the full gold / food /
production cost the moment the player selects a row, and the unit spawns (or the
building goes straight to placement) on the spot. There is no production queue.
"""

from typing import List, NamedTuple, Optional, Set, Tuple

from app.utilities import str_utils, utils
from app.utilities.typing import NID, Pos

from app.data.cities import City
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.data.database.level_units import GenericUnit
from app.data.database.tech_components import Combine

from app.engine import action, building_system, item_system, unit_funcs
from app.engine.objects.building import BuildingObject
from app.engine.objects.unit import UnitObject
from app.engine.objects.city import CityObject
from app.engine.game_state import game


class BuildingUpgrade(NamedTuple):
    """One upgrade a city could buy."""
    old: BuildingObject  #: the building standing in the city
    new: BuildingObject  #: what it would become: not in the city yet, anchored on the same tile


# ---------------------------------------------------------------------------
# Aggregation / queries
# ---------------------------------------------------------------------------

def get_influence(city: CityObject) -> int:
    """Base influence plus any bonus contributed by the city's buildings."""
    return city.influence + building_system.influence_range_modification(city)


def get_tile_yield(pos: Pos) -> dict:
    """Terrain resource yield of a single tile: its own terrain (food/production/gold)
    plus adjacency bonuses contributed by orthogonally-neighboring terrain
    (adjacent_food/adjacent_production/adjacent_gold — e.g. a river buffing its
    neighbors). Reads the *underlying* terrain (`ignore_buildings=True`) so a building
    override never changes a tile's resource yield; terrain choice is what matters.

    This is the single source of truth for per-tile yield, shared by the tile-info
    hover panel and city income."""
    totals = {'food': 0, 'production': 0, 'gold': 0}
    if not pos or not game.board.check_bounds(pos):
        return totals
    terrain = DB.terrain.get(game.get_terrain_nid(game.tilemap, pos, ignore_buildings=True))
    if terrain:
        totals['food'] += terrain.food
        totals['production'] += terrain.production
        totals['gold'] += terrain.gold
    x, y = pos
    for npos in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if not game.board.check_bounds(npos):
            continue
        nterr = DB.terrain.get(game.get_terrain_nid(game.tilemap, npos, ignore_buildings=True))
        if nterr:
            totals['food'] += nterr.adjacent_food
            totals['production'] += nterr.adjacent_production
            totals['gold'] += nterr.adjacent_gold
    return totals


def get_territory_positions(city: CityObject) -> Set[Pos]:
    """Every tile the city draws terrain income from: its center plus all influence
    tiles (Manhattan radius). In-bounds tiles only."""
    positions = get_all_influence_positions(city) | set(city.center_positions)
    return {pos for pos in positions if game.board.check_bounds(pos)}


def get_building_output(building: BuildingObject, city: CityObject) -> dict:
    """Per-turn resources a building contributes via its ResourcePerTurn component,
    including any `{tag}_resource_bonus` tech bonus for the city's team. Terrain yield
    is territory-based (see get_tile_yield) and does not depend on buildings."""
    totals = {'food': 0, 'production': 0, 'gold': 0}
    comp = building.resource_per_turn
    if comp:
        out = comp.get_output(city)
        for key in totals:
            totals[key] += out.get(key, 0)
    return totals


def get_generation(city: CityObject) -> dict:
    """Per-turn resource generation: terrain yield (base + adjacency) of every tile in
    the city's territory, plus every building's ResourcePerTurn output."""
    totals = {'food': 0, 'production': 0, 'gold': 0}
    for pos in get_territory_positions(city):
        tile = get_tile_yield(pos)
        for key in totals:
            totals[key] += tile[key]
    for building in city.buildings:
        out = get_building_output(building, city)
        for key in totals:
            totals[key] += out[key]
    return totals


def _tech_gated_values(key: NID) -> Set[NID]:
    """Every value some tech places behind a `combine=set` flag of `key`. A class /
    building nid that appears here is 'tech-locked': hidden until the team unlocks a tech
    that adds it to `game.get_tech_set(team, key)`. Nids never mentioned stay unconditional."""
    gated: Set[NID] = set()
    for tech in DB.techs:
        for component in tech.components:
            for flag_key, value, combine in component.flags():
                if combine == Combine.SET and flag_key == key:
                    gated.update(value if isinstance(value, list) else [value])
    return gated


def get_draftable_units(city: CityObject) -> List[dict]:
    """Flat list of unit-draft specs contributed by all of the city's buildings, minus
    any whose class is tech-locked (`draft_unlock`) and not yet unlocked by the city's team.
    An outpost drafts nothing."""
    if city.is_outpost:
        return []
    gated = _tech_gated_values('draft_unlock')
    unlocked = game.get_tech_set(city.team, 'draft_unlock')
    specs: List[dict] = []
    for component_specs in building_system.produces_units(city):
        for spec in component_specs:
            klass = spec.get('klass')
            if klass in gated and klass not in unlocked:
                continue
            specs.append(spec)
    return specs


def get_buildable_buildings(city: CityObject) -> List[BuildingObject]:
    """Fresh candidate BuildingObjects this city may build right now.

    A building is offered only if it is `available`, has at least one valid placement
    tile, and (if tech-locked via `build_unlock`) has been unlocked by the city's team.
    An outpost is offered only the buildings marked OutpostBuildable.
    """
    gated = _tech_gated_values('build_unlock')
    unlocked = game.get_tech_set(city.team, 'build_unlock')
    candidates: List[BuildingObject] = []
    for prefab in DB.buildings:
        if prefab.nid in gated and prefab.nid not in unlocked:
            continue
        candidate = BuildingObject.from_prefab(prefab)
        candidate.owner_nid = city.nid
        if not building_system.available(candidate, city):
            continue
        if city.is_outpost and not building_system.outpost_buildable(candidate, city):
            continue
        if not get_valid_placement_tiles(city, candidate):
            continue
        candidates.append(candidate)
    return candidates


def get_building_upgrades(city: CityObject) -> List[BuildingUpgrade]:
    """Every upgrade open to a building standing in the city, from its UpgradesTo
    component: an Outpost to a Town Hall, for one. A building that is tech-locked
    (`build_unlock`) cannot be upgraded to until the city's team unlocks it. Whether
    the city can pay for an upgrade, and whether it fits (see `upgrade_fits`), is not
    decided here."""
    gated = _tech_gated_values('build_unlock')
    unlocked = game.get_tech_set(city.team, 'build_unlock')
    upgrades: List[BuildingUpgrade] = []
    for building in city.buildings:
        if not building.position or not building.upgrades_to:
            continue
        for nid in building.upgrades_to.upgrades_to(city):
            if nid in gated and nid not in unlocked:
                continue
            candidate = BuildingObject.from_prefab(DB.buildings.get(nid))
            candidate.owner_nid = city.nid
            candidate.position = building.position
            upgrades.append(BuildingUpgrade(building, candidate))
    return upgrades


def upgrade_fits(city: CityObject, upgrade: BuildingUpgrade) -> bool:
    """Whether the new building may stand where the old one does: its whole footprint
    on the map, covering no building but the one it replaces, and somewhere the new
    building itself allows (`target_restrict`)."""
    for tile in upgrade.new.occupied_positions:
        if not game.board.check_bounds(tile):
            return False
        if game.building_position_index.get(tile, upgrade.old.uid) != upgrade.old.uid:
            return False
    return building_system.target_restrict(upgrade.new, city, upgrade.new.position)


def get_all_influence_positions(city: CityObject) -> Set[Pos]:
    """Every tile within the city's effective influence (Manhattan, measured from the
    nearest tile of the center), excluding the center."""
    return city.positions_within(get_influence(city))


def get_valid_placement_tiles(city: CityObject, building: BuildingObject) -> List[Pos]:
    """Anchor tiles where `building` may be placed.

    The building's whole footprint (see `BuildingObject.positions_at`) must lie
    within the city's influence and in bounds, and no tile of it may already be
    covered by another building. `target_restrict` is then asked about the anchor
    once; components that care about the rest of the footprint expand it themselves.
    """
    influence = get_all_influence_positions(city)
    valid: List[Pos] = []
    for pos in influence:
        footprint = building.positions_at(pos)
        if not all(tile in influence for tile in footprint):
            continue
        if not all(game.board.check_bounds(tile) for tile in footprint):
            continue
        if any(tile in game.building_position_index for tile in footprint):
            continue  # another building already covers part of the footprint
        if not building_system.target_restrict(building, city, pos):
            continue
        valid.append(pos)
    return valid


# ---------------------------------------------------------------------------
# Purchasing
# ---------------------------------------------------------------------------

def get_unit_cost(spec: dict) -> Tuple[int, int, int]:
    """The (gold, food, production) a draft spec costs."""
    return spec.get('gold_cost', 0), spec.get('food_cost', 0), spec.get('production_cost', 0)


def get_building_cost(building: BuildingObject, city: CityObject) -> Tuple[int, int, int]:
    """The (gold, food, production) `building` costs this city, via its Cost component."""
    comp = building.cost
    if not comp:
        return 0, 0, 0
    return comp.gold_cost(city), comp.food_cost(city), comp.production_cost(city)


def can_purchase(city: CityObject) -> bool:
    """Whether the city may still buy something this turn. A city produces **one** unit
    or building per turn, whichever it picks."""
    return not city.produced_this_turn


def can_afford(city: CityObject, gold_cost: int, food_cost: int, production_cost: int) -> bool:
    """Whether the city's stores (and its team's gold) cover the given cost."""
    team = game.teams.get(city.team)
    if gold_cost and (not team or team.gold < gold_cost):
        return False
    return city.food >= food_cost and city.production >= production_cost


def pay_costs(city: CityObject, gold_cost: int, food_cost: int, production_cost: int):
    """Spend the given cost out of the team's gold and the city's food/production stores
    as reversible actions. Pass negative amounts to refund."""
    team = game.teams.get(city.team)
    if gold_cost and team:
        action.do(action.ChangeTeamGold(team, -gold_cost))
    if food_cost:
        action.do(action.ChangeCityFood(city, -food_cost))
    if production_cost:
        action.do(action.ChangeCityProduction(city, -production_cost))


def mark_purchase(city: CityObject, produced: bool = True):
    """Spend (or hand back, with produced=False) the city's one purchase for the turn."""
    action.do(action.SetCityProduced(city, produced))


def upgrade_building(city: CityObject, upgrade: BuildingUpgrade):
    """Swap a building in the city for what it upgrades to. Does not pay for it - the
    caller pays (see pay_costs) and checks `upgrade_fits` first."""
    action.do(action.UpgradeBuilding(city, upgrade.old, upgrade.new))


def apply_building_bonuses(city: CityObject, unit: UnitObject):
    """Give a freshly drafted unit what the city's buildings grant it: extra starting
    levels (LevelIncrease) and flat stat bonuses (StatChange). Neither can take the
    unit past its class's max level or max stats."""
    klass = DB.classes.get(unit.klass)
    extra_levels = building_system.starting_level_modification(city, unit)
    extra_levels = min(extra_levels, klass.max_level - unit.level)
    if extra_levels > 0:
        unit_funcs.auto_level(unit, unit.level, extra_levels)
        unit.level += extra_levels

    bonus = {}
    for stat_changes in building_system.stat_change(city, unit):
        for stat_nid, value in stat_changes.items():
            bonus[stat_nid] = bonus.get(stat_nid, 0) + value
    for stat_nid, value in bonus.items():
        max_stat = klass.max_stats.get(stat_nid, 30) + unit.stat_cap_modifiers.get(stat_nid, 0)
        bonus[stat_nid] = min(value, max_stat - unit.stats[stat_nid])
    if bonus:
        unit_funcs.apply_stat_changes(unit, bonus)


def draft_unit(city: CityObject, spec: dict) -> Optional[UnitObject]:
    """Create a drafted unit of the spec's class/level on the nearest open tile to the
    city, already finished for the turn (greyed out) so it cannot act the turn it is
    bought. Does not pay for it - the caller pays (see pay_costs)."""
    klass = spec['klass']
    if klass not in DB.classes:
        return None
    unit_nid = str_utils.get_next_int('201', [u.nid for u in game.units])
    faction = DB.factions[0].nid if DB.factions else None
    prefab = GenericUnit(unit_nid, None, spec['level'], klass, faction, [], [], city.team, 'None')
    new_unit = UnitObject.from_prefab(prefab, game.current_mode)
    new_unit.party = game.current_party
    apply_building_bonuses(city, new_unit)
    action.do(action.RegisterUnit(new_unit))
    pos = game.target_system.get_nearest_open_tile(new_unit, city.position)
    if pos:
        action.do(action.ArriveOnMap(new_unit, pos))
        # Wait is built after arrival - it snapshots the unit's position for fog of war
        action.do(action.Wait(new_unit))
    return new_unit


# ---------------------------------------------------------------------------
# Carried food
# ---------------------------------------------------------------------------

def get_carried_food(unit: UnitObject) -> int:
    """Total food held in the food items the unit carries."""
    return sum(item.data['food'] for item in unit.items if item.food)


def spend_carried_food(unit: UnitObject, amount: int):
    """Take `amount` food out of the unit's food items, emptying the first before
    touching the next, as reversible actions. An item that runs out is used up. The
    caller checks the unit has enough."""
    for item in unit.items.copy():
        if amount <= 0:
            break
        if item.food:
            spent = min(amount, item.data['food'])
            if spent:
                action.do(action.SetObjData(item, 'food', item.data['food'] - spent))
            amount -= spent
            if item_system.is_broken(unit, item):
                item_system.on_broken(unit, item)


# ---------------------------------------------------------------------------
# Founding
# ---------------------------------------------------------------------------

def get_outpost_prefab() -> Optional[BuildingPrefab]:
    """The building a newly founded city starts as: the one carrying the Outpost
    component."""
    for prefab in DB.buildings:
        if prefab.outpost:
            return prefab
    return None


def new_outpost_city(unit: UnitObject) -> Tuple[CityObject, BuildingObject]:
    """A city for `unit` to found, and the Outpost that will be its center, anchored
    on the unit's tile. Neither is on the map yet: the city is not registered and the
    Outpost is not in it (see action.FoundCity)."""
    outpost_prefab = get_outpost_prefab()
    prefab = City(str_utils.get_next_name(outpost_prefab.name, [city.nid for city in game.city_registry.values()]))
    prefab.team = unit.team
    prefab.position = unit.position
    city = CityObject.from_prefab(prefab)
    outpost = BuildingObject.from_prefab(outpost_prefab)
    outpost.position = unit.position
    outpost.owner_nid = city.nid
    return city, outpost


def get_found_cost(city: CityObject, outpost: BuildingObject) -> Tuple[int, int]:
    """The (gold, food) it costs to found `city`, from its Outpost's Cost component.
    Gold comes from the team; food from what the founding unit carries. A new city
    has no production store to draw on, so a production cost is not charged."""
    gold_cost, food_cost, _ = get_building_cost(outpost, city)
    return gold_cost, food_cost


def can_found_city(unit: UnitObject) -> bool:
    """Whether `unit` may found a city where it stands. The Outpost's whole footprint
    must be on the map, clear of other buildings, at least `city_min_distance` tiles
    from every other city's center, and somewhere the Outpost itself allows
    (`target_restrict`); and the unit's team and the unit must cover the cost."""
    if not get_outpost_prefab():
        return False
    city, outpost = new_outpost_city(unit)
    footprint = outpost.occupied_positions
    if not all(game.board.check_bounds(tile) for tile in footprint):
        return False
    if any(tile in game.building_position_index for tile in footprint):
        return False
    min_distance = DB.constants.value('city_min_distance')
    for other in game.cities:
        if any(utils.calculate_distance(tile, center) < min_distance
               for tile in footprint for center in other.center_positions):
            return False
    if not building_system.target_restrict(outpost, city, outpost.position):
        return False
    gold_cost, food_cost = get_found_cost(city, outpost)
    return game.teams.get(unit.team).gold >= gold_cost and get_carried_food(unit) >= food_cost


def found_city(unit: UnitObject) -> CityObject:
    """Found a city where `unit` stands and pay for it. The caller checks
    `can_found_city` first."""
    city, outpost = new_outpost_city(unit)
    gold_cost, food_cost = get_found_cost(city, outpost)
    if gold_cost:
        action.do(action.ChangeTeamGold(game.teams.get(unit.team), -gold_cost))
    spend_carried_food(unit, food_cost)
    action.do(action.FoundCity(city, outpost))
    return city


# ---------------------------------------------------------------------------
# Per-turn income
# ---------------------------------------------------------------------------

def _apply_territory_income(city: CityObject):
    """Apply the terrain resource yield (base + adjacency) of every tile in the city's
    territory as reversible actions (mirrors ResourcePerTurn.on_upkeep)."""
    team = game.teams.get(city.team)
    totals = {'food': 0, 'production': 0, 'gold': 0}
    for pos in get_territory_positions(city):
        tile = get_tile_yield(pos)
        for key in totals:
            totals[key] += tile[key]
    if totals['food']:
        action.do(action.ChangeCityFood(city, totals['food']))
    if totals['production']:
        action.do(action.ChangeCityProduction(city, totals['production']))
    if totals['gold'] and team:
        action.do(action.ChangeTeamGold(team, totals['gold']))


def run_city_upkeep(city: CityObject):
    """Run a single city's start-of-turn income: every building's ResourcePerTurn, plus
    the terrain yield of every tile in the city's radius. Cities have no resource upkeep
    and do not grow on their own. Also refreshes the city's one purchase for the turn."""
    if city.produced_this_turn:
        mark_purchase(city, False)
    building_system.on_upkeep(city)
    _apply_territory_income(city)


def run_all_city_upkeeps(team: NID):
    """Run upkeep for every city owned by the given team."""
    for city in game.cities:
        if city.team == team:
            run_city_upkeep(city)


def get_unit_upkeep(team: NID) -> int:
    """Total gold a team's units cost this turn: each living unit's class `upkeep_cost`,
    reduced per-unit by every `upkeep_cost_<tag>` tech for the tags that unit carries
    (floored at 0 per unit so a unit never yields gold). Off-field units count too."""
    total = 0
    for unit in game.get_team_units(team, only_on_field=False):
        if unit.dead:
            continue
        klass = DB.classes.get(unit.klass)
        if not klass or not klass.upkeep_cost:
            continue
        cost = klass.upkeep_cost
        for tag in unit.tags:
            cost -= game.get_tech_value(team, 'upkeep_cost_' + tag)
        total += max(0, cost)
    return total


def run_unit_upkeep(team: NID):
    """Deduct the team's total unit upkeep (see get_unit_upkeep) from its gold as a single
    reversible action."""
    upkeep = get_unit_upkeep(team)
    team_obj = game.teams.get(team)
    if upkeep and team_obj:
        action.do(action.ChangeTeamGold(team_obj, -upkeep))
