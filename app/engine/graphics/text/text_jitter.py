from random import Random
from typing import Tuple

class JitterXY():
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class TextJitter():
    rng = Random()

    @staticmethod
    def get_jitter(magnitude: float = 1) -> JitterXY:
        return JitterXY(TextJitter.rng.gauss(0, 1) * magnitude, TextJitter.rng.gauss(0, 1) * magnitude)