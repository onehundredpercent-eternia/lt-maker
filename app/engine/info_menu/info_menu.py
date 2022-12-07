from app.constants import BEEG_MODE

from app.engine.sprites import SPRITES
from app.engine.sound import get_sound_thread
from app.engine import engine, skill_system
from app.engine.game_state import game

def to_info_menu():
    if BEEG_MODE:
        game.memory['next_state'] = 'beeg_info_menu'
    else:
        game.memory['next_state'] = 'info_menu'
    game.state.change('transition_to')

def handle_info():
    if game.cursor.get_hover():
        get_sound_thread().play_sfx('Select 1')
        if BEEG_MODE:
            game.memory['next_state'] = 'beeg_info_menu'
        else:
            game.memory['next_state'] = 'info_menu'
        game.memory['current_unit'] = game.cursor.get_hover()
        game.state.change('transition_to')
    else:
        get_sound_thread().play_sfx('Select 3')
        game.boundary.toggle_all_enemy_attacks()

def handle_aux():
    avail_units = [
        u for u in game.units
        if u.team == 'player' and
        u.position and
        not u.finished and
        skill_system.can_select(u) and
        'Tile' not in u.tags]

    if avail_units:
        cur_unit = game.cursor.get_hover()
        if not cur_unit or cur_unit not in avail_units:
            cur_unit = game.memory.get('aux_unit')
        if not cur_unit or cur_unit not in avail_units:
            cur_unit = avail_units[0]

        if cur_unit in avail_units:
            idx = avail_units.index(cur_unit)
            idx = (idx + 1) % len(avail_units)
            new_pos = avail_units[idx].position
            game.memory['aux_unit'] = cur_unit
            get_sound_thread().play_sfx('Select 4')
            game.cursor.set_pos(new_pos)

def build_groove(surf, topleft, width, fill):
    bg = SPRITES.get('groove_back')
    start = engine.subsurface(bg, (0, 0, 2, 5))
    mid = engine.subsurface(bg, (2, 0, 1, 5))
    end = engine.subsurface(bg, (3, 0, 2, 5))
    fg = SPRITES.get('groove_fill')

    # Build back groove
    surf.blit(start, topleft)
    for idx in range(width - 2):
        mid_pos = (topleft[0] + 2 + idx, topleft[1])
        surf.blit(mid, mid_pos)
    surf.blit(end, (topleft[0] + width, topleft[1]))

    # Build fill groove
    number_needed = int(fill * (width - 1))  # Width of groove minus section for start and end
    for groove in range(number_needed):
        surf.blit(fg, (topleft[0] + 1 + groove, topleft[1] + 1))
