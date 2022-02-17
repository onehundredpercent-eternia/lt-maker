from app.constants import WINHEIGHT, WINWIDTH
import os
from dataclasses import dataclass
from app.engine import engine
from PyQt5.QtGui import QPixmap

@dataclass
class BasicSprite(object):
    nid: str = None
    full_path: str = None
    _pixmap: str = None
    image: engine.Surface = None

    @property
    def pixmap(self):
        if not self._pixmap:
            self._pixmap = QPixmap(self.full_path)
        return self._pixmap

    @pixmap.setter
    def pixmap(self, pm):
        self._pixmap = pm

@dataclass
class SpecialSprite(object):
    nid: str = None
    # pregenerated sprites, e.g. black screen/white screen
    full_path: str = None
    pixmap: str = None
    _image: engine.Surface = None

    # because these are pregenerated, they have to be converted only when used, with pygame initialized
    _converted: bool = False

    @property
    def image(self):
        if not self._converted:
            self._image = self._image.convert_alpha()
            self._converted = True
        return self._image

class SpriteDict(dict):
    def get(self, val):
        if val in self:
            return self[val].image
        return None

def load_sprites(root):
    for root, dirs, files in os.walk(root):
        for name in files:
            if name.endswith('.png'):
                full_name = os.path.join(root, name)
                SPRITES[name[:-4]] = BasicSprite(nid=name[:-4], full_path=full_name)

    for sprite in SPRITES.values():
        if sprite.full_path:
            sprite.image = engine.image_load(sprite.full_path)

def load_special_sprites():
    black_bg = engine.create_simple_surface((WINWIDTH, WINHEIGHT))
    black_bg_sprite = SpecialSprite(nid='bg_black', _image=black_bg)
    SPRITES['bg_black'] = black_bg_sprite

SPRITES = SpriteDict()
load_sprites('sprites/')
load_special_sprites()

def reset():
    SPRITES.clear()
    load_sprites('sprites/')
    load_special_sprites()
