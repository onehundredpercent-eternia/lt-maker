from dataclasses import dataclass
from enum import Enum

class ErrorLevel(Enum):
    WARNING = 0
    FATAL = 1

@dataclass
class DBError():
    level: ErrorLevel
    what: str