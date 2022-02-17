from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.data.ui_prefab import UIObjectPrefab
from app.utilities.data import Prefab
from app.utilities.typing import NID


@dataclass
class UIObject(Prefab):
    nid: str
    can_be_invalid: bool = True
    log_errors: bool = True

    size: Tuple = field(default_factory=tuple)
    arguments: Dict[str, str] = field(default_factory=dict)
    bg_sprite: NID = None

    subcomponents: List[Tuple[Tuple[int, int], UIObject]] = field(default_factory=list)

    @classmethod
    def from_prefab(cls, prefab: UIObjectPrefab, arg_dict: Dict[str, str] = None):
        self = cls(prefab.nid)
        self.size = prefab.size
        self.arguments = {arg: value for arg, value in prefab.arguments.items()}
        if arg_dict:
            self.arguments.update(arg_dict)
        self.bg_sprite = prefab.bg_sprite
        self.subcomponents = []
        for pos, subcomponent in prefab.subcomponents:
            self.subcomponents.append((pos, UIObject.from_prefab(subcomponent)))

        self.can_be_invalid = prefab.can_be_invalid
        self.log_errors = prefab.log_errors
        return self

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
            value = [(tuple(pos), UIObject.restore(subcomponent_dict)) for pos, subcomponent_dict in value]
        elif name == 'size': # convert to tuple
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

    def __hash__(self) -> int:
        return hash(self.nid)
