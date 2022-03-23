from enum import Enum
from typing import Dict, List, Tuple, TYPE_CHECKING

# if TYPE_CHECKING:
from app.data.hex_prefab import HexPrefab
from app.data.hex_type import HexType

from app.utilities import hex_math
from app.utilities.typing import NID
from app.data.overworld import OverworldPrefab


class Sight(Enum):
    UNEXPLORED = 0
    EXPLORED = 1
    INSIGHT = 2

class HexData():
    def __init__(self, pos, sight=Sight.UNEXPLORED):
        self.pos: hex_math.Hex = pos
        self.adjacency: List[hex_math.Hex] = []
        self.sight: Sight = sight

    @property
    def position(self) -> tuple:
        # Returns pixel position
        return hex_math.hex_to_pixel(self.pos)

    def save(self):
        return ((self.pos.q, self.pos.r, self.pos.s), self.sight)

    @classmethod
    def restore(cls, dat):
        pos = hex_math.Hex(*dat[0])
        return cls(pos, dat[1])

class HexBoard():
    def __init__(self, overworld_prefab: OverworldPrefab):
        self.hexes: Dict[Tuple, HexPrefab] = overworld_prefab.hexes.copy()

        self.hex_graph = {}  # Store Hex Data
        for hex_prefab in self.hexes:
            hex_data = HexData(hex_prefab.pos)
            self.hex_graph[hex_data.pos] = hex_data

        self.assign_adjacency()

    def assign_adjacency(self):
        for hex_data in self.hex_graph:
            potential_neighbors: List[hex_math.Hex] = hex_math.get_neighbors(hex_data.pos)
            for neighbor in potential_neighbors:
                if neighbor in self.hex_graph:
                    self.hex_graph.adjacency.append(neighbor)

    def save(self):
        return [h.save() for h in self.hex_graph.values()]

    def restore(self, hex_graph_data):
        self.hex_graph.clear()
        for dat in hex_graph_data:
            hex_data = HexData.restore(dat)
            self.hex_graph[hex_data.pos] = hex_data

        self.assign_adjacency()

    def get_hex_type(self, pos) -> HexType:
        hex_prefab = self.hexes.get(pos)
        if hex_prefab:
            return hex_prefab.hex_type
        return None

    def get_mcost(self, pos) -> float:
        hex_type = self.get_hex_type(pos)
        if hex_type:
            return hex_type.movement_cost
        return 1

    def _update_fow(self, pos: hex_math.Hex, sight_range: int, new_sight: Sight):
        positions_in_range: List[hex_math.Hex] = hex_math.get_all_hex_in_distance(pos, sight_range)
        for hex_pos in positions_in_range:
            hex_data = self.hex_graph.get(hex_pos)
            if hex_data:
                hex_data.sight = new_sight

    def fow_leave(self, pos: hex_math.Hex, sight_range: int = 2):
        self._update_fow(pos, sight_range, Sight.EXPLORED)
        
    def fow_arrive(self, pos: hex_math.Hex, sight_range: int = 2):
        self._update_fow(pos, sight_range, Sight.INSIGHT)
