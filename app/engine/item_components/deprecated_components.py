
from __future__ import annotations

from app.data.components import Type
from app.data.item_components import ItemComponent, ItemTags
from app.engine.game_state import game


class EvalTargetRestrict(ItemComponent):
    nid = 'eval_target_restrict'
    desc = "Use this to restrict what units can be targeted"
    tag = ItemTags.DEPRECATED

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
