from __future__ import annotations
from typing import Tuple

from random import Random

from app.utilities.typing import NID
from app.utilities.utils import tuple_add

class TextEffect():
    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        pass

class ColorEffect(TextEffect):
    def __init__(self, color: NID):
        self._color = color
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return self._color, curr_offset
    def __repr__(self):
        return f"color({self._color})"

class JitterEffect(TextEffect):
    _rng = Random()
    def get_jitter(magnitude: float = 1) -> Tuple[float, float]:
        return (JitterEffect._rng.gauss(0, 1) * magnitude, JitterEffect._rng.gauss(0, 1) * magnitude)

    def __init__(self):
        self._jitter = (0, 0)
        self._count = 0
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        if self._count % 3 == 1:
            self._jitter = JitterEffect.get_jitter()
        self._count += 1
        self._count = self._count % 3 # prevent infinitely counting up
        return curr_color, tuple_add(curr_offset, self._jitter)
    def __repr__(self):
        return f"jitter({self._jitter[0]:.2f},{self._jitter[1]:.2f})"
