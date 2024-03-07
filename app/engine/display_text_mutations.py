from __future__ import annotations
from typing import List, Tuple, Optional

from app.engine.jitter import get_jitter
from app.utilities.typing import NID

import pygame

class TextEffect():
    def __init__(self):
        raise "TextEffect should not be directly instantiated"
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        pass

class NullEffect(TextEffect):
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return curr_color, curr_offset
    def __repr__(self):
        return "NullEffect"

class ColorEffect(TextEffect):
    def __init__(self, color: NID):
        self._color = color
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return self._color, curr_offset
    def __repr__(self):
        return f"{self._color}"

class JitterEffect(TextEffect):
    def __init__(self):
        self._jitter = get_jitter()
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return curr_color, tuple(map(sum, zip(curr_offset, self._jitter)))
    def __repr__(self):
        return f"({self._jitter[0]:.2f},{self._jitter[1]:.2f})"

class TextTransform():
    def __init__(self):
        raise "TextEffect should not be directly instantiated"
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        pass

class FlipTransform(TextTransform):
    def __init__(self, flip_x: bool = False, flip_y: bool = True):
        self._flip_x = flip_x
        self._flip_y = flip_y
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        return pygame.transform.flip(surf, self._flip_x, self._flip_y)

class RotateTransform(TextTransform):
    def __init__(self, degrees: float = 30):
        self._degrees = degrees
    def apply(self, surf: pygame.Surface) -> pygame.Surface:
        return pygame.transform.rotate(surf, self._degrees)