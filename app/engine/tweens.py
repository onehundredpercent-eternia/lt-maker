from enum import IntEnum

from app.engine import engine
from app.utilities import utils
from app.utilities.algorithms.interpolation import lerp, tlerp, cubic_easing, tcubic_easing

# Time is always measured in milliseconds

class CurveType(IntEnum):
    Linear = 1
    Quad = 2
    Cubic = 3

# a generic tween object that can tween any property of any object
class Tween():
    def __init__(self, initial_value, setter, final_value, duration: int, curve: CurveType = None, starting_time: int = None):
        """
        initial_value -> what the value starts at
        setter -> function to call to set the value
        final_value -> what the value should become
        duration -> how long the tween should last  # milliseconds
        curve -> How to lerp the value over time
        starting_time -> delay the start by some amount of time
        """
        self.initial_value = initial_value
        self.setter = setter
        self.final_value = final_value
        assert duration >= 0
        self.duration = duration
        self.starting_time = starting_time or engine.get_time()
        self.curve = curve or CurveType.Linear

        self.is_tuple = isinstance(self.starting_value, tuple)

        # State variables
        self.playing = True
        self.done = False

    def play(self):
        self.playing = True

    def stop(self):
        self.playing = False

    def kill(self):
        self.stop()
        self.done = True

    def ease(self, perc: float) -> float:
        if self.curve == CurveType.Linear:
            if self.is_tuple:
                val = tlerp(self.starting_value, self.final_value, perc)
            else:
                val = lerp(self.starting_value, self.final_value, perc)
        elif self.curve == CurveType.Quad:
            if self.is_tuple:
                val = tquad_easing(self.starting_value, self.final_value, perc)
            else:
                val = quad_easing(self.starting_value, self.final_value, perc)
        elif self.curve == CurveType.Cubic:
            if self.is_tuple:
                val = tcubic_easing(self.starting_value, self.final_value, perc)
            else:
                val = cubic_easing(self.starting_value, self.final_value, perc)
        else:
            if self.is_tuple:
                val = tlerp(self.starting_value, self.final_value, perc)
            else:
                val = lerp(self.starting_value, self.final_value, perc)
        return val

    def update(self, current_time=None) -> bool:
        # Returns whether the current tween is done
        if self.playing:
            current_time = current_time or engine.get_time()
            offset_time = current_time - self.starting_time
            perc = utils.clamp(offset_time / self.duration, 0, 1)
            val = self.ease(perc)
            
            # Now set the calculated value
            self.setter(val)
            # Hey, we're done!
            if perc >= 1:
                self.done = True
                self.playing = False

        return self.done

    @classmethod
    def animate_speed(cls, obj, speed: float, curve: CurveType = None, starting_time: int = None) -> Tween:
        def setter(x):
            obj.idx = int(x)
        final_value = obj.num_frames - 0.001
        duration = obj.num_frames * speed
        new_tween = cls(obj.idx, setter, final_value, duration, curve, starting_time)
        return new_tween

    @classmethod
    def animate_frames(cls, obj, frame_times: List[int], curve: CurveType = None, starting_time: int = None) -> Tween:
        assert all(ft > 0 for ft in frame_times)
        def setter(x):
            total_vals = 0
            for idx, val in enumerate(frame_times):
                if total_vals <= x < total_vals + val:
                    obj.idx = idx
                    return
                total_vals += val

        final_value = sum(frame_times)
        duration = utils.frames2ms(final_value)
        new_tween = cls(0, setter, final_value, duration, curve, starting_time)
        return new_tween

    @classmethod
    def vibrate_horiz(cls, obj, duration: float, intensity: float, starting_time: int = None) -> Tween:
        def setter(x):
            if obj.offset[0] > 0:
                obj.offset = (-intensity, 0)
            else:
                obj.offset = (intensity, 0)

        # Initial and Final value aren't actually used
        new_tween = cls(0, setter, 1, duration, None, starting_time)
        return new_tween

class TweenSequence():
    def __init__(self, loop=True):
        self.tweens: List[Tween] = []
        self.starting_times: List[int] = []  # measured in ms
        self.starting_time: int = engine.get_time()  # measured in game time
        self.loop: bool = loop
        self.done: bool = False

    def add_tween(self, tween: Tween, delay_by: int = None):
        self.tweens.append(tween)
        if delay_by:
            self.starting_times.append(self.starting_time + delay_by)
            tween.playing = False

    def update(self, current_time=None) -> bool:
        # Returns whether the current tween sequence is done

        current_time = current_time or engine.get_time()
        for idx, st in enumerate(self.starting_time):
            if st >= current_time:
                self.tweens[idx].play()

        for tween in self.tweens:
            tween.update(current_time)

        if all(tween.done for tween in self.tweens):
            if self.loop:
                self.reset()
            else:
                self.done = True
        return self.done

    def reset(self):
        self.starting_time = engine.get_time()
        for tween in self.tweens:
            tween.reset()
            tween.stop()

if __name__ == '__main__':
    class Obj():
        def __init__(self, pos, color):
            self.pos = pos
            self.color = color
            self.idx = 0

    obj = Obj(5, (80, 80, 80))
    def pos_setter(x): obj.pos = x
    def color_setter(x): obj.color = tuple([int(_) for _ in x])
    def idx_setter(x): obj.idx = x

    tween = Tween(lambda: obj.pos, pos_setter, 10, 5)
    counter = 0
    while not tween.done:
        counter += 0.5
        tween.update(counter)
        print(obj.pos)

    print("Now backwards!")
    tween = Tween(lambda: obj.pos, pos_setter, 2, 4)
    counter = 0
    while not tween.done:
        counter += 0.5
        tween.update(counter)
        print(obj.pos)

    print("Now color!")
    tween = Tween(lambda: obj.color, color_setter, (120, 80, 50), 3)
    counter = 0
    while not tween.done:
        counter += 0.5
        tween.update(counter)
        print(obj.color)

    print("Now cubic curve!")
    tween = Tween(lambda: obj.pos, pos_setter, 7, 5, CurveType.Cubic)
    counter = 0
    while not tween.done:
        counter += 0.5
        tween.update(counter)
        print(obj.pos)
