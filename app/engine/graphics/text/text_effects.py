from __future__ import annotations
from typing import List, Dict, Tuple, Optional

from math import sin, pi
from random import Random

from app.utilities.typing import NID
from app.utilities.utils import tuple_add

_rng = Random()


class TextSettings:
    def __init__(self, color: NID, offset: Tuple[float, float]):
        self.color = color
        self.offset = offset

    def apply(self, effects: List[TextEffect], bit: Optional[int] = None):
        for effect in effects:
            if effect.is_char_level:
                effect.apply(self, bit)
            else:
                effect.apply(self)


class TextEffect:
    nid: NID = ""
    is_char_level: bool = False
    impl_nid: NID = None

    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")

    def __str__(self):
        return self.nid


class ColorEffect(TextEffect):
    nid = "color"

    def __init__(self, color: NID):
        self._color = color

    def apply(self, settings: TextSettings):
        settings.color = self._color

    def __str__(self):
        return f"{self._color}"


class JitterEffect(TextEffect):
    nid = "jitter"

    @classmethod
    def _get_jitter(klass, magnitude: float = 1) -> Tuple[float, float]:
        return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)

    def __init__(self, idx: int = 0, magnitude: float = 1, wait: int = 3):
        self._idx = idx
        self._magnitude = magnitude
        self._wait = wait

        self._jitter = (0, 0)
        self._count = 0

    def apply(self, settings: TextSettings):
        if self._count % self._wait == 1:
            self._jitter = self._get_jitter(self._magnitude)
        # prevent infinitely counting up
        self._count = (self._count + 1) % self._wait
        settings.offset = tuple_add(settings.offset, self._jitter)


class Jitter2Effect(TextEffect):
    nid = "jitter2"
    is_char_level = True
    impl_nid = "jitter"

    def __init__(self, magnitude: float = 1, wait: int = 3):
        self._magnitude = magnitude
        self._wait = wait

        self._length = 0
        self._bits = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [
            TEXT_EFFECTS[self.impl_nid](idx, self._magnitude, self._wait)
            for idx in range(length)
        ]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception(
                "Jitter2Effect length not initialized, must call set_length()"
            )
        self._bits[bit].apply(settings)

    def __str__(self):
        return self.nid


def _initialize_sin_sequence(length: int) -> List[float]:
    return [sin(x * 2 * pi / length) for x in range(length)]

class SinEffect(TextEffect):
    nid = "sin"

    _SIN_SEQUENCE_LENGTH = 30
    _sin_sequence = _initialize_sin_sequence(_SIN_SEQUENCE_LENGTH)

    def __init__(self, idx: int = 0, x_amplitude: float = 0, y_amplitude: float = 3.5):
        self._idx = idx
        self._amplitude = (x_amplitude, y_amplitude)

        self._count = 0

    def apply(self, settings: TextSettings):
        idx = (
            self._count + self._idx * self._SIN_SEQUENCE_LENGTH // 10
        ) % self._SIN_SEQUENCE_LENGTH
        x_offset = settings.offset[0] + self._sin_sequence[idx] * self._amplitude[0]
        y_offset = settings.offset[1] + self._sin_sequence[idx] * self._amplitude[1]
        settings.offset = (x_offset, y_offset)
        self._count = (self._count + 1) % self._SIN_SEQUENCE_LENGTH


class WaveEffect(TextEffect):
    nid = "wave"
    is_char_level = True
    impl_nid = "sin"

    def __init__(self, amplitude: float = 3.5):
        self._amplitude = amplitude

        self._length = 0
        self._bits = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [
            TEXT_EFFECTS[self.impl_nid](idx, 0, self._amplitude)
            for idx in range(length)
        ]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception("WaveEffect length not initialized, must call set_length()")
        self._bits[bit].apply(settings)


class Wave2Effect(TextEffect):
    nid = "wave2"
    is_char_level = True
    impl_nid = "sin"

    def __init__(self, x_amplitude: float = 2, y_amplitude: float = 3.5):
        self._amplitude = (x_amplitude, y_amplitude)
        self._length = 0
        self._bits = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [
            TEXT_EFFECTS[self.impl_nid](idx, self._amplitude[0], self._amplitude[1])
            for idx in range(length)
        ]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception("WaveEffect length not initialized, must call set_length()")
        self._bits[bit].apply(settings)


TEXT_EFFECTS: Dict[NID, TextEffect] = {
    effect.nid: effect for effect in TextEffect.__subclasses__()
}
