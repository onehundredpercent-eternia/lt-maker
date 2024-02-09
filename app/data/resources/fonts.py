from dataclasses import asdict, dataclass, field
from enum import Enum
import os, shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.data.database.game_flags import dataclass_from_dict

from app.data.resources.base_catalog import ManifestCatalog

class FontType(str, Enum):
    TTF = 'ttf'
    IMAGE = 'image'

@dataclass
class Font():
    nid: str                                                                             #: NID of the font.
    file_name: str = None                                                                #: Root path without file ending, e.g. `project.ltproj/resources/convo`.
    font_type: FontType = FontType.IMAGE                                                 #: Type of font this is. One of IMAGE or TTF.
    default_color: Optional[str] = None                                                  #: IMAGE only. The key of the default color in the palette, if any.
    palettes: Dict[str, List[Tuple[int, int, int]]] = field(default_factory=dict)        #: IMAGE only. A dictionary of color names to the palette of the font color.

    def image_path(self):
        if self.font_type == FontType.IMAGE:
            return self.file_name + '.png'

    def index_path(self):
        if self.font_type == FontType.IMAGE:
            return self.file_name + '.idx'

    def save(self):
        s_dict = asdict(self)
        del s_dict["file_name"]
        return s_dict

    @classmethod
    def restore(cls, s_dict):
        return dataclass_from_dict(cls, s_dict)

class FontCatalog(ManifestCatalog[Font]):
    datatype = Font
    manifest = 'fonts.json'
    title = 'fonts'
    filetype = ''

    def load(self, loc):
        resource_dict = self.read_manifest(os.path.join(loc, self.manifest))
        if len(resource_dict) == 0:
            self.load('default.ltproj/resources/fonts')
            return
        for s_dict in resource_dict:
            new_resource = self.datatype.restore(s_dict)
            if new_resource.font_type == FontType.IMAGE:
                new_resource.file_name = os.path.join(loc, new_resource.nid)
            self.append(new_resource)

    def save(self, loc):
        for datum in self:
            new_idx_path = os.path.join(loc, datum.nid + '.idx')
            if os.path.abspath(datum.index_path()) != os.path.abspath(new_idx_path):
                self.make_copy(datum.index_path(), new_idx_path)
            new_image_path = os.path.join(loc, datum.nid + '.png')
            if os.path.abspath(datum.image_path()) != os.path.abspath(new_image_path):
                self.make_copy(datum.image_path(), new_image_path)
            datum.file_name = os.path.join(loc, datum.nid)
        self.dump(loc)