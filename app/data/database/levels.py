from __future__ import annotations
from app.utilities.typing import NID
from collections import OrderedDict
from typing import Optional, Union

from app.data.database.level_units import GenericUnit, UniqueUnit, UnitGroup
from app.data.database.ai_groups import AIGroup
from app.events.regions import Region
from app.data.cities import City
from app.utilities.data import Data, Prefab

OBJECTIVE_KEYS = ['simple', 'win', 'loss']

class LevelPrefab(Prefab):
    def __init__(self, nid, name):
        self.nid = nid
        self.name = name
        self.tilemap: Optional[NID] = None  # Tilemap Nid
        self.bg_tilemap: Optional[NID] = None  # bg tilemap nid
        self.party: NID = None  # Party Prefab Nid
        self.music = OrderedDict()

        self.objective = {key: '' for key in OBJECTIVE_KEYS}
        self.roam: bool = False
        self.roam_unit: NID = None

        self.go_to_overworld: bool = False
        self.should_record: bool = True
        self.tags: list = []

        self.units = Data[Union[UniqueUnit, GenericUnit]]()
        self.regions = Data[Region]()
        self.cities = Data[City]()
        self.unit_groups = Data[UnitGroup]()
        self.ai_groups = Data[AIGroup]()  # Each AI Group is Level Specific

    def save_attr(self, name, value):
        if name in ['units', 'unit_groups', 'regions', 'cities', 'ai_groups']:
            value = [v.save() for v in value]
        elif name == 'objective':
            value = value.copy()  # Must make a copy so we don't keep a reference to the same one
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'units':
            value = Data([GenericUnit.restore(unit_data) if unit_data['generic']
                          else UniqueUnit.restore(unit_data) for unit_data in value])
        elif name == 'unit_groups':
            value = Data([UnitGroup.restore(val) for val in value])
        elif name == 'regions':
            value = Data([Region.restore(val) for val in value])
        elif name == 'cities':
            value = Data([City.restore(val) for val in value])
        elif name == 'music':
            value = {k: value.get(k) for k in value.keys()}
        elif name == 'ai_groups':
            if value:
                value = Data([AIGroup.restore(val) for val in value])
            else:
                value = Data()
        else:
            value = super().restore_attr(name, value)
        return value

    @classmethod
    def restore(cls, s_dict):
        self = super().restore(s_dict)

        # Clear any unused ai groups
        # Cannot be done on save because then autosaving will randomly remove non-populated ai groups you may have planned to use
        all_unit_ai_groups = {unit.ai_group for unit in self.units if unit.ai_group}
        for ai_group in self.ai_groups[:]:
            if ai_group.nid not in all_unit_ai_groups:
                self.ai_groups.delete(ai_group)

        # Create any missing ai groups since old versions of the project files
        # don't have reified ai groups
        for ai_group_nid in all_unit_ai_groups:
            if ai_group_nid not in self.ai_groups:
                self.ai_groups.append(AIGroup(ai_group_nid, 1))

        return self

    @classmethod
    def default(cls):
        return cls('0', 'Prologue')

class LevelCatalog(Data[LevelPrefab]):
    datatype = LevelPrefab
