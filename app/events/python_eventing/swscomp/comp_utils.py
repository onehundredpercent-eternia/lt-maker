
from dataclasses import dataclass, field
from enum import Enum
from typing import List

class ParseMode(Enum):
    COMMAND = 1
    ARGS = 2
    FLAGS = 3

@dataclass
class EventCommandData():
    command: str
    args: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    # if this is parsing a half-finished line, what mode we finished parsing at
    right_mode: ParseMode = ParseMode.FLAGS

    def to_event_command_str(self) -> str:
        command = self.command
        args = ','.join(self.args)
        # flags are always strings
        flags = ','.join([f'"{flag}"' for flag in self.flags])
        return "%s(%s).set_flags(%s)" % (command, args, flags)

@dataclass
class ScriptWithSentinel():
    """
    A python event script, with all event commands
    replaced with the COMMAND_SENTINEL,
    and extracted into EventCommandData
    for use in second-pass compilation
    """
    source: str
    commands: List[EventCommandData]

COMMAND_SENTINEL = '__COMMAND_SENTINEL'