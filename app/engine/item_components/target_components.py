from __future__ import annotations

import logging
from functools import lru_cache

from app.data.components import Type
from app.data.item_components import ItemComponent
from app.engine import item_funcs, skill_system, target_system
from app.engine.game_state import game
from app.utilities import utils


class TargetsAnything(ItemComponent):
    nid = 'target_tile'
    desc = "Item targets any tile"
    tag = 'target'

    def ai_targets(self, unit, item) -> set:
        return {(x, y) for x in range(game.tilemap.width) for y in range(game.tilemap.height)}

    def valid_targets(self, unit, item) -> set:
        rng = item_funcs.get_range(unit, item)
        positions = target_system.find_manhattan_spheres(rng, *unit.position)
        return {pos for pos in positions if game.tilemap.check_bounds(pos)}

class TargetsUnits(ItemComponent):
    nid = 'target_unit'
    desc = "Item targets any unit"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position}
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class TargetsEnemies(ItemComponent):
    nid = 'target_enemy'
    desc = "Item targets any enemy"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position and
                skill_system.check_enemy(unit, other)}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position and
                   skill_system.check_enemy(unit, other)}
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class TargetsAllies(ItemComponent):
    nid = 'target_ally'
    desc = "Item targets any ally"
    tag = 'target'

    def ai_targets(self, unit, item):
        return {other.position for other in game.units if other.position and
                skill_system.check_ally(unit, other)}

    def valid_targets(self, unit, item) -> set:
        targets = {other.position for other in game.units if other.position and
                   skill_system.check_ally(unit, other)}
        return {t for t in targets if utils.calculate_distance(unit.position, t) in item_funcs.get_range(unit, item)}

class EvalSpecialRange(ItemComponent):
    nid = 'eval_special_range'
    desc = "Use this to restrict range to specific tiles around the unit"
    tag = 'target'

    expose = Type.String
    value = ''

    # if the range is large, the calculation will be large; let's not repeat this more than necessary.
    # luckily, the calculation is trivial.
    @staticmethod
    @lru_cache(maxsize=None)
    def calculate_range_restrict(condition, max_rng):
        valid_range_squares = set()
        try:
            # neat performance trick
            cond_as_func = eval('lambda x, y:' + condition)
            for x in range(-max_rng, max_rng+1):
                for y in range(-max_rng, max_rng+1):
                    if cond_as_func(x, y):
                        valid_range_squares.add((x, y))
        except Exception as e:
            logging.error("eval_special_range failed for condition %s with error %s", condition, str(e))
        return valid_range_squares

    def range_restrict(self, unit, item):
        rng = item_funcs.get_range(unit, item)
        return EvalSpecialRange.calculate_range_restrict(self.value, max(rng))

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        net_pos = (def_pos[0] - unit.position[0], def_pos[1] - unit.position[1])
        range_restriction = self.range_restrict(unit, item)
        if net_pos in range_restriction:
            return True
        return False

class EvalTargetRestrict(ItemComponent):
    nid = 'eval_target_restrict'
    desc = "Use this to restrict what units can be targeted"
    tag = 'target'

    expose = Type.String
    value = 'True'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        from app.engine import evaluate
        try:
            target = game.board.get_unit(def_pos)
            if target and evaluate.evaluate(self.value, target, position=def_pos):
                return True
            for s_pos in splash:
                target = game.board.get_unit(s_pos)
                if evaluate.evaluate(self.value, target, position=s_pos):
                    return True
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return True
        return False

    def simple_target_restrict(self, unit, item):
        from app.engine import evaluate
        try:
            if evaluate.evaluate(self.value, unit):
                return True
        except Exception as e:
            print("Could not evaluate %s (%s)" % (self.value, e))
            return True
        return False

class EmptyTileTargetRestrict(ItemComponent):
    nid = 'empty_tile_target_restrict'
    desc = "Item will only target tiles without units on them"
    tag = 'target'

    def target_restrict(self, unit, item, def_pos, splash) -> bool:
        if not game.board.get_unit(def_pos):
            return True
        return False

class MinimumRange(ItemComponent):
    nid = 'min_range'
    desc = "Set the minimum_range of the item to an integer"
    tag = 'target'

    expose = Type.Int
    value = 0

    def minimum_range(self, unit, item) -> int:
        return self.value

class MaximumRange(ItemComponent):
    nid = 'max_range'
    desc = "Set the maximum_range of the item to an integer"
    tag = 'target'

    expose = Type.Int
    value = 0

    def maximum_range(self, unit, item) -> int:
        return self.value

class MaximumEquationRange(ItemComponent):
    nid = 'max_equation_range'
    desc = "Set the maximum_range of the item to an equation"
    tag = 'target'

    expose = Type.Equation

    def maximum_range(self, unit, item) -> int:
        from app.engine import equations
        if unit:
            value = equations.parser.get(self.value, unit)
            return int(value)
        else:
            return -1

class GlobalRange(ItemComponent):
    nid = 'global_range'
    desc = "Item has no maximum range"
    tag = 'target'

    def maximum_range(self, unit, item) -> int:
        return 99
