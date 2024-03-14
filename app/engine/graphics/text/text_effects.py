from __future__ import annotations
from typing import Tuple, List, Optional

from math import sin, pi
from random import Random

from app.utilities.typing import NID
from app.utilities.utils import tuple_add

_rng = Random()


class TextSettings():
    def __init__(self, color: NID, offset: Tuple[float, float]):
        self.color = color
        self.offset = offset

    def apply(self, effects: List[TextEffect], bit: Optional[int] = None):
        for effect in effects:
            if isinstance(effect, BitEffect):
                effect.apply(self, bit)
            else:
                effect.apply(self)


class TextEffect():
    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")

    def apply(self, settings: TextSettings):
        # modifies setting
        pass


class ColorEffect(TextEffect):
    def __init__(self, color: NID):
        self._color = color

    def apply(self, settings: TextSettings):
        settings.color = self._color

    def __repr__(self):
        return f"color({self._color})"


class JitterEffect(TextEffect):
    @classmethod
    def _get_jitter(klass, magnitude: float = 1) -> Tuple[float, float]:
        return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)

    def __init__(self, wait_iters: int = 3):
        self._wait_iters = wait_iters
        self._jitter = (0, 0)
        self._count = 0

    def apply(self, settings: TextSettings):
        if self._count % self._wait_iters == 1:
            self._jitter = self._get_jitter()
        # prevent infinitely counting up
        self._count = (self._count + 1) % self._wait_iters
        settings.offset = tuple_add(settings.offset, self._jitter)

    def __repr__(self):
        return f"jitter({self._wait_iters}{self._jitter[0]:.2f},{self._jitter[1]:.2f})"


class BitEffect():
    def __init__(self):
        raise Exception("BitEffect should not be directly instantiated")


def _initialize_sin_sequence(length: int) -> List[float]:
    return [sin(x * 2 * pi / length)
            for x in range(length)]


class Jitter2Effect(BitEffect):
    class Bit():
        @classmethod
        def _get_jitter(klass, magnitude: float = 1) -> Tuple[float, float]:
            return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)

        def __init__(self, wait_iters: int = 3):
            self._wait_iters = wait_iters
            self._jitter = (0, 0)
            self._count = 0

        def apply(self, settings: TextSettings):
            if self._count % self._wait_iters == 1:
                self._jitter = self._get_jitter()
            self._count = (self._count + 1) % self._wait_iters
            settings.offset = tuple_add(settings.offset, self._jitter)

    def __init__(self):
        self._length = 0
        self._bits: List[self.Bit] = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [self.Bit() for _ in range(length)]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception(
                "Jitter2Effect length not initialized, must call set_length()")
        self._bits[bit].apply(settings)

    def __repr__(self):
        return f"jitter2({self._length})"


class WaveEffect(BitEffect):
    class Bit():
        _SIN_SEQUENCE_LENGTH = 30
        _sin_sequence = _initialize_sin_sequence(_SIN_SEQUENCE_LENGTH)

        def __init__(self, index: int):
            self._index = index
            self._amplitude = 3.5
            self._count = 0

        def apply(self, settings: TextSettings):
            idx = (self._count + self._index *
                   self._SIN_SEQUENCE_LENGTH // 10) % self._SIN_SEQUENCE_LENGTH
            settings.offset = (
                settings.offset[0], settings.offset[1] + self._sin_sequence[idx] * self._amplitude)
            self._count = (self._count + 1) % self._SIN_SEQUENCE_LENGTH

    def __init__(self):
        self._length = 0
        self._bits: List[self.Bit] = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [self.Bit(x) for x in range(length)]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception(
                "WaveEffect length not initialized, must call set_length()")
        self._bits[bit].apply(settings)

    def __repr__(self):
        return f"wave({self._length})"


class Wave2Effect(BitEffect):
    class Bit():
        _SIN_SEQUENCE_LENGTH = 30
        _sin_sequence = _initialize_sin_sequence(_SIN_SEQUENCE_LENGTH)

        def __init__(self, index: int):
            self._index = index
            self._amplitude = (2, 3.5)
            self._count = 0

        def apply(self, settings: TextSettings):
            idx = (self._count + self._index *
                   self._SIN_SEQUENCE_LENGTH // 10) % self._SIN_SEQUENCE_LENGTH
            x_offset = settings.offset[0] + \
                self._sin_sequence[idx] * self._amplitude[0]
            y_offset = settings.offset[1] + \
                self._sin_sequence[idx] * self._amplitude[1]
            settings.offset = (x_offset, y_offset)
            self._count = (self._count + 1) % self._SIN_SEQUENCE_LENGTH

    def __init__(self):
        self._length = 0
        self._bits: List[self.Bit] = []

    def set_length(self, length: int):
        self._length = length
        self._bits = [self.Bit(x) for x in range(length)]

    def apply(self, settings: TextSettings, bit: int):
        if not self._bits:
            raise Exception(
                "WaveEffect length not initialized, must call set_length()")
        self._bits[bit].apply(settings)

    def __repr__(self):
        return f"wave({self._length})"
