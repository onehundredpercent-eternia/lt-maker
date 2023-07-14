from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

ARG_TYPE_MAP: Dict[str, str] = {
    'unit': "UnitObject",
    'item': "ItemObject",
    'target': "UnitObject"
}

class ResolvePolicy(Enum):
    UNIQUE = 'unique'
    UNION = 'union'
    NUMERIC_ACCUM = 'numeric_accumulate'

@dataclass
class HookInfo():
    args: List[str] = field(default_factory=list)
    policy: ResolvePolicy = ResolvePolicy.UNIQUE
    has_default_value: bool = False


"""
Resolution policies go here
"""

def unique(vals: List[Any]):
    if not vals:
        return None
    return vals[0]

def union(vals: List[Any]):
    return set(vals)

def numeric_accumulate(vals: List[int | float]):
    return sum(vals)