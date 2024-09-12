from __future__ import annotations
from dataclasses import field
from typing import Any
from app.utilities.data import Data
from app.utilities.prefab import Prefab
from app.utilities import str_utils

AI_ActionTypes = ['None', 'Attack', 'Support', 'Steal', 'Interact', 'Move_to', 'Move_away_from', 'Wait']
AI_TargetTypes = ['None', 'Enemy', 'Ally', 'Unit', 'Position', 'Event', 'Terrain', 'Time']
unit_spec = ['All', 'Class', 'Tag', 'Name', 'Team', 'Faction', 'Party', 'ID']
# View Range
# (Don't look | Movement*2 + Maximum Item Range | Entire Map | Custom Range (Integer))

class AIPrefab(Prefab):
    nid: str
    priority: int
    offense_bias: float = 2
    behaviours: list[AIBehaviour] = field(default_factory=list)
    roam_ai: bool = False

    def add_behaviour(self, behaviour: AIBehaviour):
        self.behaviours.append(behaviour)

    def add_default(self):
        self.behaviours.append(AIBehaviour.DoNothing())

    def pop_behaviour(self):
        self.behaviours.pop()

    def set_behaviour(self, idx: int, behaviour: AIBehaviour):
        self.behaviours[idx] = behaviour

    @classmethod
    def default(cls):
        return cls(None, 0)

    def has_unit_spec(self, spec_type, spec_nid) -> bool:
        for behaviour in self.behaviours:
            if behaviour.has_unit_spec(spec_type, spec_nid):
                return True
        return False

    def change_unit_spec(self, spec_type, old_nid, new_nid):
        for behaviour in self.behaviours:
            behaviour.change_unit_spec(spec_type, old_nid, new_nid)

    def guard_ai(self) -> bool:
        # Determines whether this AI will ever move
        # Used in game.boundary for graphics
        if all(behaviour.action == "None" for behaviour in self.behaviours):
            return False
        for behaviour in self.behaviours:
            if behaviour.action == "None":
                continue
            elif not behaviour.guard_ai():
                return False
        return True

class AIBehaviour(Prefab):
    action: str
    target: Any
    target_spec: Any = None
    view_range: int = 0
    invert_targeting: bool = False
    roam_speed: int = 100
    desired_proximity: int = 0
    condition: str = ''

    @classmethod
    def DoNothing(cls):
        return cls('None', 'None', 0)

    @classmethod
    def default(cls):
        return cls.DoNothing()

    def has_unit_spec(self, spec_type, spec_nid):
        if self.target in ('Enemy', 'Ally', 'Unit'):
            if self.target_spec and self.target_spec[0] == spec_type and self.target_spec[1] == spec_nid:
                return True
        return False

    def change_unit_spec(self, spec_type, old_nid, new_nid):
        if self.target in ('Enemy', 'Ally', 'Unit'):
            if self.target_spec and self.target_spec[0] == spec_type and self.target_spec[1] == old_nid:
                self.target_spec[1] = new_nid

    def guard_ai(self):
        return self.view_range == -1

class AICatalog(Data[AIPrefab]):
    datatype = AIPrefab

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = str_utils.get_next_name("New AI", nids)
        new_ai = AIPrefab(nid, 20)
        self.append(new_ai)
        return new_ai
