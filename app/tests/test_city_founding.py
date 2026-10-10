import app.engine.building_component_access as BCA
import app.engine.item_component_access as ICA
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.data.database.items import ItemPrefab
from app.engine import abilities, action, building_system, city_funcs, item_funcs, item_system
from app.engine.objects.building import BuildingObject
from app.tests.engine_harness import EngineTestCase, diff_saves
from app.tests.test_city_capture import TOWN_HALL, add_building_prefabs, add_city
from app.utilities.data import Data

# testing_proj level 0: Eirika (4, 5) and Seth (4, 4) against the generic
# fighters 101 (9, 6) and 102 (8, 6), with O'Neill guarding (10, 8).
# Mostly walls. The only open two by two blocks are around SITE and around FAR_SITE
LEVEL = '0'
SITE = (3, 3)
SITE_TILES = {(3, 3), (4, 3), (3, 4), (4, 4)}
FAR_SITE = (11, 7)

OUTPOST = 'TestOutpost'
RATIONS = 'TestRations'
GOLD_COST = 100
FOOD_COST = 15

# A movement type of testing_proj, and a terrain of it that type cannot enter
WALKER = 'Regular'
WALL_TERRAIN = '9'


def add_founding_prefabs():
    '''An Outpost that costs gold and food to found, and a sack holding 10 food'''
    DB.buildings.append(BuildingPrefab(
        OUTPOST, 'Outpost', '', None, size=(2, 2),
        components=Data([
            BCA.restore_component(('city_center', None)),
            BCA.restore_component(('outpost', None)),
            BCA.restore_component(('requires_traversable', WALKER)),
            BCA.restore_component(('cost', {'base_gold_cost': GOLD_COST, 'base_food_cost': FOOD_COST})),
        ])))
    DB.items.append(ItemPrefab(
        RATIONS, 'Rations', '',
        components=Data([ICA.restore_component(('food', 10))])))
    # A building an outpost may build, and one only a full city may
    DB.buildings.append(BuildingPrefab(
        'Quarry', 'Quarry', '', None,
        components=Data([BCA.restore_component(('outpost_buildable', None))])))
    DB.buildings.append(BuildingPrefab(
        'Academy', 'Academy', '', None,
        components=Data([BCA.restore_component(('produces_units', [['Myrmidon', 1, 0, 0, 0]]))])))


def give_rations(game, unit):
    item = item_funcs.create_item(unit, RATIONS)
    game.register_item(item)
    unit.add_item(item)
    return item


class FoundingTestCase(EngineTestCase):
    def setUp(self):
        super().setUp()
        add_building_prefabs()
        add_founding_prefabs()
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')
        self.eirika = self.game.get_unit('Eirika')
        self.team = self.game.teams.get('player')

    def stand_on_site(self):
        action.do(action.Teleport(self.eirika, SITE))

    def supply(self, gold=GOLD_COST, sacks=2):
        '''Enough to found one city, unless told otherwise'''
        self.team.gold = gold
        return [give_rations(self.game, self.eirika) for _ in range(sacks)]


class CarriedFoodTests(FoundingTestCase):
    def test_a_unit_carries_the_food_in_all_its_food_items(self):
        self.supply(sacks=2)
        self.assertEqual(20, city_funcs.get_carried_food(self.eirika))

    def test_a_unit_with_no_food_items_carries_none(self):
        self.assertEqual(0, city_funcs.get_carried_food(self.eirika))

    def test_spending_takes_from_the_first_item_first(self):
        first, second = self.supply(sacks=2)
        city_funcs.spend_carried_food(self.eirika, 4)
        self.assertEqual((6, 10), (first.data['food'], second.data['food']))

    def test_an_item_that_runs_out_is_used_up_and_the_next_one_pays_the_rest(self):
        first, second = self.supply(sacks=2)
        city_funcs.spend_carried_food(self.eirika, 13)
        self.assertNotIn(first, self.eirika.items)
        self.assertIn(second, self.eirika.items)
        self.assertEqual(7, second.data['food'])

    def test_spending_exactly_what_an_item_holds_uses_it_up(self):
        first, second = self.supply(sacks=2)
        city_funcs.spend_carried_food(self.eirika, 10)
        self.assertNotIn(first, self.eirika.items)
        self.assertEqual(10, second.data['food'])

    def test_turning_back_a_spend_returns_the_item_with_its_food(self):
        first, second = self.supply(sacks=2)
        items = self.eirika.items.copy()
        start = len(self.game.action_log.actions)
        city_funcs.spend_carried_food(self.eirika, 13)
        for act in reversed(self.game.action_log.actions[start:]):
            act.reverse()
        self.assertEqual(items, self.eirika.items)
        self.assertEqual((10, 10), (first.data['food'], second.data['food']))

    def test_an_item_shows_how_much_food_it_has_left(self):
        first, _ = self.supply(sacks=2)
        city_funcs.spend_carried_food(self.eirika, 4)
        display = item_system.item_uses_display(self.eirika, first)
        self.assertEqual((6, '/', 10),
                         (display.get_curr_uses(self.eirika, first), display.delim,
                          display.get_max_uses(self.eirika, first)))


class FoundingTests(FoundingTestCase):
    def menu_options(self) -> list:
        return [option.get() for option in self.game.state.current_state().menu.options]

    def test_a_supplied_hero_is_offered_found(self):
        self.supply()
        self.harness.move_unit('Eirika', SITE)
        self.assertIn('Found', self.menu_options())

    def test_founding_puts_an_outpost_under_the_hero_and_charges_for_it(self):
        first, second = self.supply(gold=GOLD_COST + 30)
        self.harness.move_unit('Eirika', SITE)
        self.harness.choose('Found')
        self.harness.run_until_state('free')

        city = self.game.get_city_at(SITE)
        self.assertEqual('player', city.team)
        self.assertEqual(OUTPOST, city.center.nid)
        self.assertEqual(SITE_TILES, set(city.center_positions))
        self.assertEqual(30, self.team.gold)
        self.assertEqual(20 - FOOD_COST, city_funcs.get_carried_food(self.eirika))
        self.assertTrue(self.eirika.finished)

    def test_a_founded_city_survives_a_save_and_load(self):
        self.supply()
        self.harness.move_unit('Eirika', SITE)
        self.harness.choose('Found')
        self.harness.run_until_state('free')
        before, after = self.harness.round_trip()
        self.assertEqual([], diff_saves(before, after))
        self.assertEqual(OUTPOST, self.game.get_city_at((4, 4)).center.nid)

    def test_a_generic_unit_cannot_found(self):
        self.team.gold = 0
        self.game.teams.get('enemy').gold = GOLD_COST
        fighter = self.game.get_unit('101')
        give_rations(self.game, fighter)
        give_rations(self.game, fighter)
        action.do(action.Teleport(fighter, FAR_SITE))
        self.assertTrue(city_funcs.can_found_city(fighter))
        self.assertEqual(set(), abilities.FoundAbility.targets(fighter))

    def test_a_supplied_hero_on_open_ground_can_found(self):
        self.supply()
        self.stand_on_site()
        self.assertTrue(city_funcs.can_found_city(self.eirika))

    def test_no_founding_without_the_gold(self):
        self.supply(gold=GOLD_COST - 1)
        self.stand_on_site()
        self.assertFalse(city_funcs.can_found_city(self.eirika))

    def test_no_founding_without_the_food(self):
        self.supply(sacks=1)
        self.stand_on_site()
        self.assertFalse(city_funcs.can_found_city(self.eirika))

    def test_no_founding_where_a_tile_of_the_outpost_would_be_a_wall(self):
        # From where Eirika starts, the outpost would reach down into the wall at (4, 6)
        self.supply()
        self.assertFalse(city_funcs.can_found_city(self.eirika))

    def test_no_founding_within_the_minimum_distance_of_another_city(self):
        self.supply()
        self.stand_on_site()
        # The outpost would end at column 4. This center starts 4 tiles to its right
        add_city(self.game, 'Near', 'enemy', (8, 3))
        self.assertFalse(city_funcs.can_found_city(self.eirika))

    def test_founding_is_allowed_at_exactly_the_minimum_distance(self):
        self.supply()
        self.stand_on_site()
        add_city(self.game, 'Far', 'enemy', (9, 3))
        self.assertTrue(city_funcs.can_found_city(self.eirika))

    def test_a_razed_city_no_longer_keeps_others_away(self):
        self.supply()
        self.stand_on_site()
        near = add_city(self.game, 'Near', 'enemy', (8, 3))
        action.do(action.RazeCity(near))
        self.assertTrue(city_funcs.can_found_city(self.eirika))

    def test_no_founding_on_top_of_another_building(self):
        self.supply()
        self.stand_on_site()
        # A constant the project file does not list is shared by every load of it
        min_distance = DB.constants.get('city_min_distance')
        self.addCleanup(min_distance.set_value, min_distance.value)
        min_distance.set_value(0)
        add_city(self.game, 'Overlap', 'enemy', (4, 4))
        self.assertFalse(city_funcs.can_found_city(self.eirika))

    def test_no_founding_where_the_outpost_would_hang_off_the_map(self):
        self.supply()
        seth = self.game.get_unit('Seth')
        give_rations(self.game, seth)
        give_rations(self.game, seth)
        # The one open tile in the last column
        edge = (self.game.tilemap.width - 1, 5)
        action.do(action.Teleport(seth, edge))
        self.assertFalse(city_funcs.can_found_city(seth))

    def test_undoing_a_founding_takes_the_city_back_off_the_map(self):
        self.supply()
        self.stand_on_site()
        city, outpost = city_funcs.new_outpost_city(self.eirika)
        act = action.FoundCity(city, outpost)
        action.do(act)
        act.reverse()
        self.assertEqual([], self.game.cities)
        self.assertEqual({}, self.game.building_position_index)
        act.execute()
        self.assertIs(city, self.game.get_city_at((4, 4)))


class OutpostRestrictionTests(FoundingTestCase):
    '''An outpost builds only what is marked for it, and drafts nothing'''

    def buildable(self, city) -> list:
        return [building.nid for building in city_funcs.get_buildable_buildings(city)]

    def found_outpost(self):
        self.supply()
        self.stand_on_site()
        return city_funcs.found_city(self.eirika)

    def test_a_founded_city_is_an_outpost(self):
        self.assertTrue(self.found_outpost().is_outpost)

    def test_a_city_with_a_town_hall_is_not_an_outpost(self):
        self.assertFalse(add_city(self.game, 'Capital', 'player', SITE).is_outpost)

    def test_an_outpost_is_offered_only_outpost_buildable_buildings(self):
        self.assertEqual(['Quarry'], self.buildable(self.found_outpost()))

    def test_a_full_city_is_offered_everything(self):
        city = add_city(self.game, 'Capital', 'player', SITE)
        self.assertEqual({'TestFarm', 'Quarry', 'Academy'}, set(self.buildable(city)))

    def test_an_outpost_drafts_nothing_even_with_a_building_that_trains_units(self):
        outpost = self.found_outpost()
        academy = BuildingObject.from_prefab(DB.buildings.get('Academy'))
        action.do(action.AddBuilding(outpost, academy))
        self.assertEqual([], city_funcs.get_draftable_units(outpost))

    def test_a_full_city_drafts_from_the_same_building(self):
        city = add_city(self.game, 'Capital', 'player', SITE)
        academy = BuildingObject.from_prefab(DB.buildings.get('Academy'))
        action.do(action.AddBuilding(city, academy))
        self.assertEqual(['Myrmidon'], [spec['klass'] for spec in city_funcs.get_draftable_units(city)])


class OutpostSiteTests(FoundingTestCase):
    '''RequiresTraversable: an Outpost only stands where its movement type can walk'''

    def can_stand_at(self, anchor) -> bool:
        outpost = BuildingObject.from_prefab(DB.buildings.get(OUTPOST))
        return building_system.target_restrict(outpost, None, anchor)

    def walkable(self, pos) -> bool:
        terrain = DB.terrain.get(self.game.get_terrain_nid(self.game.tilemap, pos))
        return DB.mcost.get_mcost(WALKER, terrain.mtype) < 99

    def anchors(self) -> list:
        tilemap = self.game.tilemap
        return [(x, y) for x in range(tilemap.width - 1) for y in range(tilemap.height - 1)]

    def footprint(self, anchor) -> list:
        return [(anchor[0] + dx, anchor[1] + dy) for dx in range(2) for dy in range(2)]

    def test_it_can_stand_exactly_where_all_four_tiles_are_walkable(self):
        expected = [anchor for anchor in self.anchors()
                    if all(self.walkable(tile) for tile in self.footprint(anchor))]
        allowed = [anchor for anchor in self.anchors() if self.can_stand_at(anchor)]
        self.assertEqual(expected, allowed)
        # The level has both kinds of site, or this proves nothing
        self.assertTrue(allowed)
        self.assertLess(len(allowed), len(self.anchors()))


class BuildingFootprintTerrainTests(FoundingTestCase):
    '''A building's terrain reaches the board on every tile it covers'''

    def setUp(self):
        super().setUp()
        DB.buildings.append(BuildingPrefab('Bastion', 'Bastion', '', WALL_TERRAIN, size=(2, 2)))

    def passable(self, pos) -> bool:
        return self.game.board.get_movement_grid(WALKER).get(pos).reachable

    def test_placing_and_removing_a_two_by_two_building_updates_all_four_tiles(self):
        city = add_city(self.game, 'Home', 'player', (1, 1))
        bastion = BuildingObject.from_prefab(DB.buildings.get('Bastion'))
        bastion.position = FAR_SITE
        tiles = [(11, 7), (12, 7), (11, 8), (12, 8)]
        self.assertTrue(all(self.passable(tile) for tile in tiles))

        act = action.AddBuilding(city, bastion)
        action.do(act)
        self.assertFalse(any(self.passable(tile) for tile in tiles))

        act.reverse()
        self.assertTrue(all(self.passable(tile) for tile in tiles))
