import random

RANDOM_SEED = 0

def get_random_seed() -> int:
    return RANDOM_SEED

def set_random_seed(val: int):
    global RANDOM_SEED
    RANDOM_SEED = val

def random_choice(choices: list, pos: tuple, seed: int = None, offset: int = 0):
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed + pos[0] * 1024**2 + pos[1] * 1024 + offset)
    return random.choice(choices)
