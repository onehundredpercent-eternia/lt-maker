from __future__ import annotations

from typing import List

from enum import StrEnum

class Terrain(StrEnum):
    GRASS = 'Grass'
    LIGHT_GRASS = 'Light Grass'
    NOISY_GRASS = 'Noisy Grass'
    SAND = 'Sand'
    ROAD = 'Road'
    FOREST = 'Forest'
    THICKET = 'Thicket'
    CLIFF = 'Cliff'
    HILL = 'Hill'
    MOUNTAIN = 'Mountain'
    RIVER = 'River'
    SEA = 'Sea'
    BRIDGEH = 'Bridge H'
    BRIDGEV = 'Bridge V'
    HOUSE = 'House'
    CASTLE = 'Castle'
    RUINS = 'Ruins'

    # WALL_TOP = 'Wall Top'
    # WALL_BOTTOM = 'Wall Bottom'

    @staticmethod
    def list() -> List["Terrain"]:
        return [_ for _ in Terrain]

    @staticmethod
    def name_list() -> List[str]:
        return [t.value for t in Terrain]

    @staticmethod
    def light_grass_adjacent(terrain: "Terrain") -> bool:
        return terrain in (Terrain.NOISY_GRASS, )

    @staticmethod
    def cliff(terrain: "Terrain") -> bool:
        return terrain in (Terrain.CLIFF, )
