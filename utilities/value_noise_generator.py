import random, math

from PIL import Image

class ValueNoise():
    num_octaves = 5
    pixels_per_lattice = 24
    pixel_depth = 48 * 4

    def __init__(self, width: int, height: int):
        self.pixel_width = width
        self.pixel_height = height
        self.lattice_width = width // self.pixels_per_lattice
        self.lattice_height = height // self.pixels_per_lattice
        self.lattice_depth = self.pixel_depth // self.pixels_per_lattice
        self.lattice_depth //= 4

        self.noise_map = self.generate_full_noise_map()

    def generate_full_noise_map(self):
        frequency = 0.25
        frequency_mult = 2  # lacunarity
        amplitude_mult = 0.35
        amplitude = 1
        true_noise_map = [0 for _ in range(self.pixel_width * self.pixel_height * self.pixel_depth)]
        for i in range(self.num_octaves):
            print("Octave: %d" % i)
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
        randoms = [random.random() for _ in range(self.lattice_width * self.lattice_height * self.lattice_depth)]
        noise_map = []
        for pz in range(self.pixel_depth):
            print(pz)
            for px in range(self.pixel_width):
                for py in range(self.pixel_height):
                    lx = px * frequency / self.pixels_per_lattice
                    ly = py * frequency / self.pixels_per_lattice
                    lz = pz * frequency / self.pixels_per_lattice
                    lx %= self.lattice_width
                    ly %= self.lattice_height
                    lz %= self.lattice_depth
                    flx = math.floor(lx)
                    fly = math.floor(ly)
                    flz = math.floor(lz)
                    tx = lx - flx
                    ty = ly - fly
                    tz = lz - flz
                    rx0 = flx
                    rx1 = (flx + 1) % self.lattice_width
                    ry0 = fly
                    ry1 = (fly + 1) % self.lattice_height
                    rz0 = flz
                    rz1 = (flz + 1) % self.lattice_depth
                    c000 = randoms[rz0 * self.lattice_width * self.lattice_height + rx0 * self.lattice_height + ry0]
                    c010 = randoms[rz0 * self.lattice_width * self.lattice_height + rx0 * self.lattice_height + ry1]
                    c001 = randoms[rz0 * self.lattice_width * self.lattice_height + rx1 * self.lattice_height + ry0]
                    c011 = randoms[rz0 * self.lattice_width * self.lattice_height + rx1 * self.lattice_height + ry1]
                    c100 = randoms[rz1 * self.lattice_width * self.lattice_height + rx0 * self.lattice_height + ry0]
                    c110 = randoms[rz1 * self.lattice_width * self.lattice_height + rx0 * self.lattice_height + ry1]
                    c101 = randoms[rz1 * self.lattice_width * self.lattice_height + rx1 * self.lattice_height + ry0]
                    c111 = randoms[rz1 * self.lattice_width * self.lattice_height + rx1 * self.lattice_height + ry1]
                    nx00 = self._interp(c000, c001, tx)
                    nx01 = self._interp(c010, c011, tx)
                    nx10 = self._interp(c100, c101, tx)
                    nx11 = self._interp(c110, c111, tx)
                    ny0 = self._interp(nx00, nx01, ty)
                    ny1 = self._interp(nx10, nx11, ty)
                    final = self._interp(ny0, ny1, tz)
                    # print("px:%d py:%d %.2f %.2f %d %d %d %d tx:%.2f ty:%.2f c00:%.2f c10:%.2f c01:%.2f c11:%.2f f:%.2f" % (px, py, lx, ly, rx0, rx1, ry0, ry1, tx, ty, c00, c10, c01, c11, final))
                    noise_map.append(final)
        return noise_map

    def noise_map_to_pillow(self, noise_map, pz):
        new_image = Image.new('RGB', (self.pixel_width, self.pixel_height))
        for px in range(self.pixel_width):
            for py in range(self.pixel_height):
                noise_value = int(255 * noise_map[pz * self.pixel_width * self.pixel_height + px * self.pixel_height + py])
                new_image.putpixel((px, py), (noise_value, noise_value, noise_value))
        new_image.save("im%03d.png" % pz)

    def save_img(self):
        for pz in range(self.pixel_depth):
            self.noise_map_to_pillow(self.noise_map, pz)

VALUE_NOISE = ValueNoise(384, 216)
VALUE_NOISE.save_img()
