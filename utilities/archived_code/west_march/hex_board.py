import heapq

from enum import Enum
from typing import Dict, List, Tuple, TYPE_CHECKING

# if TYPE_CHECKING:
from app.constants import TILEWIDTH, TILEHEIGHT
from app.data.hex_prefab import HexPrefab
from app.data.hex_type import HexType

from app.utilities import hex_math
from app.utilities.typing import NID
from app.data.overworld import OverworldPrefab

from app.data.database import DB


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
    def pixel_pos(self) -> tuple:
        # Returns pixel position
        return hex_math.hex_to_pixel(self.pos)

    @property
    def position(self):
        return self.pixel_pos[0] / TILEWIDTH, self.pixel_pos[1] / TILEHEIGHT

    def save(self):
        return (self.pos, self.sight)

    @classmethod
    def restore(cls, dat):
        pos = tuple(dat[0])
        return cls(pos, dat[1])

class HexBoard():
    def __init__(self, overworld_prefab: OverworldPrefab):
        self.hexes: Dict[hex_math.Hex, HexPrefab] = overworld_prefab.hexes.copy()

        self.hex_graph = {}  # Store Hex Data
        for hex_prefab in self.hexes.values():
            hex_data = HexData(hex_prefab.pos)
            self.hex_graph[hex_data.pos] = hex_data

        self.assign_adjacency()

    def assign_adjacency(self):
        for hex_data in self.hex_graph.values():
            potential_neighbors: List[hex_math.Hex] = hex_math.get_neighbors(hex_data.pos)
            for neighbor in potential_neighbors:
                if neighbor in self.hex_graph:
                    hex_data.adjacency.append(neighbor)

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

    def get_name(self, pos) -> str:
        hex_prefab = self.hexes.get(pos)
        if hex_prefab:
            if hex_prefab.name:
                return hex_prefab.name
            elif DB.hex_types.get(hex_prefab.hex_type):
                return DB.hex_types.get(hex_prefab.hex_type).name
        return ''

    def get_mcost(self, pos) -> float:
        hex_type_nid = self.get_hex_type(pos)
        hex_type = DB.hex_types.get(hex_type_nid)
        if hex_type:
            return hex_type.movement_cost
        return 1

    def get_adj(self, pos) -> List[hex_math.Hex]:
        hex_data = self.hex_graph.get(pos)
        if hex_data:
            return hex_data.adjacency
        return []

    def get_sight(self, pos) -> Sight:
        hex_data = self.hex_graph.get(pos)
        if hex_data:
            return hex_data.sight
        return Sight.UNEXPLORED

    def _update_fow(self, pos: hex_math.Hex, sight_range: int, new_sight: Sight):
        positions_in_range: List[hex_math.Hex] = hex_math.get_all_hex_within_distance(pos, sight_range)
        for hex_pos in positions_in_range:
            hex_data = self.hex_graph.get(hex_pos)
            if hex_data:
                hex_data.sight = new_sight

    def fow_leave(self, pos: hex_math.Hex, sight_range: int = 2):
        self._update_fow(pos, sight_range, Sight.EXPLORED)
        
    def fow_arrive(self, pos: hex_math.Hex, sight_range: int = 2):
        self._update_fow(pos, sight_range, Sight.INSIGHT)

    def has_path(self, a: hex_math.Hex, b: hex_math.Hex, only_visible=False) -> bool:
        """
        Returns whether there is a path between two hexes
        """
        pathfinding = HexPathfinding(self, b)
        path = pathfinding.process_astar(a, only_visible)
        if path:
            return True
        return False

    def shortest_path(self, a: hex_math.Hex, b: hex_math.Hex, only_visible=False) -> List[hex_math.Hex]:
        """
        Returns the shortest path between the two hexes
        """
        pathfinding = HexPathfinding(self, b)
        return pathfinding.process_astar(a, only_visible)

class HexPathfinding():
    def __init__(self, hex_board: HexBoard, end: hex_math.Hex):
        self.hex_board = hex_board
        self.heuristic_data: Dict[hex_math.Hex, tuple] = {} # Dictionary that contains heuristic data
        self.parent_data: Dict[hex_math.Hex, hex_math.Hex] = {}  # Dictionary that contians parent data for each hex

        self.open = []
        self.closed = set()

        self.end = end

    def reset(self):
        self.heuristic_data.clear()
        self.parent_data.clear()
        for hex_pos in self.hex_board.hex_graph:
            self.heuristic_data[hex_pos] = [0, 0, 0]
            self.parent_data[hex_pos] = None

        self.open = []
        heapq.heapify(self.open)
        self.closed.clear()

    def get_heuristic(self, pos: hex_math.Hex) -> float:
        return hex_math.calculate_distance(pos, self.end)

    def update_hex(self, adj: hex_math.Hex, pos: hex_math.Hex):
        pos_g = self.heuristic_data[pos][1]
        adj_g = pos_g + self.hex_board.get_mcost(adj)
        self.heuristic_data[adj][1] = adj_g
        adj_h = self.get_heuristic(adj)
        self.heuristic_data[adj][2] = adj_h
        adj_f = adj_g + adj_h
        self.heuristic_data[adj][0] = adj_f
        # Update parent
        self.parent_data[adj] = pos

    def return_path(self, pos: hex_math.Hex) -> List[hex_math.Hex]:
        path = []
        while pos:
            path.append(pos)
            pos = self.parent_data.get(pos)
        return path

    def process_astar(self, start: hex_math.Hex, only_visible=False) -> List[hex_math.Hex]:
        self.reset()
        start_f = self.heuristic_data[start][0]
        heapq.heappush(self.open, (start_f, start))
        while self.open:
            f, pos = heapq.heappop(self.open)
            # Don't process the hex twice
            self.closed.add(pos)
            # If ending cell, return path
            if pos == self.end:
                return self.return_path(pos)
            # Get adjacent hexes for hexes
            if only_visible:
                adj_hexes = [adj for adj in self.hex_board.get_adj(pos) if self.hex_board.get_sight(adj) in (Sight.INSIGHT, Sight.EXPLORED)]
            else:
                adj_hexes = [adj for adj in self.hex_board.get_adj(pos)]
            for adj in adj_hexes:
                if self.hex_board.get_mcost(adj) < 99 and adj not in self.closed:
                    adj_f = self.heuristic_data[adj][0] 
                    if (adj_f, adj) in self.open:
                        adj_g = self.heuristic_data[adj][1]
                        cur_g = self.heuristic_data[pos][1]
                        # check if current path is beter than the one previous found for this adj
                        if adj_g > cur_g + self.hex_board.get_mcost(adj):
                            self.update_hex(adj, pos)
                            adj_f = self.heuristic_data[adj][0] 
                            heapq.heappush(self.open, (adj_f, adj))
                    else:
                        self.update_hex(adj, pos)
                        adj_f = self.heuristic_data[adj][0] 
                        heapq.heappush(self.open, (adj_f, adj))
                else:
                    pass  # Cannot move to here
        return []
