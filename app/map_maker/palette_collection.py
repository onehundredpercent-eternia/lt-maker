from typing import Any, Dict
import glob, json, os

from dataclasses import dataclass, field

from app.utilities.data import Data
from app.map_maker.terrain import Terrain
from app.map_maker.qt_renderers.qt_palette import QtPalette

@dataclass
class PaletteCollection:
    nid: str
    name: str
    author: str
    palette_dir: str
    outdoor: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    palettes: Dict[Terrain, QtPalette] = field(default_factory=dict)

    def get_palette(self, terrain: Terrain) -> QtPalette:
        return self.palettes.get(terrain)

    def load_palettes(self):
        self.palettes = {
            Terrain.GRASS: QtPalette(os.path.join(self.palette_dir, 'grass.png')),
        }

class MapMakerPaletteCatalog(Data[PaletteCollection]):
    datatype = PaletteCollection

def load_all_palettes():
    valid_palette_folders = glob.glob('app/map_maker/palettes/*')
    for fn in valid_palette_folders:
        metadata_path = os.path.join(fn, 'metadata.json')
        if os.path.isdir(fn) and os.path.exists(metadata_path):
            # Read metadata
            with open(metadata_path) as fp:
                metadata = json.load(fp)
                new_palette = PaletteCollection(
                    metadata['name'], 
                    metadata['name'], 
                    metadata['author'], 
                    metadata.get('outdoor', True),
                    fn, 
                    metadata
                )
                PALETTES.append(new_palette)

PALETTES = MapMakerPaletteCatalog()
load_all_palettes()

CURRENT_PALETTE = PALETTES[0]

def get_current_palette_collection():
    return CURRENT_PALETTE

def set_current_palette_collection(idx: int):
    global CURRENT_PALETTE
    CURRENT_PALETTE = PALETTES[idx]
