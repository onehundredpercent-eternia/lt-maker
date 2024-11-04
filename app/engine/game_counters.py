from dataclasses import fields
from typing import Dict, List, Optional
from app.constants import FRAMERATE
from app.utilities.utils import frames2ms, frames_to_ms
from app.engine import engine
from app.counters import GenericAnimCounter, movement_counter

class Counters():
    anim_counters: Dict[str, GenericAnimCounter]
    last_update: int = 0 # should be divisible evenly by update_delta
    update_delta: float = FRAMERATE

    def __init__(self):
        self.anim_counters = {}

        self.passive_sprite_counter = GenericAnimCounter.from_frames_back_and_forth([32, 4, 32], get_time=engine.get_time)
        self.active_sprite_counter = GenericAnimCounter.from_frames_back_and_forth([20, 4, 20], get_time=engine.get_time)
        self.move_sprite_counter = GenericAnimCounter.from_frames([13, 6, 13, 6], get_time=engine.get_time)
        self.fast_move_sprite_counter = GenericAnimCounter.from_frames([6, 3, 6, 3], get_time=engine.get_time)
        self.arrow_counter = GenericAnimCounter.from_frames([16, 16, 16], get_time=engine.get_time)
        self.x2_counter = GenericAnimCounter.from_frames([3] * 18, get_time=engine.get_time)
        self.flag_counter = GenericAnimCounter.from_frames([15] * 4, get_time=engine.get_time)
        self.fps6_360counter = GenericAnimCounter.from_frames([6] * 360, get_time=engine.get_time)
        self.fps2_360counter = GenericAnimCounter.from_frames([2] * 360, get_time=engine.get_time)
        self.reset()

    def reset(self):
        for counter in self.anim_counters.values():
            counter.reset()
        self._attack_movement_counter = movement_counter()

    @property
    def attack_movement_counter(self):
        current_time = engine.get_time()
        self._attack_movement_counter.update(current_time)
        return self._attack_movement_counter


ANIMATION_COUNTERS = Counters()
