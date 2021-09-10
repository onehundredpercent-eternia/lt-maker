import math, random

from dataclasses import dataclass

from app.constants import TILEWIDTH, TILEHEIGHT
from app.engine.sprites import SPRITES

from app.engine import engine, image_mods
from app.engine.game_state import game
from app.utilities import utils

@dataclass
class FogParticle():
    x: float = 0
    y: float = 0
    x_speed: float = 0
    y_speed: float = 0
    size: int = 0
    transparency: float = 0
    time_offset: float = 0

class FogParticleSystem():
    def __init__(self, nid, abundance, bounds, size):
        width, height = size
        self.nid = nid
        self.abundance = int(abundance * width * height)
        self.particles = []
        self.remove_me_flag = False

        self.lx, self.ux, self.ly, self.uy = bounds

        # Build sprites
        _fog_sprite = SPRITES.get('particle_fog_mote')
        _fog_sprites = [engine.subsurface(_fog_sprite, (0, 0, 3, 3)),
                        engine.subsurface(_fog_sprite, (3 + 1, 0, 5, 5)),
                        engine.subsurface(_fog_sprite, (8 + 2, 0, 7, 7)),
                        engine.subsurface(_fog_sprite, (15 + 3, 0, 9, 9)),
                        engine.subsurface(_fog_sprite, (24 + 4, 0, 11, 11))]
        self.transparencies = []
        for sprite in _fog_sprites:
            self.transparencies.append([image_mods.make_translucent(sprite, k) for k in (0.9, 0.92, 0.94, 0.96, 0.98, 1.0)])
    
    def save(self):
        return self.nid

    def add_particle(self, x, y):
        transparency = .8
        time_offset = random.randrange(0, 100) * 100
        size = random.randrange(0, 5)
        speed = utils.clamp(random.normalvariate(1, .5), 0.1, 5)
        angle = random.uniform(315, 359) * math.pi / 180
        x_speed = speed * (2.5 - size/2) * math.cos(angle)
        y_speed = speed * (2.5 - size/2) * math.sin(angle)
        new_particle = FogParticle(x, y, x_speed, y_speed, size, transparency, time_offset)
        return new_particle
        
    def update(self):
        current_time = engine.get_time()

        for particle in self.particles:
            particle.x += particle.x_speed
            particle.y -= particle.y_speed
            t_offset = math.sin((current_time + particle.time_offset) / 500)
            particle.transparency = .95 + 0.1 * t_offset

        # Remove particles that have left the map
        self.particles = [p for p in self.particles if (p.x < game.tilemap.width * TILEWIDTH and p.y < game.tilemap.height * TILEHEIGHT)]

        if len(self.particles) < self.abundance:
            xpos = random.randint(self.lx, self.ux)
            ypos = random.randint(self.ly, self.uy)
            new_particle = self.add_particle(xpos, ypos)
            self.particles.append(new_particle)

        if self.abundance <= 0 and not self.particles:
            self.remove_me_flag = True

    def prefill(self):
        for _ in range(300):
            self.update()

    def draw(self, surf, offset_x=0, offset_y=0):
        for particle in self.particles:
            closest_transparency = utils.clamp(particle.transparency, 0.9, 1.0)
            if 0.9 <= closest_transparency < 0.91:
                idx = 0
            elif 0.91 <= closest_transparency < 0.93:
                idx = 1
            elif 0.93 <= closest_transparency < 0.95:
                idx = 2
            elif 0.95 <= closest_transparency < 0.97:
                idx = 3
            elif 0.97 <= closest_transparency < 0.99:
                idx = 4
            else:
                idx = 5
            sprite = self.transparencies[particle.size][idx]
            surf.blit(sprite, (particle.x - offset_x, particle.y - offset_y))
