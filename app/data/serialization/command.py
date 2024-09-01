from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SCommand(Enum):
    WRITE = 0
    COPY = 1

@dataclass
class SerializeCommand():
    path: Path
    contents: str
    action: SCommand