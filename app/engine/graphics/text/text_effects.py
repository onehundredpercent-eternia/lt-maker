from __future__ import annotations
from typing import Tuple, List

from random import Random

from app.utilities.typing import NID
from app.utilities.utils import tuple_add

class TextSetting():
    def __init__(self, color: NID, offset: Tuple[float, float]):
        self.color = color
        self.offset = offset

    def apply(self, effects: List[TextEffect]):
        for effect in effects:
            effect.apply(self)

class TextEffect():
    def __init__(self):
        raise Exception("TextEffect should not be directly instantiated")
    def apply(self, setting: TextSetting):
        # modifies setting
        pass

class ColorEffect(TextEffect):
    def __init__(self, color: NID):
        self._color = color
    def apply(self, setting: TextSetting):
        setting.color = self._color
    def __repr__(self):
        return f"color({self._color})"

class JitterEffect(TextEffect):
    _rng = Random()
    def get_jitter(magnitude: float = 1) -> Tuple[float, float]:
        return (JitterEffect._rng.gauss(0, 1) * magnitude, JitterEffect._rng.gauss(0, 1) * magnitude)

    def __init__(self):
        self._jitter = (0, 0)
        self._count = 0
    def apply(self, setting: TextSetting):
        if self._count % 3 == 1:
            self._jitter = JitterEffect.get_jitter()
        self._count += 1
        self._count = self._count % 3 # prevent infinitely counting up
        setting.offset = tuple_add(setting.offset, self._jitter)
    def __repr__(self):
        return f"jitter({self._jitter[0]:.2f},{self._jitter[1]:.2f})"
