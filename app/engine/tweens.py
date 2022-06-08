from enum import IntEnum

from app.engine import engine
from app.utilities import utils
from app.utilities.algorithms.interpolation import lerp, tlerp, cubic_easing, tcubic_easing

# Time is always measured in milliseconds

class CurveType(IntEnum):
    Linear = 1
    Quad = 2
    Cubic = 3

# Draft of a very generic tween object that can tween any property
# of any object
class Tween():
    def __init__(self, getter, setter, final_value, duration, curve=None, starting_time=None):
        """
        getter -> function to call to get value
        setter -> function to call to set the value
        final_value -> what the value should become
        duration -> how long the tween should last  # milliseconds
        curve -> How to lerp the value over time
        starting_time -> delay the start by some amount of time
        """
        self.getter = getter
        self.setter = setter
        self.final_value = final_value
        assert duration >= 0
        self.duration = duration
        self.starting_time = starting_time or engine.get_time()
        self.starting_value = getter()
        self.curve = curve or CurveType.Linear

        self.is_tuple = isinstance(self.starting_value, tuple)

        # State variables
        self.playing = True
        self.done = False

    def update(self, current_time=None):
        if self.playing:
            current_time = current_time or engine.get_time()
            offset_time = current_time - self.starting_time
            perc = utils.clamp(offset_time / self.duration, 0, 1)
            if self.curve == CurveType.Linear:
                if self.is_tuple:
                    val = tlerp(self.starting_value, self.final_value, perc)
                else:
                    val = lerp(self.starting_value, self.final_value, perc)
            elif self.curve == CurveType.Cubic:
                if self.is_tuple:
                    val = tcubic_easing(self.starting_value, self.final_value, perc)
                else:
                    val = cubic_easing(self.starting_value, self.final_value, perc)
            else:  # LOL
                if self.is_tuple:
                    val = tlerp(self.starting_value, self.final_value, perc)
                else:
                    val = lerp(self.starting_value, self.final_value, perc)
            # Now set the calculated value
            self.setter(val)
            # Hey, we're done!
            if perc >= 1:
                self.done = True

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

# TODO: TweenSequences, QuadLerp?
