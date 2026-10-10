from unittest.mock import patch

import app.engine.building_component_access as BCA
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.engine import action, building_sprite, city_funcs
from app.tests.engine_harness import diff_saves
from app.tests.test_city_capture import FARM, TOWN_HALL, add_city
from app.tests.test_city_founding import (FAR_SITE, OUTPOST, SITE, SITE_TILES,
                                          WALL_TERRAIN, FoundingTestCase)
from app.utilities.data import Data

GOLD_COST = 150
FOOD_COST = 50


class UpgradeTestCase(FoundingTestCase):
    '''Eirika's team owns an outpost on SITE that can become a Town Hall for a price'''

    def setUp(self):
        super().setUp()
        DB.buildings.get(OUTPOST).components.append(
            BCA.restore_component(('upgrades_to', [TOWN_HALL])))
        DB.buildings.get(TOWN_HALL).components.append(
            BCA.restore_component(('cost', {'base_gold_cost': GOLD_COST, 'base_food_cost': FOOD_COST})))
        self.stand_on_site()
        self.supply()
        self.city = city_funcs.found_city(self.eirika)
        self.outpost = self.city.center

    def stock(self, gold=GOLD_COST, food=FOOD_COST):
        '''Enough to pay for the upgrade, unless told otherwise'''
        self.team.gold = gold
        self.city.food = food

    def the_upgrade(self) -> city_funcs.BuildingUpgrade:
        upgrades = city_funcs.get_building_upgrades(self.city)
        self.assertEqual(1, len(upgrades))
        return upgrades[0]


class BuildingUpgradeTests(UpgradeTestCase):
    def test_an_outpost_is_offered_its_upgrade_to_a_town_hall(self):
        upgrade = self.the_upgrade()
        self.assertIs(self.outpost, upgrade.old)
        self.assertEqual(TOWN_HALL, upgrade.new.nid)
        self.assertEqual(SITE, upgrade.new.position)
        self.assertEqual((GOLD_COST, FOOD_COST, 0), city_funcs.get_building_cost(upgrade.new, self.city))

    def test_a_city_with_a_town_hall_is_offered_no_upgrade(self):
        capital = add_city(self.game, 'Capital', 'player', FAR_SITE)
        self.assertEqual([], city_funcs.get_building_upgrades(capital))

    def test_an_upgrade_to_a_tech_locked_building_is_not_offered(self):
        with patch.object(city_funcs, '_tech_gated_values', return_value={TOWN_HALL}):
            self.assertEqual([], city_funcs.get_building_upgrades(self.city))

    def test_upgrading_makes_the_outpost_a_full_city_on_the_same_tiles(self):
        upgrade = self.the_upgrade()
        city_funcs.upgrade_building(self.city, upgrade)
        self.assertFalse(self.city.is_outpost)
        self.assertIs(upgrade.new, self.city.center)
        self.assertEqual(SITE_TILES, set(self.city.center_positions))
        self.assertNotIn(self.outpost, self.city.buildings)
        for tile in SITE_TILES:
            self.assertIs(upgrade.new, self.game.get_building_at(tile))
            self.assertIs(self.city, self.game.get_city_at(tile))

    def test_the_new_building_takes_the_old_ones_place_in_the_citys_order(self):
        farm = city_funcs.get_buildable_buildings(self.city)[0]
        farm.position = (5, 3)
        action.do(action.AddBuilding(self.city, farm))
        upgrade = self.the_upgrade()
        city_funcs.upgrade_building(self.city, upgrade)
        self.assertEqual([upgrade.new, farm], self.city.buildings)

    def test_turning_back_an_upgrade_puts_the_outpost_back_where_it_was(self):
        farm = city_funcs.get_buildable_buildings(self.city)[0]
        farm.position = (5, 3)
        action.do(action.AddBuilding(self.city, farm))
        index = self.game.building_position_index.copy()
        act = action.UpgradeBuilding(self.city, *self.the_upgrade())
        action.do(act)
        act.reverse()
        self.assertTrue(self.city.is_outpost)
        self.assertEqual([self.outpost, farm], self.city.buildings)
        self.assertEqual(index, self.game.building_position_index)

    def test_redoing_an_upgrade_makes_the_same_city(self):
        upgrade = self.the_upgrade()
        act = action.UpgradeBuilding(self.city, *upgrade)
        action.do(act)
        act.reverse()
        act.execute()
        self.assertEqual([upgrade.new], self.city.buildings)
        self.assertFalse(self.city.is_outpost)

    def test_an_upgrade_fits_where_the_outpost_stands(self):
        self.assertTrue(city_funcs.upgrade_fits(self.city, self.the_upgrade()))

    def test_an_upgrade_does_not_fit_on_ground_the_new_building_refuses(self):
        # SITE is not wall terrain, so a Town Hall that asks for it cannot stand there
        DB.buildings.get(TOWN_HALL).components.append(
            BCA.restore_component(('requires_terrain', [WALL_TERRAIN])))
        self.assertFalse(city_funcs.upgrade_fits(self.city, self.the_upgrade()))

    def test_a_bigger_upgrade_does_not_fit_over_a_neighboring_building(self):
        DB.buildings.get(TOWN_HALL).size = (3, 2)
        self.assertTrue(city_funcs.upgrade_fits(self.city, self.the_upgrade()))
        farm = city_funcs.get_buildable_buildings(self.city)[0]
        farm.position = (5, 3)
        action.do(action.AddBuilding(self.city, farm))
        self.assertFalse(city_funcs.upgrade_fits(self.city, self.the_upgrade()))

    def test_a_bigger_upgrade_does_not_fit_off_the_map(self):
        DB.buildings.get(TOWN_HALL).size = (2, 20)
        self.assertFalse(city_funcs.upgrade_fits(self.city, self.the_upgrade()))


class ManageTabTests(UpgradeTestCase):
    '''The third tab of the city menu, opened with AUX over the outpost'''

    def open_manage_tab(self):
        self.harness.move_cursor_to(SITE)
        self.harness.press('AUX')
        self.harness.run_until_state('city_menu')
        self.menu = self.game.state.current_state().menu
        self.harness.press('RIGHT')
        self.harness.press('RIGHT')
        self.assertEqual('Manage', self.menu.current_tab)

    def test_the_outposts_manage_tab_lists_the_upgrade(self):
        self.stock()
        self.open_manage_tab()
        upgrade = self.menu.get_current()
        self.assertIsInstance(upgrade, city_funcs.BuildingUpgrade)
        self.assertEqual(TOWN_HALL, upgrade.new.nid)

    def test_a_full_citys_manage_tab_is_empty(self):
        add_city(self.game, 'Capital', 'player', FAR_SITE)
        self.harness.move_cursor_to(FAR_SITE)
        self.harness.press('AUX')
        self.harness.run_until_state('city_menu')
        menu = self.game.state.current_state().menu
        self.harness.press('RIGHT')
        self.harness.press('RIGHT')
        self.assertEqual('Manage', menu.current_tab)
        self.assertIsNone(menu.get_current())
        # Selecting nothing does nothing
        self.harness.press('SELECT')
        self.assertEqual('city_menu', self.harness.state)

    def test_buying_the_upgrade_charges_the_city_and_uses_its_purchase(self):
        self.stock(gold=GOLD_COST + 30, food=FOOD_COST + 5)
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertFalse(self.city.is_outpost)
        self.assertEqual(TOWN_HALL, self.city.center.nid)
        self.assertEqual(30, self.team.gold)
        self.assertEqual(5, self.city.food)
        self.assertTrue(self.city.produced_this_turn)
        # A Town Hall has nothing further to become
        self.assertIsNone(self.menu.get_current())

    def test_an_upgraded_city_survives_a_save_and_load(self):
        self.stock()
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.harness.press('BACK')
        self.harness.run_until_state('free')
        before, after = self.harness.round_trip()
        self.assertEqual([], diff_saves(before, after))
        city = self.game.get_city(self.city.nid)
        self.assertFalse(city.is_outpost)
        self.assertEqual(SITE_TILES, set(city.center_positions))

    def test_the_upgrade_cannot_be_bought_without_the_gold(self):
        self.stock(gold=GOLD_COST - 1)
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertTrue(self.city.is_outpost)
        self.assertEqual(GOLD_COST - 1, self.team.gold)

    def test_the_upgrade_cannot_be_bought_without_the_food(self):
        self.stock(food=FOOD_COST - 1)
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertTrue(self.city.is_outpost)
        self.assertEqual(FOOD_COST - 1, self.city.food)

    def test_the_upgrade_cannot_be_bought_once_the_city_has_bought_this_turn(self):
        self.stock()
        city_funcs.mark_purchase(self.city)
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertTrue(self.city.is_outpost)
        self.assertEqual(GOLD_COST, self.team.gold)

    def test_the_upgrade_cannot_be_bought_where_it_does_not_fit(self):
        DB.buildings.get(TOWN_HALL).components.append(
            BCA.restore_component(('requires_terrain', [WALL_TERRAIN])))
        self.stock()
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertTrue(self.city.is_outpost)
        self.assertEqual(GOLD_COST, self.team.gold)

    def test_after_upgrading_the_city_builds_what_an_outpost_could_not(self):
        DB.buildings.append(BuildingPrefab('Hall', 'Hall', '', None, components=Data()))
        self.assertNotIn('Hall', [b.nid for b in city_funcs.get_buildable_buildings(self.city)])
        self.stock()
        self.open_manage_tab()
        self.harness.press('SELECT')
        self.assertIn('Hall', [b.nid for b in city_funcs.get_buildable_buildings(self.city)])
        self.assertIn(FARM, [b.nid for b in city_funcs.get_buildable_buildings(self.city)])


class BuildingsOnTheMapTests(UpgradeTestCase):
    '''A building that has left its city stays registered, with its position, and must
    no longer be drawn'''

    def drawn_buildings(self) -> list:
        drawn = []
        with patch.object(building_sprite, 'get_building_sprite', side_effect=drawn.append):
            self.harness.step()
        return drawn

    def test_a_citys_buildings_are_drawn(self):
        self.assertEqual([self.outpost], self.drawn_buildings())

    def test_after_an_upgrade_only_the_new_building_is_drawn(self):
        upgrade = self.the_upgrade()
        city_funcs.upgrade_building(self.city, upgrade)
        self.assertEqual(SITE, self.outpost.position)
        self.assertIs(self.outpost, self.game.get_building(self.outpost.uid))
        self.assertEqual([upgrade.new], self.drawn_buildings())

    def test_only_the_new_building_is_drawn_after_a_save_and_load(self):
        upgrade = self.the_upgrade()
        city_funcs.upgrade_building(self.city, upgrade)
        self.harness.round_trip()
        self.harness.run_until_state('free')
        self.assertEqual([TOWN_HALL], [building.nid for building in self.drawn_buildings()])

    def test_a_removed_building_is_not_drawn(self):
        action.do(action.RemoveBuilding(self.city, self.outpost))
        self.assertEqual([], self.drawn_buildings())

    def test_a_razed_citys_buildings_are_not_drawn(self):
        action.do(action.RazeCity(self.city))
        self.assertEqual([], self.drawn_buildings())
