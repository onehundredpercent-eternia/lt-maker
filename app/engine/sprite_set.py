from app.constants import TILEHEIGHT, TILEWIDTH
from app.engine import engine, image_mods
from app.utilities import str_utils, utils

# Generic Sprite Set Object
# Used, for instance, for miss and no damage animations
# And for map effects
# Basically just an ordered sequence of sprites that can be acted upon by tweens
# always 32-bit convert alpha images

class SpriteSet():
    def __init__(self, prefab, position):
        self.nid = prefab.nid
        if not prefab.image:
            prefab.image = engine.image_load(prefab.nid)
            prefab.image = prefab.image.convert_alpha()
            width = prefab.image.get_width() // prefab.frame_x
            height = prefab.image.get_height() // prefab.frame_y
            prefab.images = [engine.subsurface(prefab.image, (idx % prefab.frame_x, idx // prefab.frame_x, width, height)) for idx in range(prefab.num_frames)]
        self.images = prefab.images[:]
        self.num_frames = prefab.num_frames
        self.enabled = True

        self.tweens = []

    def save(self) -> tuple:
        return {'nid': self.nid}

    def update(self):
        current_time = engine.get_time()
        if not self.is_ready(current_time):
            return

        done = False
        if str_utils.is_int(self.speed):
            self.counter = int(current_time - self.first_update) // self.speed
            if self.counter >= self.num_frames:
                if self.loop:
                    self.counter = 0
                    self.first_update = current_time
                    self.delay = 0
                elif self.hold:
                    self.counter = self.num_frames - 1
                else:
                    self.counter = self.num_frames - 1
                    done = True
        else:  # Frame by frame timing
            num_frames = self.speed[self.counter]
            self.frames_held += 1
            if self.frames_held >= num_frames:
                self.frames_held = 0
                self.counter += 1
            if self.counter >= min(len(self.speed), self.num_frames):
                if self.loop:
                    self.counter = 0
                    self.frames_held = 0
                    self.delay = 0
                elif self.hold:
                    self.counter = self.num_frames - 1
                else:
                    self.counter = self.num_frames - 1
                    done = True

        if self.tint_after_delay == self.counter:
            self.tint = True

        # Now actually create image
        if self.reverse:
            frame_counter = self.num_frames - 1 - self.counter
        else:
            frame_counter = self.counter
        left = (frame_counter % self.frame_x) * self.width
        top = (frame_counter // self.frame_x) * self.height
        self.image = engine.subsurface(self.sprite, (left, top, self.width, self.height))

        return done

    def draw(self, surf, offset=None, blend=None):
        current_time = engine.get_time()
        if not self.is_ready(current_time):
            return surf
        x, y = self.get_position(offset)
        if blend:
            image = image_mods.change_color(self.image, blend)
        else:
            image = self.image
        if self.tint:
            engine.blit(surf, image, (x, y), None, engine.BLEND_RGB_ADD)
        else:
            surf.blit(image, (x, y))
        return surf

class MapAnimation(Animation):
    def __init__(self, anim, position, delay=0, loop=False, hold=False, reverse=False, speed_adj: float = 1):
        super().__init__(anim, position, delay, loop, hold, reverse, speed_adj=speed_adj)
        self.position = self.position[0] * TILEWIDTH, self.position[1] * TILEHEIGHT
        self.use_center()

    def use_center(self):
        self.position = self.position[0] + TILEWIDTH//2 - self.width//2, self.position[1] + TILEHEIGHT//2 - self.height//2

    def get_position(self, offset):
        if offset:
            return self.position[0] + offset[0] * TILEWIDTH, self.position[1] + offset[1] * TILEHEIGHT
        else:
            return self.position
