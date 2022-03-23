import os
import collections
from datetime import datetime

from app.constants import WINWIDTH, WINHEIGHT, VERSION, FPS
from app.engine import engine

import app.engine.config as cf

def start(title, from_editor=False):
    if from_editor:
        engine.constants['standalone'] = False
    engine.init()
    icon = engine.image_load('favicon.ico')
    engine.set_icon(icon)

    from app.engine import sprites
    sprites.load_images()

    # Hack to get icon to show up in windows
    try:
        import ctypes
        myappid = u'rainlash.lextalionis.ltmaker.current' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except:
        print("Maybe not Windows? (but that's OK)")

    engine.DISPLAYSURF = engine.build_display(engine.SCREENSIZE)
    engine.set_title(title + ' - v' + VERSION)
    print("Version: %s" % VERSION)

screenshot = False
def save_screenshot(raw_events: list, surf):
    global screenshot
    for e in raw_events:
        if e.type == engine.KEYDOWN and e.key == engine.key_map['`']:
            screenshot = True
            if not os.path.isdir('screenshots'):
                os.mkdir('screenshots')
        elif e.type == engine.KEYUP and e.key == engine.key_map['`']:
            screenshot = False
        elif e.type == engine.KEYDOWN and e.key == engine.key_map['f12']:
            if not os.path.isdir('screenshots'):
                os.mkdir('screenshots')
            current_time = str(datetime.now()).replace(' ', '_').replace(':', '.')
            engine.save_surface(surf, 'screenshots/LT_%s.png' % current_time)
    if screenshot:
        current_time = str(datetime.now()).replace(' ', '_').replace(':', '.')
        engine.save_surface(surf, 'screenshots/LT_%s.bmp' % current_time)

def draw_fps(surf, fps_records):
    from app.engine.fonts import FONT
    total_time = sum(fps_records)
    num_frames = len(fps_records)
    fps = int(num_frames / (total_time / 1000))
    max_frame = max(fps_records)
    min_fps = 1000 // max_frame

    FONT['small-white'].blit(str(fps), surf, (surf.get_width() - 20, 0))
    FONT['small-white'].blit(str(min_fps), surf, (surf.get_width() - 20, 12))

def run(game):
    from app.engine.sound import get_sound_thread
    from app.engine.game_counters import ANIMATION_COUNTERS
    from app.engine.input_manager import get_input_manager

    ANIMATION_COUNTERS.reset()

    get_sound_thread().reset()
    get_sound_thread().set_music_volume(cf.SETTINGS['music_volume'])
    get_sound_thread().set_sfx_volume(cf.SETTINGS['sound_volume'])

    surf = engine.create_surface((WINWIDTH, WINHEIGHT))
    # import time
    clock = engine.Clock()
    fps_records = collections.deque(maxlen=FPS)
    while True:
        # start = time.time_ns()
        engine.update_time()
        fps_records.append(engine.get_delta())
        # print(engine.get_delta())

        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break
        event = get_input_manager().process_input(raw_events)

        surf, repeat = game.state.update(event, surf)
        while repeat:  # Let's the game traverse through state chains
            surf, repeat = game.state.update([], surf)

        if cf.SETTINGS['display_fps']:
            draw_fps(surf, fps_records)

        get_sound_thread().update(raw_events)

        engine.push_display(surf, engine.SCREENSIZE, engine.DISPLAYSURF)

        save_screenshot(raw_events, surf)

        engine.update_display()
        # end = time.time_ns()
        # milliseconds_elapsed = (end - start)/1e6
        # if milliseconds_elapsed > 10:
        #     print("Engine took too long: %f" % milliseconds_elapsed)

        game.playtime += clock.tick()

def run_combat(mock_combat):
    from app.engine.sound import get_sound_thread
    from app.engine.input_manager import get_input_manager

    get_sound_thread().reset()
    get_sound_thread().set_music_volume(cf.SETTINGS['music_volume'])
    get_sound_thread().set_sfx_volume(cf.SETTINGS['sound_volume'])

    surf = engine.create_surface((WINWIDTH, WINHEIGHT))
    clock = engine.Clock()
    while True:
        engine.update_time()

        raw_events = engine.get_events()
        if raw_events == engine.QUIT:
            break
        event = get_input_manager().process_input(raw_events)

        mock_combat.take_input(event)
        mock_combat.update()
        surf = mock_combat.draw(surf)

        get_sound_thread().update(raw_events)

        engine.push_display(surf, engine.SCREENSIZE, engine.DISPLAYSURF)
        save_screenshot(raw_events, surf)

        engine.update_display()
        clock.tick()
