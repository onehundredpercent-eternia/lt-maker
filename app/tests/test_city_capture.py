import unittest

import app.engine.building_component_access as BCA
from app.data.cities import City
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.engine import abilities, action, city_funcs
from app.engine.objects.city import CityObject
from app.map_maker.terrain import Terrain
from app.tests.engine_harness import EngineTestCase, diff_saves
from app.tests.test_change_map_terrain import _PrefabLevelTestCaseMixin
from app.utilities.data import Data

# testing_proj level 0: Eirika (4, 5) and Seth (4, 4) against the generic
# fighters 101 (9, 6) and 102 (8, 6), with O'Neill guarding (10, 8)
LEVEL = '0'

TOWN_HALL = 'TestTownHall'
FARM = 'TestFarm'


def add_building_prefabs():
    '''A 2x2 Town Hall that is a city center, and a plain one tile farm'''
    DB.buildings.append(BuildingPrefab(
        TOWN_HALL, 'Town Hall', '', None, size=(2, 2),
        components=Data([BCA.restore_component(('city_center', None))])))
    DB.buildings.append(BuildingPrefab(FARM, 'Farm', '', None))


def remove_building_prefabs():
    DB.buildings.remove_key(TOWN_HALL)
    DB.buildings.remove_key(FARM)


def add_city(game, nid, team, anchor, farms=()) -> CityObject:
    '''Puts a city on the map as start_level does, centered on a Town Hall at anchor'''
    prefab = City(nid)
    prefab.team = team
    prefab.position = anchor
    prefab.buildings = [[TOWN_HALL, anchor]] + [[FARM, pos] for pos in farms]
    city = CityObject.from_prefab(prefab)
    game.register_city(city)
    for building in city.buildings:
        game.register_building(building)
    game.rebuild_terrain_overrides()
    return city


class CityCenterTests(EngineTestCase):
    '''A city's center is the footprint of its center building, not one tile'''

    def setUp(self):
        super().setUp()
        add_building_prefabs()
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')
        self.city = add_city(self.game, 'Capital', 'enemy', (6, 4))

    def test_every_tile_of_the_town_hall_is_the_city(self):
        for pos in [(6, 4), (7, 4), (6, 5), (7, 5)]:
            self.assertIs(self.city, self.game.get_city_at(pos))

    def test_a_tile_next_to_the_town_hall_is_not_the_city(self):
        for pos in [(5, 4), (8, 5), (6, 3), (7, 6)]:
            self.assertIsNone(self.game.get_city_at(pos))

    def test_influence_spreads_from_the_whole_center(self):
        expected = {(6, 3), (7, 3), (5, 4), (8, 4), (5, 5), (8, 5), (6, 6), (7, 6)}
        self.assertEqual(expected, city_funcs.get_all_influence_positions(self.city))

    def test_a_center_building_is_never_offered_to_build(self):
        # Nothing restricts where the farm goes, so it is offered; the Town Hall is not
        self.city.team = 'player'
        buildable = [building.nid for building in city_funcs.get_buildable_buildings(self.city)]
        self.assertIn(FARM, buildable)
        self.assertNotIn(TOWN_HALL, buildable)

    def test_a_city_without_a_center_building_is_one_tile(self):
        prefab = City('Camp')
        prefab.team = 'enemy'
        prefab.position = (2, 2)
        camp = CityObject.from_prefab(prefab)
        self.game.register_city(camp)
        self.assertIs(camp, self.game.get_city_at((2, 2)))
        self.assertIsNone(self.game.get_city_at((3, 2)))
        self.assertEqual({(2, 1), (1, 2), (3, 2), (2, 3)}, city_funcs.get_all_influence_positions(camp))


class SeizeAndRazeTests(EngineTestCase):
    def setUp(self):
        super().setUp()
        add_building_prefabs()
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')

    def menu_options(self) -> list:
        return [option.get() for option in self.game.state.current_state().menu.options]

    def test_a_hero_on_an_enemy_center_can_seize_or_raze(self):
        add_city(self.game, 'Capital', 'enemy', (6, 4))
        self.harness.move_unit('Eirika', (6, 5))
        self.assertIn('Seize', self.menu_options())
        self.assertIn('Raze', self.menu_options())

    def test_a_hero_beside_the_center_can_do_neither(self):
        add_city(self.game, 'Capital', 'enemy', (6, 3))
        self.harness.move_unit('Eirika', (6, 5))
        self.assertNotIn('Seize', self.menu_options())
        self.assertNotIn('Raze', self.menu_options())

    def test_an_enemy_on_the_center_blocks_both(self):
        # 102 stands on (8, 6), the far corner of this center
        add_city(self.game, 'Capital', 'enemy', (7, 5))
        self.harness.move_unit('Eirika', (7, 5))
        self.assertNotIn('Seize', self.menu_options())
        self.assertNotIn('Raze', self.menu_options())

    def test_your_own_city_cannot_be_taken(self):
        add_city(self.game, 'Home', 'player', (6, 4))
        self.harness.move_unit('Eirika', (6, 5))
        self.assertNotIn('Seize', self.menu_options())
        self.assertNotIn('Raze', self.menu_options())

    def test_a_generic_unit_can_raze_but_not_seize(self):
        # The generic fighter 101 stands on the corner of a player city
        add_city(self.game, 'Home', 'player', (9, 6))
        fighter = self.game.get_unit('101')
        self.assertTrue(fighter.generic)
        self.assertEqual(set(), abilities.SeizeAbility.targets(fighter))
        self.assertEqual({(9, 6)}, abilities.RazeAbility.targets(fighter))

    def test_seizing_hands_the_city_over_and_ends_the_units_turn(self):
        city = add_city(self.game, 'Capital', 'enemy', (6, 4))
        self.harness.move_unit('Eirika', (6, 5))
        self.harness.choose('Seize')
        self.harness.run_until_state('free')
        self.assertEqual('player', city.team)
        self.assertTrue(self.game.get_unit('Eirika').finished)
        before, after = self.harness.round_trip()
        self.assertEqual([], diff_saves(before, after))
        self.assertEqual('player', self.game.get_city('Capital').team)

    def test_seizing_can_be_reversed(self):
        city = add_city(self.game, 'Capital', 'enemy', (6, 4))
        act = action.ChangeCityTeam(city, 'player')
        action.do(act)
        act.reverse()
        self.assertEqual('enemy', city.team)

    def test_razing_takes_the_city_and_its_buildings_off_the_map(self):
        city = add_city(self.game, 'Capital', 'enemy', (6, 4), farms=[(5, 4)])
        self.harness.move_unit('Eirika', (6, 5))
        self.harness.choose('Raze')
        self.harness.run_until_state('free')
        self.assertTrue(city.razed)
        self.assertEqual([], city.buildings)
        self.assertNotIn(city, self.game.cities)
        self.assertIsNone(self.game.get_city_at((6, 4)))
        self.assertEqual({}, self.game.building_position_index)
        self.assertTrue(self.game.get_unit('Eirika').finished)
        # Anything that held the city can still find it
        self.assertIs(city, self.game.get_city('Capital'))

    def test_a_razed_city_survives_a_save_and_load(self):
        add_city(self.game, 'Capital', 'enemy', (6, 4), farms=[(5, 4)])
        self.harness.move_unit('Eirika', (6, 5))
        self.harness.choose('Raze')
        self.harness.run_until_state('free')
        before, after = self.harness.round_trip()
        self.assertEqual([], diff_saves(before, after))
        self.assertTrue(self.game.get_city('Capital').razed)
        self.assertEqual([], self.game.cities)

    def test_reversing_a_raze_puts_everything_back_as_it_was(self):
        city = add_city(self.game, 'Capital', 'enemy', (6, 4), farms=[(5, 4), (8, 4)])
        buildings = city.buildings.copy()
        index = self.game.building_position_index.copy()
        act = action.RazeCity(city)
        action.do(act)
        act.reverse()
        self.assertFalse(city.razed)
        self.assertEqual(buildings, city.buildings)
        self.assertEqual(index, self.game.building_position_index)
        self.assertIs(city, self.game.get_city_at((7, 5)))


class RazeRuinsTests(_PrefabLevelTestCaseMixin, unittest.TestCase):
    '''On a map_prefab level, razing leaves ruins behind'''

    LEVEL_NID = 'test_raze_ruins_level'
    MAP_PREFAB_NID = 'test_raze_ruins_map'

    CENTER = [(2, 2), (3, 2), (2, 3), (3, 3)]
    FARM_POS = (0, 3)

    def setUp(self):
        super().setUp()
        add_building_prefabs()
        self.addCleanup(remove_building_prefabs)
        self.addCleanup(DB.constants.get('raze_ruin_chance').set_value,
                        DB.constants.value('raze_ruin_chance'))
        self.city = add_city(self.game, 'Capital', 'enemy', (2, 2), farms=[self.FARM_POS])

    def terrain(self, pos) -> Terrain:
        return self.game.level.tilemap.prefab.get_terrain(pos)

    def raze(self, ruin_chance: int) -> action.RazeCity:
        DB.constants.get('raze_ruin_chance').set_value(ruin_chance)
        act = action.RazeCity(self.city)
        action.do(act)
        return act

    def test_the_center_always_becomes_ruins(self):
        self.raze(0)
        for pos in self.CENTER:
            self.assertEqual(Terrain.RUINS, self.terrain(pos))

    def test_an_outlying_building_that_fails_its_roll_gives_the_tile_back(self):
        self.raze(0)
        self.assertEqual(Terrain.GRASS, self.terrain(self.FARM_POS))

    def test_an_outlying_building_that_passes_its_roll_becomes_ruins(self):
        self.raze(100)
        self.assertEqual(Terrain.RUINS, self.terrain(self.FARM_POS))

    def test_reversing_a_raze_clears_the_ruins(self):
        act = self.raze(100)
        act.reverse()
        for pos in self.CENTER + [self.FARM_POS]:
            self.assertEqual(Terrain.GRASS, self.terrain(pos))
        self.assertEqual(2, len(self.city.buildings))

    def test_redoing_a_raze_ruins_the_same_tiles(self):
        act = self.raze(100)
        act.reverse()
        act.execute()
        for pos in self.CENTER + [self.FARM_POS]:
            self.assertEqual(Terrain.RUINS, self.terrain(pos))
        self.assertTrue(self.city.razed)


if __name__ == '__main__':
    unittest.main()
