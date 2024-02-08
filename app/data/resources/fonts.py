from collections import defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
import os, shutil
from typing import DefaultDict, Dict, List, Tuple
from app.data.database.game_flags import dataclass_from_dict

from app.data.resources.base_catalog import BaseResourceCatalog, ManifestCatalog

class FontType(Enum):
    TTF = 0
    IMAGE = 1

@dataclass
class Font():
    nid: str                                                #: NID of the font.
    full_path: str                                          #: Path to either the .idx file, or the .ttf file.
    palettes: Dict[str, List[Tuple[int, int, int]]]         #: IMAGE only: a dictionary of color names to the palette of the font color

    def __init__(self, nid, full_path=None):
        self.nid = nid
        self.full_path = full_path

        # for IMAGE fonts
        self.palettes

    def save(self):
        return asdict(self)

    def restore(self, d):
        if not d:
            return
        restored = dataclass_from_dict(self.__class__, d)
        self.__dict__ = restored.__dict__

class FontCatalog(ManifestCatalog[Font]):
    manifest = 'map_sprites.json'
    title = 'fonts'
    datatype = Font
    filetype = '.png'

    def move_resources()

    # I don't think move image or save are needed right now...
    def move_image(self, icon, loc):
        new_full_path = os.path.join(loc, icon.nid + self.filetype)
        if os.path.abspath(icon.full_path) != os.path.abspath(new_full_path):
            shutil.copy(icon.full_path, new_full_path)
            icon.set_full_path(new_full_path)

    def save(self, loc):
        for font in self:
            self.move_image(font, loc)

    def load(self, loc):
        font_dict = self.read_manifest(os.path.join(loc, self.manifest))
        if len(font_dict) == 0: # first time loading, load default fonts
            self.load_from_resources('default.ltproj/resources/fonts')

    def load_from_resources(self, loc):
        for root, dirs, files in os.walk(loc):
            for name in files:
                if name.endswith(self.filetype):
                    full_path = os.path.join(root, name)
                    nid = name[:-len(self.filetype)]
                    new_resource = self.datatype(nid, full_path)
                    self.append(new_resource)