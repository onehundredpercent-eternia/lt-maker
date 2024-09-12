import copy
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple
from app.data.category import CategorizedCatalog
from app.data.database.weapons import WexpGain
from app.data.serialization.dataclass_serialization import dataclass_from_dict
from app.utilities.prefab import Prefab
from app.utilities.typing import NID, NestedPrimitiveDict
from app.utilities import str_utils

class UnitPrefab(Prefab):
    nid: str
    name: Optional[str] = None
    desc: Optional[str] = None
    variant: Optional[str] = None

    level: int = 1
    klass: NID = None

    tags: List[NID] = field(default_factory=list)
    bases: Dict[NID, int] = field(default_factory=dict)
    growths: Dict[NID, int] = field(default_factory=dict)
    stat_cap_modifiers: Dict[NID, int] = field(default_factory=dict)
    starting_items: List[Tuple[NID, bool]] = field(default_factory=list)  # (item_nid, droppable)

    learned_skills: List[List] = field(default_factory=list) # each list is a tuple (level, skill_nid)
    unit_notes: List[Tuple[str, str]] = field(default_factory=list)
    wexp_gain: Dict[NID, WexpGain] = field(default_factory=dict)

    alternate_classes: list = field(default_factory=list)

    portrait_nid: Optional[NID] = None
    affinity: Optional[NID] = None

    fields: List[Tuple[str, str]] = field(default_factory=list) # arbitrary field, allow players to fill out anything they want

    def get_stat_titles(self):
        return ["Bases", "Growths", "Stat Cap Mods"]

    def get_stat_lists(self):
        return [self.bases, self.growths, self.stat_cap_modifiers]

    def get_items(self) -> List[NID]:
        return [i[0] for i in self.starting_items]

    def get_skills(self) -> List[NID]:
        return [i[1] for i in self.learned_skills]

    def replace_item_nid(self, old_nid, new_nid):
        for item in self.starting_items:
            if item[0] == old_nid:
                item[0] = new_nid

    def replace_skill_nid(self, old_nid, new_nid):
        for skill in self.learned_skills:
            if skill[1] == old_nid:
                skill[1] = new_nid

    @classmethod
    def default(cls):
        return cls('0')

class UnitCatalog(CategorizedCatalog[UnitPrefab]):
    datatype = UnitPrefab

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Unit", nids)
        bases = {k: 0 for k in db.stats.keys()}
        growths = {k: 0 for k in db.stats.keys()}
        wexp_gain = {weapon_nid: db.weapons.default(db) for weapon_nid in db.weapons.keys()}
        new_unit = UnitPrefab(nid, name, '', '', 1, db.classes[0].nid,
                              bases=bases, growths=growths, wexp_gain=wexp_gain)
        new_unit.fields = []
        self.append(new_unit)
        return new_unit
