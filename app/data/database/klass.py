import copy
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple

from app.data.serialization.dataclass_serialization import dataclass_from_dict
from app.utilities.data import Data
from app.utilities.prefab import Prefab
from app.data.database.weapons import WexpGain
from app.utilities import str_utils
from app.utilities.typing import NID, NestedPrimitiveDict, Point

class Klass(Prefab):
    nid: str = None
    name: str = None

    desc: str = ""
    tier: int = 1
    movement_group: str = None

    promotes_from: str = None           # cllass this class promotes from
    turns_into: List[NID] = None        # List of classes this class can promote
    tags: List[NID] = None              # List of tags
    max_level: int = 20

    bases: Dict[NID, int] = None        # (stat, value)
    growths: Dict[NID, int] = None      # (stat, value)
    growth_bonus: Dict[NID, int] = None # (stat, value)
    promotion: Dict[NID, int] = None    # (stat, value)
    max_stats: Dict[NID, int] = None    # (stat, value)

    learned_skills: List[Tuple[int, NID]] = None # (level, skill_nid)
    wexp_gain: Dict[NID, WexpGain] = None

    icon_nid: str = None
    icon_index: Point = (0, 0)
    map_sprite_nid: str = None
    combat_anim_nid: str = None

    fields: List[Tuple[str, str]] = None # arbitrary field, allow players to fill out anything they want for XTRA POWERFUL SCRIPTING

    def get_stat_titles(self):
        return ['Generic Bases', 'Generic Growths', 'Promotion Gains', 'Growth Bonuses', 'Stat Maximums']

    def get_stat_lists(self):
        return [self.bases, self.growths, self.promotion, self.growth_bonus, self.max_stats]

    def get_skills(self) -> List[NID]:
        return [skill[1] for skill in self.learned_skills]

    def replace_skill_nid(self, old_nid, new_nid):
        for skill in self.learned_skills:
            if skill[1] == old_nid:
                skill[1] = new_nid

    def promotion_options(self, db) -> list:
        return [option for option in self.turns_into if db.classes.get(option).tier == self.tier + 1]

class ClassCatalog(Data[Klass]):
    datatype = Klass

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Class", nids)
        movement_group = db.mcost.unit_types[0]
        bases = {k: 0 for k in db.stats.keys()}
        growths = {k: 0 for k in db.stats.keys()}
        growth_bonus = {k: 0 for k in db.stats.keys()}
        promotion = {k: 0 for k in db.stats.keys()}
        max_stats = {stat.nid: stat.maximum for stat in db.stats}
        wexp_gain = {weapon_nid: db.weapons.default(db) for weapon_nid in db.weapons.keys()}
        new_class = Klass(
            nid, name, "", 1, movement_group, None, [], [], 20,
            bases, growths, growth_bonus, promotion, max_stats,
            [], wexp_gain)
        new_class.fields = []
        self.append(new_class)
        return new_class
