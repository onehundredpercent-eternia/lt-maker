from __future__ import annotations
from typing import Tuple
from app.constants import WINHEIGHT, WINWIDTH, BEEG_MODE
from app.utilities.typing import Point

if BEEG_MODE:
    horizontal_screen_positions = {'OffscreenLeft': -128,
                                   'FarLeft': 0,
                                   'Left': 36,
                                   'MidLeft': 72,
                                   'CenterLeft': 72,
                                   'CenterRight': WINWIDTH - 96 - 72,
                                   'MidRight': WINWIDTH - 96 - 72,
                                   'LevelUpRight': WINWIDTH - 96 - 40,
                                   'Right': WINWIDTH - 96 - 36,
                                   'FarRight': WINWIDTH - 96,
                                   'OffscreenRight': WINWIDTH}
else:
    horizontal_screen_positions = {'OffscreenLeft': -96,
                                   'FarLeft': -24,
                                   'Left': 0,
                                   'MidLeft': 24,
                                   'CenterLeft': 24,
                                   'CenterRight': WINWIDTH - 120,
                                   'MidRight': WINWIDTH - 120,
                                   'LevelUpRight': WINWIDTH - 100,
                                   'Right': WINWIDTH - 96,
                                   'FarRight': WINWIDTH - 72,
                                   'OffscreenRight': WINWIDTH}

vertical_screen_positions = {'Top': 0,
                             'Middle': (WINHEIGHT - 80) // 2,
                             'Bottom': WINHEIGHT - 80}

if BEEG_MODE:
    vertical_screen_positions['Top'] = 20

def parse_screen_position(pos: Tuple | str) -> Tuple[Point, bool]:
    """Returns a tuple of Point (on screen) and bool (indicating if the portrait should be mirrored)"""
    if not isinstance(pos, tuple):
        pos = (pos,)
    def resolve_pos(p: int | str, horiz=True) -> int:
        if isinstance(p, int):
            return p
        else:
            if horiz:
                return horizontal_screen_positions.get(p, 0)
            else:
                return vertical_screen_positions.get(p, 0)
    position = (0, 0)

    if len(pos) == 2:
        position = resolve_pos(pos[0]), resolve_pos(pos[1], False)
    else:
        pos = pos[0]
        if isinstance(pos, int) or pos in horizontal_screen_positions:
            position = resolve_pos(pos), vertical_screen_positions['Bottom']
        else:
            position = horizontal_screen_positions['Left'], resolve_pos(pos, False)
    return position, position[0] <= horizontal_screen_positions['CenterLeft']

def get_desired_center(x: int) -> int:
    if BEEG_MODE:
        if x < 80:  # FarLeft
            return 8
        elif x < 120:  # Left
            return 104
        elif x < 144:  # MidLeft
            return 144
        elif x > WINWIDTH - 80:  # FarRight
            return WINWIDTH - 8
        elif x > WINWIDTH - 120:  # Right
            return WINWIDTH - 104
        elif x > WINWIDTH - 144:  # MidRight
            return WINWIDTH - 144
        else:
            return WINWIDTH//2
    else:
        if x < 48:  # FarLeft
            return 8
        elif x < 72:  # Left
            return 80
        elif x < 104:  # MidLeft
            return 104
        elif x > WINWIDTH - 48:  # FarRight
            return WINWIDTH - 8
        elif x > WINWIDTH - 72:  # Right
            return WINWIDTH - 88
        elif x > WINWIDTH - 144:  # MidRight
            return WINWIDTH - 112
        else:
            return WINWIDTH//2
