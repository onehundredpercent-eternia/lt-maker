import unittest
from unittest.mock import patch

from app.engine import action, city_funcs
from app.engine import config as cf
from app.tests.engine_harness import EngineTestCase
from app.tests.test_city_capture import add_building_prefabs, add_city

# testing_proj level 0: Eirika (4, 5) and Seth (4, 4) against the generic
# fighters 101 (9, 6) and 102 (8, 6), with O'Neill guarding (10, 8)
LEVEL = '0'
CITY = (11, 7)


class TurnTestCase(EngineTestCase):
    def setUp(self):
        super().setUp()
        cf.SETTINGS['autoend_turn'] = 1
        add_building_prefabs()
        self.harness = self.start_harness()
        self.game = self.harness.start_level(LEVEL)
        self.harness.run_until_state('free')

    def remove_player_units(self):
        self.remove_units('player')

    def remove_units(self, team):
        for unit in self.game.get_team_units(team):
            action.do(action.LeaveMap(unit))

    def finish_player_units(self):
        for unit in self.game.get_player_units():
            action.do(action.Wait(unit))
        # Coming back to the free state is what looks for a finished turn
        self.game.state.change('free')

    def teams_that_ran_upkeep(self, until_turn) -> list:
        '''The teams whose cities collected income on the way to until_turn'''
        with patch.object(city_funcs, 'run_all_city_upkeeps', wraps=city_funcs.run_all_city_upkeeps) as upkeeps:
            self.harness.run_until_player_turn(until_turn)
        return [call.args[0] for call in upkeeps.call_args_list]

    def end_turn(self):
        self.harness.end_turn()


class TurnWithoutUnitsTests(TurnTestCase):
    '''A player with nothing on the map still has cities to run, so their turn is
    theirs to end'''

    def test_the_turn_ends_itself_once_every_unit_has_acted(self):
        self.finish_player_units()
        self.harness.run_until_player_turn(2)

    def test_the_turn_does_not_end_itself_when_the_player_has_no_units(self):
        self.remove_player_units()
        self.end_turn()
        self.harness.run_until_player_turn(2)
        self.harness.step(300)
        self.assertEqual(2, self.game.turncount)
        self.assertEqual('player', self.game.phase.get_current())
        self.assertEqual('free', self.harness.state)

    def test_a_player_with_no_units_can_still_open_their_city(self):
        add_city(self.game, 'Capital', 'player', CITY)
        self.remove_player_units()
        self.end_turn()
        self.harness.run_until_player_turn(2)
        self.harness.move_cursor_to(CITY)
        self.harness.press('AUX')
        self.harness.run_until_state('city_menu')

    def test_a_player_with_no_units_can_end_the_turn_themselves(self):
        self.remove_player_units()
        self.end_turn()
        self.harness.run_until_player_turn(2)
        self.end_turn()
        self.harness.run_until_player_turn(3)


class TurnWithCitiesTests(TurnTestCase):
    '''A city is a reason to have a turn, for the player and for everyone else'''

    def test_the_turn_waits_for_a_city_that_has_not_bought_anything(self):
        add_city(self.game, 'Capital', 'player', CITY)
        self.finish_player_units()
        self.harness.step(300)
        self.assertEqual(1, self.game.turncount)
        self.assertEqual('free', self.harness.state)

    def test_the_turn_ends_itself_once_the_city_has_bought_as_well(self):
        city = add_city(self.game, 'Capital', 'player', CITY)
        city_funcs.mark_purchase(city)
        self.finish_player_units()
        self.harness.run_until_player_turn(2)

    def test_another_teams_city_does_not_hold_up_the_players_turn(self):
        add_city(self.game, 'Stronghold', 'enemy', CITY)
        self.finish_player_units()
        self.harness.run_until_player_turn(2)

    def test_a_team_with_a_city_and_no_units_still_takes_its_phase(self):
        add_city(self.game, 'Stronghold', 'enemy', CITY)
        self.remove_units('enemy')
        self.end_turn()
        self.assertEqual(['enemy', 'player'], self.teams_that_ran_upkeep(until_turn=2))

    def test_a_team_with_no_city_and_no_units_is_passed_over(self):
        self.remove_units('enemy')
        self.end_turn()
        self.assertEqual(['player'], self.teams_that_ran_upkeep(until_turn=2))

    def test_a_razed_city_is_no_reason_to_take_a_phase(self):
        city = add_city(self.game, 'Stronghold', 'enemy', CITY)
        action.do(action.RazeCity(city))
        self.remove_units('enemy')
        self.end_turn()
        self.assertEqual(['player'], self.teams_that_ran_upkeep(until_turn=2))

    def test_cities_alone_keep_the_turns_going(self):
        # Nobody has a unit on the map: the player and the enemy each hold a city
        add_city(self.game, 'Capital', 'player', (3, 3))
        add_city(self.game, 'Stronghold', 'enemy', CITY)
        self.remove_units('player')
        self.remove_units('enemy')
        self.end_turn()
        self.assertEqual(['enemy', 'player'], self.teams_that_ran_upkeep(until_turn=2))


if __name__ == '__main__':
    unittest.main()
