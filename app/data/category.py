from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

from app.utilities.data import Data, Prefab
from app.utilities.typing import NID

@dataclass
class Categories(Dict[NID, List[str]]):
    @classmethod
    def load(cls, s_dict: Dict[NID, str]) -> Categories:
        categories = cls()
        categories.clear()
        for nid, cat_str in s_dict.items():
            categories[nid] = cat_str.split('/')
        return categories

    def save(self) -> Dict[NID, str]:
        s_dict = {}
        categories = sorted(list(self.items()))
        for nid, cats in categories:
            s_dict[nid] = '/'.join(cats)
        return s_dict
