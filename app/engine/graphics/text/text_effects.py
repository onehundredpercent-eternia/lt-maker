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
            effect.apply(self)


class TextEffect:
    """A text effect that applies a consistent effect to a text chunk"""

    nid: NID = None

    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")

    def __str__(self):
        return self.nid

    def update(self):
        """update the internal state of this TextEffect, should only be called once per frame"""
        pass

    def apply(self, settings: TextSettings):
        """modifies settings in place

        Args:
            settings (TextSettings): settings to modify
        """
        pass

    def as_tags(self) -> Tuple[str, str]:
        """recreate the starting and ending tags used for this text effect

        Returns:
            Tuple[str, str]: starting and ending tags for this
        """
        pass


class ColorEffect(TextEffect):
    nid = "color"

    def __init__(self, color: NID):
        self._color = color

    def __str__(self):
        return f"{self._color}"

    def apply(self, settings: TextSettings):
        settings.color = self._color

    def as_tags(self) -> Tuple[str, str]:
        return (f"<{self._color}>", "</>")


class JitterEffect(TextEffect):
    nid = "jitter"

    @classmethod
    def _get_jitter(klass, magnitude: float = 1) -> Tuple[float, float]:
        return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)

    def __init__(self, idx: int = 0, magnitude: float = 1, wait: int = 3):
        self._idx = idx
        self._magnitude = magnitude
        self._wait = wait

        self._jitter = self._jitter = self._get_jitter(self._magnitude)
        self._count = 0

    def update(self):
        # prevent infinitely counting up
        self._count = (self._count + 1) % self._wait
        if self._count % self._wait == 0:
            self._jitter = self._get_jitter(self._magnitude)

    def apply(self, settings: TextSettings):
        settings.offset = tuple_add(settings.offset, self._jitter)

    def as_tags(self) -> Tuple[str, str]:
        return (
            f"<{self.nid} idx={self._idx} magnitude={self._magnitude} wait={self._wait}>",
            "</>",
        )


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

    def update(self):
        self._count = (self._count + 1) % self._SIN_SEQUENCE_LENGTH

    def apply(self, settings: TextSettings):
        idx = (
            self._count + self._idx * self._SIN_SEQUENCE_LENGTH // 10
        ) % self._SIN_SEQUENCE_LENGTH
        x_offset = settings.offset[0] + self._sin_sequence[idx] * self._amplitude[0]
        y_offset = settings.offset[1] + self._sin_sequence[idx] * self._amplitude[1]
        settings.offset = (x_offset, y_offset)

    def as_tags(self) -> Tuple[str, str]:
        return (
            f"<{self.nid} idx={self._idx} x_amplitude={self._amplitude[0]} y_amplitude={self._amplitude[1]}>",
            "</>",
        )


class CoordinatedTextEffect:
    """A text effect that decays into a character wise application of impl_nid with incrementing idx.
    This class is only used for preprocessing and decays to a TextEffect applied per character after
    preprocessing. Depending on the implementation of the impl_nid text effect, and how it interacts
    with an idx variable, it can be used to generate coordinated text effects.
    """

    nid: NID = None
    impl_nid: NID = None

    def __init__(self):
        raise Exception("CoordinatedTextEffect should not be directly instantiated")

    def __str__(self):
        return self.nid

    def next(self) -> TextEffect:
        """generate the next text effect in the sequence to implement this coordinated effect

        Returns:
            TextEffect: the next text effect in the sequence
        """
        pass


class Jitter2Effect(CoordinatedTextEffect):
    nid = "jitter2"
    impl_nid = "jitter"

    def __init__(self, magnitude: float = 1, wait: int = 3):
        self._magnitude = magnitude
        self._wait = wait
        self._idx = 0

    def next(self) -> TextEffect:
        impl = TEXT_EFFECTS[self.impl_nid](self._idx, self._magnitude, self._wait)
        self._idx += 1
        return impl


class WaveEffect(CoordinatedTextEffect):
    nid = "wave"
    impl_nid = "sin"

    def __init__(self, amplitude: float = 3.5):
        self._amplitude = amplitude
        self._idx = 0

    def next(self) -> TextEffect:
        impl = TEXT_EFFECTS[self.impl_nid](self._idx, 0, self._amplitude)
        self._idx += 1
        return impl


class Wave2Effect(CoordinatedTextEffect):
    nid = "wave2"
    impl_nid = "sin"

    def __init__(self, x_amplitude: float = 2, y_amplitude: float = 3.5):
        self._amplitude = (x_amplitude, y_amplitude)
        self._idx = 0

    def next(self) -> TextEffect:
        impl = TEXT_EFFECTS[self.impl_nid](
            self._idx, self._amplitude[0], self._amplitude[1]
        )
        self._idx += 1
        return impl


TEXT_EFFECTS: Dict[NID, TextEffect] = {
    effect.nid: effect for effect in TextEffect.__subclasses__()
}

COORDINATED_TEXT_EFFECTS: Dict[NID, CoordinatedTextEffect] = {
    effect.nid: effect for effect in CoordinatedTextEffect.__subclasses__()
}
