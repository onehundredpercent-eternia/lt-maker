from app.constants import WINHEIGHT, WINWIDTH, MEMENTO_MODE

if MEMENTO_MODE:
    horizontal_screen_positions = {'OffscreenLeft': -128,
                                   'FarLeft': 0,
                                   'Left': 36,
                                   'MidLeft': 72,
                                   'CenterLeft': 72,
                                   'CenterRight': WINWIDTH - 128 - 72,
                                   'MidRight': WINWIDTH - 128 - 72,
                                   'LevelUpRight': 216,
                                   'Right': WINWIDTH - 128 - 36,
                                   'FarRight': WINWIDTH - 128,
                                   'OffscreenRight': WINWIDTH}
else:
    horizontal_screen_positions = {'OffscreenLeft': -96,
                                   'FarLeft': -24,
                                   'Left': 0,
                                   'MidLeft': 24,
                                   'CenterLeft': 24,
                                   'CenterRight': WINWIDTH - 120,
                                   'MidRight': WINWIDTH - 120,
                                   'LevelUpRight': 140,
                                   'Right': WINWIDTH - 96,
                                   'FarRight': WINWIDTH - 72,
                                   'OffscreenRight': WINWIDTH}

vertical_screen_positions = {'Top': 0,
                             'Middle': (WINHEIGHT - 80) // 2,
                             'Bottom': WINHEIGHT - 80}

if MEMENTO_MODE:
    vertical_screen_positions['Top'] = 20

def parse_screen_position(pos) -> tuple:
    x, y = 0, 0
    mirror = False
    if pos and ',' in pos:
        split_pos = pos.split(',')
        # Handle first part of tuple
        if split_pos[0] in horizontal_screen_positions:
            x = horizontal_screen_positions[split_pos[0]]
            mirror = 'Left' in split_pos[0]
        elif split_pos[0] in vertical_screen_positions:
            y = vertical_screen_positions[split_pos[0]]
        else:
            x = int(split_pos[0])
        # Handle second part of tuple
        if split_pos[1] in horizontal_screen_positions:
            x = horizontal_screen_positions[split_pos[1]]
            mirror = 'Left' in split_pos[1]
        elif split_pos[1] in vertical_screen_positions:
            y = vertical_screen_positions[split_pos[1]]
        else:
            y = int(split_pos[1])
    elif pos in horizontal_screen_positions:
        x = horizontal_screen_positions[pos]
        if MEMENTO_MODE:
            y = vertical_screen_positions['Top']
        else:
            y = vertical_screen_positions['Bottom']
        mirror = 'Left' in pos
    elif pos in vertical_screen_positions:
        x = horizontal_screen_positions['Left']
        y = vertical_screen_positions[pos]
        mirror = True

    return (x, y), mirror
