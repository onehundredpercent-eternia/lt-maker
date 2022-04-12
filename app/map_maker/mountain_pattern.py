class MountainPattern():
    def __init__(self, coord, edge, ridges):
        self.coord: tuple = coord  # Position on tilemap
        self.edge_index: int = edge   # Wang 2-edge tiles
        self.ridges: list = ridges

    @property
    def top_edge(self) -> bool:
        return self.edge_index in (1, 3, 5, 7, 9, 11, 13, 15)

    @property
    def bottom_edge(self) -> bool:
        return self.edge_index in (4, 5, 6, 7, 12, 13, 14, 15)
    
    @property
    def left_edge(self) -> bool:
        return self.edge_index in (8, 9, 10, 11, 12, 13, 14, 15)

    @property
    def right_edge(self) -> bool:
        return self.edge_index in (2, 3, 6, 7, 10, 11, 14, 15)

    @staticmethod
    def edge_to_index(left=False, right=False, top=False, bottom=False) -> int:
        return bool(top) * 1 + bool(right) * 2 + bool(bottom) * 4 + bool(left) * 8

    
