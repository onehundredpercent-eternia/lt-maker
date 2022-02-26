import math, random
from app.map_maker.utilities import get_random_seed

class ValueNoise():
    num_octaves = 3
    pixels_per_lattice = 4

    def __init__(self, width: int, height: int, seed: int):
        self.pixel_width = width
        self.pixel_height = height
        self.seed = seed
        random.seed(self.seed)
        self.lattice_width = width // self.pixels_per_lattice
        self.lattice_height = height // self.pixels_per_lattice

        self.noise_map = self.generate_full_noise_map()

    def generate_full_noise_map(self):
        frequency = 1.5
        frequency_mult = 2  # lacunarity
        amplitude_mult = 0.35
        amplitude = 1
        true_noise_map = [0 for _ in range(self.pixel_width * self.pixel_height)]
        for i in range(self.num_octaves):
            # print("Octave: %d" % i)
            noise_map = self.generate_noise_map(frequency)
            noise_map = [v * amplitude for v in noise_map]
            amplitude *= amplitude_mult
            frequency *= frequency_mult
            true_noise_map = [n + tn for n, tn in zip(noise_map, true_noise_map)]
        # normalize map
        max_value = max(true_noise_map)
        true_noise_map = [v / max_value for v in true_noise_map]
        return true_noise_map

    def _interp(self, a, b, t):
        # t should be in range 0 to 1
        remap_t = t * t * (3 - 2 * t)
        return a * (1 - remap_t) + b * remap_t

    def generate_noise_map(self, frequency):
        randoms = [random.random() for _ in range(self.lattice_width * self.lattice_height)]
        noise_map = []
        for px in range(self.pixel_width):
            for py in range(self.pixel_height):
                lx = px * frequency / self.pixels_per_lattice
                ly = py * frequency / self.pixels_per_lattice
                lx %= self.lattice_width
                ly %= self.lattice_height
                flx = math.floor(lx)
                fly = math.floor(ly)
                tx = lx - flx
                ty = ly - fly
                rx0 = flx
                rx1 = (flx + 1) % self.lattice_width
                ry0 = fly
                ry1 = (fly + 1) % self.lattice_height
                c00 = randoms[rx0 * self.lattice_height + ry0]
                c10 = randoms[rx0 * self.lattice_height + ry1]
                c01 = randoms[rx1 * self.lattice_height + ry0]
                c11 = randoms[rx1 * self.lattice_height + ry1]
                nx0 = self._interp(c00, c01, tx)
                nx1 = self._interp(c10, c11, tx)
                ny = self._interp(nx0, nx1, ty)
                noise_map.append(ny)
        return noise_map

    def get(self, x: int, y: int) -> float:
        x = x % 64
        y = y % 64
        noise_value = self.noise_map[x * self.pixel_height + y]
        return noise_value

VALUENOISE = None

def get_noise_map(width, height):
    global VALUENOISE
    new_width = 64 
    new_height = 64
    if VALUENOISE and VALUENOISE.pixel_width == new_width and VALUENOISE.pixel_height == new_height and VALUENOISE.seed == get_random_seed():
        return VALUENOISE
    else:  # Recreate with new width and height
        VALUENOISE = ValueNoise(new_width, new_height, get_random_seed())
        return VALUENOISE
