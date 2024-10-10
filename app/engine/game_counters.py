from dataclasses import fields
from typing import List
from app.constants import FRAMERATE
from app.utilities.utils import frames2ms, frames_to_ms
from app.engine import engine
from app.counters import GenericAnimCounter, generic3counter, movement_counter, simplecounter

class Counters():
    anim_counters: List[GenericAnimCounter]
    last_update: int = 0 # should be divisible evenly by update_delta
    update_delta: float = FRAMERATE

    def __init__(self):
        self.anim_counters = []
        self.passive_sprite_counter = GenericAnimCounter.from_frames_back_and_forth([32, 4, 32])
        self.anim_counters.append(self.passive_sprite_counter)
        self.reset()

    def update(self):
        current_time = engine.get_time()
        dt = current_time - self.last_update
        if dt > self.update_delta:
            frames_elapsed = int(dt // self.update_delta)
            self.last_update = int((current_time // self.update_delta) * self.update_delta)
            for counter in self.anim_counters:
                counter.update(frames_elapsed)

    def reset(self):
        for counter in self.anim_counters:
            counter.reset()
        self._active_sprite_counter = generic3counter(frames2ms(20), frames2ms(4))
        self._move_sprite_counter = simplecounter((frames2ms(13), frames2ms(6), frames2ms(13), frames2ms(6)))
        self._fast_move_sprite_counter = simplecounter((frames2ms(6), frames2ms(3), frames2ms(6), frames2ms(3)))
        self._attack_movement_counter = movement_counter()
        self._arrow_counter = simplecounter((frames2ms(16), frames2ms(16), frames2ms(16)))
        self._x2_counter = simplecounter([frames2ms(3)] * 18)
        self._flag_counter = simplecounter([frames2ms(15)] * 4)
        self._fps6_360counter = simplecounter([frames2ms(6)] * 360)
        self._fps2_360counter = simplecounter([frames2ms(2)] * 360)

    @property
    def active_sprite_counter(self):
        current_time = engine.get_time()
        self._active_sprite_counter.update(current_time)
        return self._active_sprite_counter

    @property
    def move_sprite_counter(self):
        current_time = engine.get_time()
        self._move_sprite_counter.update(current_time)
        return self._move_sprite_counter

    @property
    def fast_move_sprite_counter(self):
        current_time = engine.get_time()
        self._fast_move_sprite_counter.update(current_time)
        return self._fast_move_sprite_counter

    @property
    def attack_movement_counter(self):
        current_time = engine.get_time()
        self._attack_movement_counter.update(current_time)
        return self._attack_movement_counter

    @property
    def arrow_counter(self):
        current_time = engine.get_time()
        self._arrow_counter.update(current_time)
        return self._arrow_counter

    @property
    def x2_counter(self):
        current_time = engine.get_time()
        self._x2_counter.update(current_time)
        return self._x2_counter

    @property
    def flag_counter(self):
        current_time = engine.get_time()
        self._flag_counter.update(current_time)
        return self._flag_counter

    @property
    def fps6_360counter(self):
        current_time = engine.get_time()
        self._fps6_360counter.update(current_time)
        return self._fps6_360counter

    @property
    def fps2_360counter(self):
        current_time = engine.get_time()
        self._fps2_360counter.update(current_time)
        return self._fps2_360counter


ANIMATION_COUNTERS = Counters()
