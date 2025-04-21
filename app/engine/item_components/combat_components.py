from app.data.database.item_components import ItemComponent, ItemTags
from app.data.database.components import ComponentType

import logging

class DynamicStagger(ItemComponent):
    nid = 'dynamic_stagger'
    desc = "Gives +X stagger solved dynamically"
    tag = ItemTags.DYNAMIC

    expose = ComponentType.String

    def dynamic_stagger(self, unit, item, target, item2, mode, attack_info, base_value) -> int:
        from app.engine import evaluate
        try:
            local_args = {'item': item, 'item2': item2, 'mode': mode, 'skill': self.skill, 'attack_info': attack_info, 'base_value': base_value}
            return int(evaluate.evaluate(self.value, unit, target, unit.position, local_args))
        except Exception as e:
            logging.error("Couldn't evaluate %s conditional (%s)", self.value, e)
            return 0
