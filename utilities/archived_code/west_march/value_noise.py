import glob

from app.engine import engine

class ValueNoise():
    transparency = 16  # 0 - 255 (opaque)
    speed = 50  # ms

    def __init__(self):
        self.ims = [engine.image_load(im) for im in glob.glob('fog/im*.png')]
        self.reset_transparency()

    def reset_transparency(self):
        for im in self.ims:
            im.set_alpha(self.transparency)

    def draw(self, surf):
        pz = int(engine.get_time() // self.speed) % len(self.ims)
        im = self.ims[pz]
        surf.blit(im, (0, 0))
        return surf
