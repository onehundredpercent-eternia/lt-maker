from unittest.mock import patch

import app.engine.building_component_access as BCA
from app.data.cities import City
from app.data.database.buildings import BuildingPrefab
from app.data.database.database import DB
from app.engine import city_funcs, unit_funcs
from app.engine.objects.city import CityObject
from app.tests.engine_harness import EngineTestCase
from app.utilities.data import Data

# testing_proj level 0: Eirika (4, 5) and Seth (4, 4) against the generic
# fighters 101 (9, 6) and 102 (8, 6), with O'Neill guarding (10, 8)
LEVEL = '0'

# Myrmidons carry the Sword tag and start with 4 STR, capped at 20. Dancers carry no tags
SWORD_CLASS = 'Myrmidon'
OTHER_CLASS = 'Dancer'


def add_building_prefab(nid, components):
    DB.buildings.append(BuildingPrefab(
        nid, nid, '', None,
        components=Data([BCA.restore_component(component) for component in components])))


def add_city(game, nid, team, position, building_nids) -> CityObject:
    '''Puts a city on the map as start_level does. Its buildings are not placed'''
    prefab = City(nid)
    prefab.team = team
    prefab.position = position
    prefab.buildings = [[building_nid, None] for building_nid in building_nids]
    city = CityObject.from_prefab(prefab)
    game.register_city(city)
    for building in city.buildings:
        game.register_building(building)
    return city


def draft_spec(klass, level=1) -> dict:
    return {'klass': klass, 'level': level, 'gold_cost': 0, 'food_cost': 0, 'production_cost': 0}


class CityIncomeTests(EngineTestCase):
    '''Every team's cities pay out at the start of that team's phase'''

    def setUp(self):
        super().setUp()
        add_building_prefab('Market', [('resource_per_turn', {'food': 2, 'production': 3, 'gold': 5})])
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')
        self.player_city = add_city(self.game, 'Home', 'player', (2, 2), ['Market'])
        self.enemy_city = add_city(self.game, 'Lair', 'enemy', (12, 2), ['Market'])

    def end_turn(self):
        # A turn does not end itself while the player's city can still buy something
        self.harness.wait('Eirika', (4, 5))
        self.harness.wait('Seth', (4, 4))
        self.harness.end_turn()
        self.harness.run_until_player_turn(2)

    def test_an_enemy_city_collects_income_on_the_enemy_phase(self):
        self.end_turn()
        self.assertEqual(5, self.game.teams.get('enemy').gold)
        self.assertEqual((2, 3), (self.enemy_city.food, self.enemy_city.production))

    def test_a_player_city_still_collects_once_per_turn(self):
        self.end_turn()
        self.assertEqual(5, self.game.teams.get('player').gold)
        self.assertEqual((2, 3), (self.player_city.food, self.player_city.production))

    def test_an_enemy_city_gets_its_purchase_back_each_turn(self):
        city_funcs.mark_purchase(self.enemy_city)
        self.end_turn()
        self.assertFalse(self.enemy_city.produced_this_turn)


class DraftBonusTests(EngineTestCase):
    '''A drafted unit starts with whatever its city's buildings grant'''

    def setUp(self):
        super().setUp()
        add_building_prefab('Barracks', [('level_increase', {'tags': ['Sword'], 'level_increase': 2})])
        add_building_prefab('Forge', [('stat_change', [['STR', 3]])])
        add_building_prefab('Anvil', [('stat_change', [['STR', 2], ['DEF', 1]])])
        add_building_prefab('Colossus', [('stat_change', [['STR', 99]])])
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')

    def draft(self, building_nids, klass=SWORD_CLASS, level=1):
        city = add_city(self.game, 'Home', 'player', (2, 2), building_nids)
        return city_funcs.draft_unit(city, draft_spec(klass, level))

    def test_a_city_with_no_such_buildings_drafts_a_plain_unit(self):
        unit = self.draft([])
        self.assertEqual(1, unit.level)
        self.assertEqual(DB.classes.get(SWORD_CLASS).bases['STR'], unit.stats['STR'])

    def test_a_unit_with_the_tag_starts_at_a_higher_level(self):
        self.assertEqual(3, self.draft(['Barracks']).level)

    def test_the_extra_levels_come_with_level_ups(self):
        with patch.object(unit_funcs, 'auto_level', wraps=unit_funcs.auto_level) as auto_level:
            unit = self.draft(['Barracks'], level=4)
        # The two levels after level 4, on top of the three the unit was built with
        auto_level.assert_called_with(unit, 4, 2)
        self.assertEqual(6, unit.level)

    def test_a_unit_without_the_tag_starts_at_its_own_level(self):
        self.assertEqual(1, self.draft(['Barracks'], klass=OTHER_CLASS).level)

    def test_extra_levels_stop_at_the_class_max_level(self):
        max_level = DB.classes.get(SWORD_CLASS).max_level
        self.assertEqual(max_level, self.draft(['Barracks'], level=max_level - 1).level)

    def test_a_stat_bonus_is_added_to_the_units_stats(self):
        unit = self.draft(['Forge'])
        self.assertEqual(DB.classes.get(SWORD_CLASS).bases['STR'] + 3, unit.stats['STR'])

    def test_stat_bonuses_from_several_buildings_add_up(self):
        klass = DB.classes.get(SWORD_CLASS)
        unit = self.draft(['Forge', 'Anvil'])
        self.assertEqual(klass.bases['STR'] + 5, unit.stats['STR'])
        self.assertEqual(klass.bases['DEF'] + 1, unit.stats['DEF'])

    def test_a_stat_bonus_stops_at_the_class_max_stat(self):
        unit = self.draft(['Colossus'])
        self.assertEqual(DB.classes.get(SWORD_CLASS).max_stats['STR'], unit.stats['STR'])
