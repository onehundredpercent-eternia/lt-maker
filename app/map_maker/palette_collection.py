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

    def get(self, terrain: Terrain) -> QtPalette:
        return self.palettes.get(terrain)

    def load_palettes(self):
        self.palettes = {
            Terrain.GRASS: QtPalette(os.path.join(self.palette_dir, 'grass.png')),
            Terrain.LIGHT_GRASS: QtPalette(os.path.join(self.palette_dir, 'grass.png')),
            Terrain.NOISY_GRASS: QtPalette(os.path.join(self.palette_dir, 'grass.png')),
            Terrain.SAND: QtPalette(os.path.join(self.palette_dir, 'sand.png')),
            Terrain.ROAD: QtPalette(os.path.join(self.palette_dir, 'road.png')),
            Terrain.RIVER: QtPalette(os.path.join(self.palette_dir, 'river.png'), os.path.join(self.palette_dir, 'river_autotiles.png')),
            Terrain.SEA: QtPalette(os.path.join(self.palette_dir, 'sea.png'), os.path.join(self.palette_dir,  'sea_autotiles.png')),
            Terrain.FOREST: QtPalette(os.path.join(self.palette_dir, 'forest.png')),
            Terrain.THICKET: QtPalette(os.path.join(self.palette_dir, 'main.png')),
            Terrain.HILL: QtPalette(os.path.join(self.palette_dir, 'main.png')),
            Terrain.MOUNTAIN: QtPalette(os.path.join(self.palette_dir, 'main.png')),
            Terrain.CLIFF: QtPalette(os.path.join(self.palette_dir, 'cliff.png')),
            Terrain.BRIDGEH: QtPalette(os.path.join(self.palette_dir, 'bridge_h.png')),
            Terrain.BRIDGEV: QtPalette(os.path.join(self.palette_dir, 'bridge_v.png')),
            Terrain.CASTLE: QtPalette(os.path.join(self.palette_dir, 'main.png')),
            Terrain.HOUSE: QtPalette(os.path.join(self.palette_dir, 'main.png')),
            Terrain.RUINS: QtPalette(os.path.join(self.palette_dir, 'main.png')),
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
                    fn, 
                    metadata.get('outdoor', True),
                    metadata
                )
                new_palette.load_palettes()
                PALETTES.append(new_palette)

PALETTES = MapMakerPaletteCatalog()
load_all_palettes()

CURRENT_PALETTE = PALETTES[0]

def get_current_palette_collection():
    return CURRENT_PALETTE

def set_current_palette_collection(idx: int):
    global CURRENT_PALETTE
    CURRENT_PALETTE = PALETTES[idx]
