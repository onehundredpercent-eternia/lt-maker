from random import Random
from typing import Tuple

_rng = Random()

def get_jitter(magnitude: float = 1) -> Tuple[float, float]:
    return (_rng.gauss(0, 1) * magnitude, _rng.gauss(0, 1) * magnitude)