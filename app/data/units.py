from dataclasses import dataclass
from typing import Dict

from app.data.weapons import WexpGain
from app.utilities.data import Data, Prefab


@dataclass
class UnitPrefab(Prefab):
    def __init__(self) -> None:
        self.nid: str = None
        self.name: str = None
        self.desc: str = None
        self.variant: str = None

        self.level: int = None
        self.klass: str = None

        self.tags: list = None
        self.bases: dict = None
        self.growths: dict = None
        self.starting_items: list = None  # of tuples (ItemPrefab, droppable)

        self.learned_skills: list = None
        self.unit_notes: list = None
        self.wexp_gain: dict = None

        self.alternate_classes: list = None

        self.portrait_nid: str = None
        self.affinity: str = None

        self.fields: list = None # arbitrary field, allow players to fill out anything they want

    def get_stat_titles(self):
        return ["Bases", "Growths"]

    def get_stat_lists(self):
        return [self.bases, self.growths]

    def get_items(self):
        return [i[0] for i in self.starting_items]

    def get_skills(self):
        return [i[1] for i in self.learned_skills]

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def replace_skill_nid(self, old_nid, new_nid):
        for skill in self.learned_skills:
            if skill[1] == old_nid:
                skill[1] = new_nid

    def save_attr(self, name, value):
        if name in ('bases', 'growths'):
            return value.copy()  # So we don't make a copy
        elif name == 'learned_skills':
            return [val.copy() for val in value]  # So we don't make a copy
        elif name == 'wexp_gain':
            return {k: v.save() for (k, v) in self.wexp_gain.items()}
        else:
            return super().save_attr(name, value)

    def restore_attr(self, name, value):
        if name in ('bases', 'growths'):
            if isinstance(value, list):
                value = {k: v for (k, v) in value}
            else:
                value = value.copy()  # Should be copy so units don't share lists/dicts
        elif name == 'wexp_gain':
            if isinstance(value, list):
                value = {nid: WexpGain(usable, wexp_gain) for (usable, nid, wexp_gain) in value}
            else:
                value = {k: WexpGain(usable, wexp_gain) for (k, (usable, wexp_gain)) in value.items()}
        elif name == 'starting_items':
            # Need to convert to item nid + droppable
            value = [i if isinstance(i, list) else [i, False] for i in value]
        elif name == 'unit_notes' or name == 'fields':
            if value is None:
                value = []
        else:
            value = super().restore_attr(name, value)
        return value

class UnitCatalog(Data[UnitPrefab]):
    datatype = UnitPrefab
