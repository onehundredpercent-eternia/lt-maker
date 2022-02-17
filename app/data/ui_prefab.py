from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.utilities.data import Data, Prefab
from app.utilities.typing import NID


@dataclass
class UIObjectPrefab(Prefab):
    nid: str = None
    generic: bool = False
    locked: bool = False
    can_be_invalid: bool = True
    log_errors: bool = True

    arguments: Dict[str, str] = field(default_factory=dict)
    size: Tuple = field(default_factory=tuple)
    bg_sprite: NID = None

    subcomponents: List[Tuple[Tuple[int, int], UIObjectPrefab]] = field(default_factory=list)

    # editor only
    canvas_offset: List[int] = field(default_factory=lambda: [0, 0])
    canvas: NID = None


    def save_attr(self, name, value):
        if name == 'subcomponents':
            value = [[list(pos), subcomponent.save()] for pos, subcomponent in self.subcomponents]
        elif name == 'size': # convert to list
            value = list(value)
        else:  # int, str, float, list, dict
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        if name == 'subcomponents':
            value = [(tuple(pos), UIObjectPrefab.restore(subcomponent_dict)) for pos, subcomponent_dict in value]
        elif name == 'size': # convert to tuple
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

    def __hash__(self) -> int:
        return hash(self.nid)

class UIObjectCatalog(Data[UIObjectPrefab]):
    datatype = UIObjectPrefab

    def __init__(self, vals: List[T] = None):
        super().__init__(vals)

    def update_restore(self, vals):
        self.clear()
        # populate with default fallbacks
        with open("app/editor/ui_editor/default_ui.json") as f:
            data = json.load(f)
            self.restore(data)
        if self.datatype and issubclass(self.datatype, Prefab):
            for s_dict in vals:
                new_val = self.datatype.restore(s_dict)
                if self.get(new_val.nid):
                    self.remove_key(new_val.nid)
                self.append(new_val)
        else:
            for val in vals:
                self.append(val)
        return self
