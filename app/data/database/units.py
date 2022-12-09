from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from app.data.database.weapons import WexpGain
from app.utilities.data import Data, Prefab
from app.utilities.typing import NID


@dataclass
class UnitPrefab(Prefab):
    nid: str
    name: Optional[str] = None
    desc: Optional[str] = None
    variant: Optional[str] = None

    level: int = 1
    klass: str = None

    tags: List[NID] = field(default_factory=list)
    bases: Dict[NID, int] = field(default_factory=dict)
    growths: Dict[NID, int] = field(default_factory=dict)
    starting_items: List[Tuple[NID, bool]] = field(default_factory=list)  # of tuples (item_nid, droppable)

    learned_skills: List[Tuple[int, NID]] = field(default_factory=list) # tuples (level, skill_nid)
    unit_notes: list = field(default_factory=list)
    wexp_gain: Dict[NID, WexpGain] = field(default_factory=dict)

    alternate_classes: list = field(default_factory=list)

    portrait_nid: Optional[NID] = None
    affinity: Optional[NID] = None

    fields: list = field(default_factory=list) # arbitrary field, allow players to fill out anything they want

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
                item = new_nid, item[1]

    def replace_skill_nid(self, old_nid, new_nid):
        for skill in self.learned_skills:
            if skill[1] == old_nid:
                skill = skill[0], new_nid

    def save_attr(self, name, value):
        if name in ('bases', 'growths'):
            return value.copy()  # So we don't make a copy
        elif name == 'learned_skills':
            return [val.copy() for val in value]  # So we don't make a copy
        elif name == 'unit_notes':
            return [val.copy() for val in value]
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

    @classmethod
    def default(cls):
        return cls('0')

class UnitCatalog(Data[UnitPrefab]):
    datatype = UnitPrefab