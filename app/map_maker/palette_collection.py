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
            # Outdoors
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
            # Indoors
            Terrain.VOID: QtPalette(os.path.join(self.palette_dir, 'void.png')),
            Terrain.FLOOR_1: QtPalette(os.path.join(self.palette_dir, 'floor1.png'), shading_fn=os.path.join(self.palette_dir, 'floor1_shading.png')),
            Terrain.FLOOR_2: QtPalette(os.path.join(self.palette_dir, 'floor2.png'), shading_fn=os.path.join(self.palette_dir, 'floor2_shading.png')),
        }

class MapMakerPaletteCatalog(Data[PaletteCollection]):
    datatype = PaletteCollection

    def outdoor_palettes(self) -> Data[PaletteCollection]:
        return Data([p for p in self.values() if p.outdoor])

    def indoor_palettes(self) -> Data[PaletteCollection]:
        return Data([p for p in self.values() if not p.outdoor])

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

CURRENT_INDOOR_PALETTE = PALETTES.indoor_palettes()[0]
CURRENT_OUTDOOR_PALETTE = PALETTES.outdoor_palettes()[0]

def get_current_indoor_palette_collection():
    return CURRENT_INDOOR_PALETTE

def get_current_outdoor_palette_collection():
    return CURRENT_OUTDOOR_PALETTE

def set_current_indoor_palette_collection(idx: int):
    global CURRENT_INDOOR_PALETTE
    CURRENT_INDOOR_PALETTE = PALETTES[idx]

def set_current_outdoor_palette_collection(idx: int):
    global CURRENT_OUTDOOR_PALETTE
    CURRENT_OUTDOOR_PALETTE = PALETTES[idx]
