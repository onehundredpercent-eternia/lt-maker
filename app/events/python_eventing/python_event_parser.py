from __future__ import annotations

from typing import Generator, Optional
from app.engine.game_state import GameState

from app.events import event_commands
from app.events.python_eventing.compilation import Compiler
from app.events.python_eventing.utils import DO_NOT_EXECUTE_SENTINEL
from app.utilities.typing import NID

class PythonEventParser():
    def __init__(self, nid: NID, source: str, game: GameState):
        self.nid = nid
        self.source = source
        self.curr_cmd_idx = 0
        self.is_finished = False
        self._script = Compiler.compile(source, game, 0)

    def fetch_next_command(self) -> Optional[event_commands.EventCommand]:
        try:
            command_idx, next_command = next(self._script)
            while command_idx is DO_NOT_EXECUTE_SENTINEL:
                command_idx, next_command = next(self._script)
            self.curr_cmd_idx = command_idx
            return next_command
        except StopIteration:
            self.is_finished = True
            return None

    def finished(self):
        return self.is_finished

    def save(self):
        s_dict = {}
        s_dict['nid'] = self.nid
        s_dict['source'] = self.source
        s_dict['is_finished'] = self.is_finished
        s_dict['curr_cmd_idx'] = self.curr_cmd_idx
        return s_dict

    @classmethod
    def restore(cls, s_dict, game: GameState) -> PythonEventParser:
        source = s_dict['source']
        nid = s_dict['nid']
        self = cls(nid, source, game)
        self.curr_cmd_idx = s_dict['curr_cmd_idx']
        self._script = Compiler.compile(source, game, self.curr_cmd_idx)
        return self
