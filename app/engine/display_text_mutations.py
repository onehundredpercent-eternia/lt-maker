from __future__ import annotations
from typing import Tuple

from random import Random

from app.utilities.typing import NID

import pygame

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
        return curr_color, tuple(map(sum, zip(curr_offset, self._jitter)))
    def __repr__(self):
        return f"jitter({self._jitter[0]:.2f},{self._jitter[1]:.2f})"

class TextTransform():
    def __init__(self):
        raise Exception("TextTransform should not be directly instantiated")
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        pass

class FlipTransform(TextTransform):
    def __init__(self, flip_x: bool = False, flip_y: bool = True):
        self._flip_x = flip_x
        self._flip_y = flip_y
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        return pygame.transform.flip(surf, self._flip_x, self._flip_y)
    def __repr__(self):
        return f"flip(x:{self._flip_x},y:{self._flip_y})"

class RotateTransform(TextTransform):
    def __init__(self, degrees: float = 30):
        self._degrees = degrees
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        return pygame.transform.rotate(surf, self._degrees)
    def __repr__(self):
        return f"rotate(deg:{self._degrees:.2f})"