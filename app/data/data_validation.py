from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple, Union

from app.editor.event_editor.event_inspector import EventInspectorEngine
from app.utilities.typing import NID

from .database.database import Database
from .database.database_types import DatabaseType
from .resources.resource_types import ResourceType
from .resources.resources import Resources

ValidOption = Tuple[Optional[str], NID]

class GameDataValidator():
    def __init__(self, db: Database, resources: Resources) -> None:
        self._db = db
        self._resources = resources
        self.event_engine = EventInspectorEngine(self._db.events)

        self.validator_map: Dict[DatabaseType | ResourceType, Callable[[str, Optional[NID]], bool]] = {
            DatabaseType.CONSTANTS: self._validate_affinity,
        }

        self.get_valids_map: Dict[DatabaseType | ResourceType, Callable[[Optional[NID], Optional[str]], List[ValidOption]]] = {
            DatabaseType.CONSTANTS: self._get_valid_affinities
        }

    def validate(self, type: DatabaseType | ResourceType, value: str, level: Optional[NID] = None) -> bool:
        return self.validator_map[type](value, level)

    def get_valid_entries(self, type: DatabaseType | ResourceType,
                          level: Optional[NID] = None,
                          text_so_far: Optional[str] = None) -> List[ValidOption]:
        return self.get_valids_map[type](level, text_so_far)

