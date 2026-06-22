"""
City helpers for the 4X city/building layer.

This module holds the city-level logic that sits on top of `building_system`
(the per-component dispatch): aggregating draftable units / buildable buildings,
computing valid placement, and running a city's per-turn upkeep.

Production-queue entry schema (plain JSON-serializable dicts, stored verbatim in
`CityObject.production_queue`):

    building entry:
        {'kind': 'building', 'nid': <building_nid>,
         'production_cost': int, 'gold_paid': int}

    unit entry:
        {'kind': 'unit', 'nid': <label>, 'klass': <class_nid>, 'level': int,
         'team': <team_nid>, 'production_cost': int, 'gold_paid': int}

Production accrues in the shared `city.production` pool; a front entry completes
when `city.production >= production_cost` and pays the full cost at once (leftover
stays in the pool, so excess accrues). `gold_paid` is recorded only so a building
that cannot be placed at completion can be refunded exactly.
"""

from typing import List, Optional, Set, Tuple

from app.utilities import str_utils
from app.utilities.typing import NID, Pos

from app.data.database.database import DB
from app.data.database.level_units import GenericUnit

from app.engine import action, building_system
from app.engine.objects.building import BuildingObject
from app.engine.objects.unit import UnitObject
from app.engine.objects.city import CityObject
from app.engine.game_state import game


# ---------------------------------------------------------------------------
# Production-queue entry factories
# ---------------------------------------------------------------------------

def make_building_entry(building_nid: NID, production_cost: int, gold_paid: int) -> dict:
    return {
        'kind': 'building',
        'nid': building_nid,
        'production_cost': production_cost,
        'gold_paid': gold_paid,
    }


def make_unit_entry(klass: NID, level: int, team: NID,
                    production_cost: int, gold_paid: int, nid: Optional[str] = None) -> dict:
    return {
        'kind': 'unit',
        'nid': nid or klass,
        'klass': klass,
        'level': level,
        'team': team,
        'production_cost': production_cost,
        'gold_paid': gold_paid,
    }


# ---------------------------------------------------------------------------
# Aggregation / queries
# ---------------------------------------------------------------------------

def get_influence(city: CityObject) -> int:
    """Base influence plus any bonus contributed by the city's buildings."""
    return city.influence + building_system.influence_range_modification(city)


def get_food_upkeep(city: CityObject) -> int:
    """Food the city consumes each turn (currently equal to its population)."""
    return city.population


def get_generation(city: CityObject) -> dict:
    """Per-turn resource generation from the city's currently worked buildings."""
    totals = {'food': 0, 'production': 0, 'gold': 0}
    for building in city.buildings:
        if not city.is_worked(building):
            continue
        comp = building.resource_per_turn
        if comp:
            for key in totals:
                totals[key] += comp.value.get(key, 0)
    return totals


def get_draftable_units(city: CityObject) -> List[dict]:
    """Flat list of unit-draft specs contributed by all of the city's buildings."""
    specs: List[dict] = []
    for component_specs in building_system.produces_units(city):
        specs.extend(component_specs)
    return specs


def get_buildable_buildings(city: CityObject) -> List[BuildingObject]:
    """Fresh candidate BuildingObjects this city may build right now.

    A building is offered only if it is `available` and has at least one valid
    placement tile.
    """
    candidates: List[BuildingObject] = []
    for prefab in DB.buildings:
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
# Per-turn upkeep
# ---------------------------------------------------------------------------

def food_threshold(population: int) -> int:
    base = DB.constants.value('city_food_base')
    growth = DB.constants.value('city_food_growth')
    return base + (population - 1) * growth


def _spawn_unit(city: CityObject, entry: dict) -> Optional[UnitObject]:
    klass = entry['klass']
    if klass not in DB.classes:
        return None
    unit_nid = str_utils.get_next_int('201', [u.nid for u in game.units])
    faction = DB.factions[0].nid if DB.factions else None
    prefab = GenericUnit(unit_nid, None, entry['level'], klass, faction, [], [], entry['team'], 'None')
    new_unit = UnitObject.from_prefab(prefab, game.current_mode)
    new_unit.party = game.current_party
    action.do(action.RegisterUnit(new_unit))
    pos = game.target_system.get_nearest_open_tile(new_unit, city.position)
    if pos:
        action.do(action.ArriveOnMap(new_unit, pos))
    return new_unit


def _refund(city: CityObject, entry: dict):
    team = game.teams.get(city.team)
    if team and entry.get('gold_paid'):
        action.do(action.ChangeTeamGold(team, entry['gold_paid']))
    if entry.get('production_cost'):
        action.do(action.ChangeCityProduction(city, entry['production_cost']))


def run_city_upkeep(city: CityObject) -> List[Tuple[CityObject, BuildingObject]]:
    """Run a single city's start-of-turn upkeep. Returns a list of (city, building)
    placements the player must position (completed buildings)."""
    # 1. Resource income from worked buildings (each component self-gates on is_worked)
    building_system.on_upkeep(city)

    # 2. Food upkeep (currently equal to population)
    upkeep = get_food_upkeep(city)
    if upkeep:
        action.do(action.ChangeCityFood(city, -upkeep))

    # 3. Population growth: spend food while it crosses the rising threshold
    while city.food >= food_threshold(city.population):
        action.do(action.ChangeCityFood(city, -food_threshold(city.population)))
        action.do(action.ChangeCityPopulation(city, 1))

    # 4. Queue completion: pay the front entry from the production pool while affordable
    pending_placements: List[Tuple[CityObject, BuildingObject]] = []
    while city.production_queue:
        entry = city.production_queue[0]
        cost = entry.get('production_cost', 0)
        if city.production < cost:
            break
        if cost:
            action.do(action.ChangeCityProduction(city, -cost))
        action.do(action.RemoveFromProductionQueue(city, 0))

        if entry['kind'] == 'unit':
            _spawn_unit(city, entry)
        elif entry['kind'] == 'building':
            prefab = DB.buildings.get(entry['nid'])
            if not prefab:
                continue
            building = BuildingObject.from_prefab(prefab)
            building.owner_nid = city.nid
            if get_valid_placement_tiles(city, building):
                pending_placements.append((city, building))
            else:
                _refund(city, entry)
    return pending_placements


def run_all_city_upkeeps(team: NID) -> List[Tuple[CityObject, BuildingObject]]:
    """Run upkeep for every city owned by the given team. Returns all pending
    building placements gathered across those cities."""
    pending: List[Tuple[CityObject, BuildingObject]] = []
    for city in game.cities:
        if city.team == team:
            pending.extend(run_city_upkeep(city))
    return pending
