from typing import List, Set, Tuple
from app.utilities.typing import NID, Pos

from app.utilities.data import Prefab
from app.utilities import utils
    
class City(Prefab):
    """
    A city prefab that has not been instantiated as a City Object yet

    Attributes:
        nid (NID): The unique identifier for the city object.
        name (str): The name of the city
        position (Pos): The position of the city object. Defaults to None.
        team (NID): The nid of the team that owns the city
        population (int): The city's current population.
        buildings (List[Tuple[NID, Pos]]): Building placements assigned to the
            city as (building_nid, position) pairs. Position is None until placed
            on the map. The same building type may appear more than once.
    """
    def __init__(self, nid: NID):
        self.nid: NID = nid
        self.name: str = nid
        self.position: Pos = None
        self.team: NID = None

        self.population: int = 1
        self.influence: int = 1

        self.buildings: List[Tuple[NID, Pos]] = []

        self.icon_nid: NID = None
        self.icon_index: tuple = (0, 0)

    def contains(self, pos: Pos) -> bool:
        """
        Check if the given position is within the city's influence

        Args:
            pos (Pos): The position to check.

        Returns:
            bool: True if the position is within the city's influence, False otherwise.
        """
        return any(utils.calculate_distance(center, pos) <= self.influence
                   for center in self.center_positions)

    @property
    def center_positions(self) -> List[Pos]:
        """
        Every tile of the city's center. A city prefab only knows its own position;
        a CityObject widens this to the footprint of its center building.
        """
        return [self.position] if self.position else []

    def positions_within(self, radius: int) -> Set[Pos]:
        """
        Get every tile within `radius` (Manhattan) of the city's center, measured from
        the nearest center tile. The center itself is not included.

        Args:
            radius (int): How far out from the center to reach.

        Returns:
            Set[Pos]: The tiles in range. Not clipped to the map.
        """
        center = self.center_positions
        positions = set()
        for cx, cy in center:
            for dx in range(-radius, radius + 1):
                reach = radius - abs(dx)
                for dy in range(-reach, reach + 1):
                    positions.add((cx + dx, cy + dy))
        positions.difference_update(center)
        return positions

    def get_all_positions(self) -> Set[Pos]:
        """
        Get all positions covered by the city's influence.

        Returns:
            Set[Pos]: A set of all positions covered by the city's influence.
        """
        return self.positions_within(self.influence)

    def restore_attr(self, name, value):
        # JSON has no tuples - coerce positions back so equality checks against
        # (x, y) tuples elsewhere (map view, contains) hold.
        if name == 'position' and value:
            return tuple(value)
        if name == 'buildings' and value:
            return [[building_nid, tuple(pos) if pos else None]
                    for building_nid, pos in value]
        return value

    @classmethod
    def default(cls):
        return cls('None')
