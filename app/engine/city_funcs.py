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

from typing import List, Optional, Set, Tuple

from app.utilities import str_utils
from app.utilities.typing import NID, Pos

from app.data.database.database import DB
from app.data.database.level_units import GenericUnit
from app.data.database.tech_components import Combine

from app.engine import action, building_system
from app.engine.objects.building import BuildingObject
from app.engine.objects.unit import UnitObject
from app.engine.objects.city import CityObject
from app.engine.game_state import game


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
    positions = {pos for pos in get_all_influence_positions(city)
                 if game.board.check_bounds(pos)}
    if city.position and game.board.check_bounds(city.position):
        positions.add(city.position)
    return positions


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
    any whose class is tech-locked (`draft_unlock`) and not yet unlocked by the city's team."""
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
        if not get_valid_placement_tiles(city, candidate):
            continue
        candidates.append(candidate)
    return candidates


def get_all_influence_positions(city: CityObject) -> Set[Pos]:
    """Every tile within the city's effective influence (Manhattan), excluding center."""
    if not city.position:
        return set()
    cx, cy = city.position
    influence = get_influence(city)
    positions: Set[Pos] = set()
    for r in range(1, influence + 1):
        for i in range(-r, r + 1):
            dy = r - abs(i)
            positions.add((cx + i, cy + dy))
            positions.add((cx + i, cy - dy))
    return positions


def get_valid_placement_tiles(city: CityObject, building: BuildingObject) -> List[Pos]:
    """Tiles where `building` may be placed: within influence, in bounds, not already
    occupied by another building, and passing the building's target_restrict."""
    valid: List[Pos] = []
    for pos in get_all_influence_positions(city):
        if not game.board.check_bounds(pos):
            continue
        if pos in game.building_terrain_overrides:  # another building already here
            continue
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
    action.do(action.RegisterUnit(new_unit))
    pos = game.target_system.get_nearest_open_tile(new_unit, city.position)
    if pos:
        action.do(action.ArriveOnMap(new_unit, pos))
        # Wait is built after arrival - it snapshots the unit's position for fog of war
        action.do(action.Wait(new_unit))
    return new_unit


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
