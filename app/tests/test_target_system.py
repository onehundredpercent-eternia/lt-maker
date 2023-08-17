import unittest
from unittest.mock import MagicMock, patch, call
from app.data.resources.resources import RESOURCES
from app.engine.item_components.base_components import Weapon
from app.engine.item_components.target_components import EvalSpecialRange, MaximumRange, MinimumRange, TargetsEnemies
from app.engine.objects.item import ItemObject
from app.engine.game_board import GameBoard
from app.engine.objects.tilemap import TileMapObject

from app.engine.target_system import TargetSystem
from app.tests.mocks.mock_game import get_mock_game
from app.engine.objects.unit import UnitObject

class TargetSystemUnitTests(unittest.TestCase):
    def setUp(self):
        from app.data.database.database import DB
        DB.load('testing_proj.ltproj')
        from app.engine import equations
        equations.clear()
        self.game = get_mock_game()
        self.target_system = self.create_target_system()

        self.game.board = GameBoard(MagicMock())

        self.player_unit = UnitObject.from_prefab(DB.units.get("Eirika"))                # eirika, prefab
        self.player_unit.team = 'player'
        self.player_weapon = self.mock_iron_sword(item=DB.items.get("Iron Sword"))
        self.range_restrict_weapon = self.mock_range_restrict_sword(item=DB.items.get("Iron Sword"))

        self.ally_unit = UnitObject.from_prefab(DB.units.get("Seth"))                # Seth, prefab
        self.ally_unit.team = 'player'

        self.enemy_unit = UnitObject.from_prefab(DB.units.get("Bone"))                # Bone, prefab
        self.enemy_unit.team = 'enemy'

    def mock_iron_sword(self, item):
        sword = ItemObject.from_prefab(item)
        sword.components = [Weapon(game=self.game), TargetsEnemies(game=self.game), MinimumRange(value=1, game=self.game), MaximumRange(value=1, game=self.game)]
        return sword

    def mock_range_restrict_sword(self, item):
        sword = ItemObject.from_prefab(item)
        sword.components = [Weapon(game=self.game), TargetsEnemies(game=self.game), \
                            MinimumRange(value=1, game=self.game), MaximumRange(value=1, game=self.game), \
                            EvalSpecialRange(value='y == 0')]
        return sword

    def create_target_system(self):
        return TargetSystem(game=self.game)
    
    def test_targets_in_range_adjacent(self):
        '''
        An adjacent enemy should be a valid target
        '''
        self.player_unit.position = (0, 0)
        self.enemy_unit.position = (0, 1)
        self.game.units.append(self.player_unit)
        self.game.units.append(self.enemy_unit)
        self.assertEqual(len(self.target_system.targets_in_range(self.player_unit, self.player_weapon)), 1)

    def test_targets_in_range_adjacent_ally(self):
        '''
        An adjacent ally is not a valid target to attack
        '''
        self.player_unit.position = (0, 0)
        self.ally_unit.position = (0, 1)
        self.game.units.append(self.player_unit)
        self.game.units.append(self.ally_unit)
        self.assertEqual(len(self.target_system.targets_in_range(self.player_unit, self.player_weapon)), 0)

    def test_targets_in_range_too_far(self):
        '''
        This enemy is too far from the player's position
        '''
        self.player_unit.position = (0, 0)
        self.enemy_unit.position = (0, 3)
        self.game.units.append(self.player_unit)
        self.game.units.append(self.enemy_unit)
        self.assertEqual(len(self.target_system.targets_in_range(self.player_unit, self.player_weapon)), 0)

    def _setup_board(self) -> list:
        valid_moves = [(0, 2), (1, 1), (0, 1), (0, 0)]
        self.game.board.height
        self.game.board.unit_grid = [[self.player_unit], [self.enemy_unit], [], [], [], []]
        self.game.board.team_grid = [['player'], ['enemy'], [], [], [], []]
        self.game.board.height = 3
        return valid_moves

    def test_get_possible_attack_positions(self):
        self.player_unit.position = (0, 0)
        self.enemy_unit.position = (0, 1)
        self.game.units.append(self.player_unit)
        self.game.units.append(self.enemy_unit)

        valid_moves = self._setup_board()

        self.assertEqual(len(self.target_system.get_possible_attack_positions(self.player_unit, (0, 1), valid_moves, self.player_weapon)), 3)

    def test_get_possible_attack_positions_range_restrict(self):
        self.player_unit.position = (0, 0)
        self.enemy_unit.position = (0, 1)
        self.game.units.append(self.player_unit)
        self.game.units.append(self.enemy_unit)

        valid_moves = self._setup_board()

        self.assertEqual(len(self.target_system.get_possible_attack_positions(self.player_unit, (0, 1), valid_moves, self.range_restrict_weapon)), 1)


if __name__ == '__main__':
    unittest.main()