from __future__ import annotations

from typing import List

from enum import StrEnum

class Terrain(StrEnum):
    GRASS = 'Grass'

    @staticmethod
    def list() -> List["Terrain"]:
        return [_ for _ in Terrain]

    @staticmethod
    def name_list() -> List[str]:
        return [t.value for t in Terrain]

    @staticmethod
    def cliff(terrain: "Terrain") -> bool:
        return terrain in (Terrain.CLIFF, )
