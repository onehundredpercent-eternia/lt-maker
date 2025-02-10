from __future__ import annotations

from typing import List

from enum import StrEnum

class Terrain(StrEnum):
    # Additional attribute
    outdoor: bool

    def __new__(
        cls, title: str, outdoor: bool = True
    ) -> Terrain:
        obj = cls.__new__(cls, title)
        obj._value_ = title

        obj.outdoor = outdoor
        return obj

    # Outdoors
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

    # Indoors
    VOID = ('Void', False)
    WALL_TOP = ('Wall Top', False)
    WALL_BOTTOM = ('Wall Bottom', False)
    FLOOR_1 = ('Floor 1', False)
    FLOOR_2 = ('Floor 2', False)
    STAIRS_UPDOWN = ('Stairs UpDown', False)
    STAIRS_LEFT = ('Stairs Left', False)
    STAIRS_RIGHT = ('Stairs Right', False)
    PILLAR = ('Pillar', False)

    @staticmethod
    def list() -> List["Terrain"]:
        return [_ for _ in Terrain]

    @staticmethod
    def indoor_terrain() -> List["Terrain"]:
        return [t for t in Terrain if not t.outdoor]

    @staticmethod
    def outdoor_terrain() -> List["Terrain"]:
        return [t for t in Terrain if t.outdoor]

    @staticmethod
    def name_list() -> List[str]:
        return [t.value for t in Terrain]

    @staticmethod
    def light_grass_adjacent(terrain: "Terrain") -> bool:
        return terrain in (Terrain.NOISY_GRASS, )

    @staticmethod
    def cliff(terrain: "Terrain") -> bool:
        return terrain in (Terrain.CLIFF, )
