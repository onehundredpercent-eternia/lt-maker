from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from app.map_maker.terrain import Terrain
from app.utilities.typing import NID

# Default mapping from map_maker Terrain enum members to DB terrain nids.
# Matches the terrain nids present in default.ltproj/game_data/terrain.json.
DEFAULT_ASSOCIATIONS: Dict[Terrain, NID] = {
    Terrain.GRASS: '1',            # Plain
    Terrain.LIGHT_GRASS: '1',
    Terrain.NOISY_GRASS: '1',
    Terrain.SAND: 'Sand',
    Terrain.ROAD: '7',             # Road
    Terrain.DESERT: 'Desert',
    Terrain.SPARSE_FOREST: '1',    # Plain
    Terrain.FOREST: '2',           # Forest
    Terrain.THICKET: '3',          # Thicket
    Terrain.CLIFF: '22',           # Cliff
    Terrain.DESERT_CLIFF: '22',
    Terrain.DESERT_ROCK: '22',
    Terrain.HILL: '20',            # Hill
    Terrain.MOUNTAIN: '21',        # Mountain
    Terrain.RIVER: '12',           # River
    Terrain.SEA: '11',             # Sea
    Terrain.POOL: '10',            # Lake
    Terrain.BRIDGEH: '4',          # Bridge
    Terrain.BRIDGEV: '4',
    Terrain.POOL_BRIDGE: '4',
    Terrain.HOUSE: '30',           # House
    Terrain.CASTLE: '31',          # Fort
    Terrain.RUINS: 'Ruins',
    Terrain.VOID: '0',             # --
    Terrain.WALL_TOP: '9',         # Wall
    Terrain.WALL_BOTTOM: '9',
    Terrain.COLUMN: '9',
    Terrain.FLOOR_1: '6',          # Floor
    Terrain.FLOOR_2: '6',
    Terrain.FLOOR_3: '6',
    Terrain.STAIRS_UPDOWN: '5',    # Stairs
    Terrain.STAIRS_LEFT: '5',
    Terrain.STAIRS_RIGHT: '5',
    Terrain.STAIRS_CENTER: '5',
    Terrain.PILLAR: '8',           # Pillar
    Terrain.TREASURE: '36',        # Chest
}

# Fallback nid used when a Terrain has neither a project override nor a
# default association.
FALLBACK_NID: NID = '0'


class MapTerrainAssociations():
    """Per-project override table mapping map_maker Terrain enum members to
    DB terrain nids.

    Lookup order for `get`: project override -> DEFAULT_ASSOCIATIONS -> '0'.
    """

    def __init__(self) -> None:
        self.overrides: Dict[Terrain, NID] = {}

    def get(self, terrain: Terrain) -> NID:
        if terrain in self.overrides:
            return self.overrides[terrain]
        if terrain in DEFAULT_ASSOCIATIONS:
            return DEFAULT_ASSOCIATIONS[terrain]
        return FALLBACK_NID

    def set(self, terrain: Terrain, nid: NID) -> None:
        self.overrides[terrain] = nid

    def clear(self, terrain: Terrain) -> None:
        if terrain in self.overrides:
            del self.overrides[terrain]

    def clear_all(self) -> None:
        self.overrides.clear()

    def save(self) -> List[Tuple[str, NID]]:
        return [(terrain.name, nid) for terrain, nid in self.overrides.items()]

    def restore(self, data: Optional[List[Tuple[str, NID]]]) -> None:
        self.overrides = {}
        if not data:
            return
        for terrain_name, nid in data:
            try:
                terrain = Terrain[terrain_name]
            except KeyError:
                logging.warning(
                    "MapTerrainAssociations: Unknown Terrain name %s, skipping...",
                    terrain_name)
                continue
            self.overrides[terrain] = nid
