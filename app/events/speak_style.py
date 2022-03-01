from __future__ import annotations

from typing import Set, Tuple
from app.utilities.typing import NID

class SpeakStyle():
    def __init__(self, nid: NID = None, speaker: NID = None, text_position: str | Tuple[int, int] = None,
                 width: int = None, text_speed: float = None, font_color: str = None,
                 font_type: str = None, dialog_box: str = None, num_lines: int = None,
                 draw_cursor: bool = None, message_tail: str = None, flags: Set[str] = None):
        self.nid: NID = nid
        self.speaker: NID = speaker
        self.text_position: str | Tuple[int, int] = text_position
        self.width: int = width
        self.text_speed: float = text_speed
        self.font_color: str = font_color
        self.font_type: str = font_type
        self.dialog_box: str = dialog_box
        self.num_lines: int = num_lines
        self.draw_cursor: bool = draw_cursor
        self.message_tail: str = message_tail
        self.flags: Set[str] = flags
