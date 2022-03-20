from app.data.item_components import ItemComponent, ItemTags

class NoAI(ItemComponent):
    nid = 'no_ai'
    desc = "Item cannot be used by the AI"
    tag = ItemTags.BASE

    def ai_priority(self, unit, item, target, move):
        return -1

    def ai_targets(self, unit, item) -> set:
        return set()
