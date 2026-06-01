from typing import List, Set
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
    """
    def __init__(self, nid: NID):
        self.nid: NID = nid
        self.name: str = ""
        self.position: Pos = None
        self.team: NID = None

        self.population: int = 1

    def contains(self, pos: Pos) -> bool:
        """
        Check if the given position is within the city's influence

        Args:
            pos (Pos): The position to check.

        Returns:
            bool: True if the position is within the city's influence, False otherwise.
        """
        x, y = pos
        if self.position:
            return utils.calculate_distance(self.position, pos) <= self.influence
        else:
            return False

    def get_all_positions(self) -> Set[Pos]:
        """
        Get all positions covered by the city's influence.

        Returns:
            Set[Pos]: A set of all positions covered by the city's influence.
        """
        if self.position:
            positions = set()
            for r in range(1, self.influence):
                for i in range(-r, r+1):
                    magn = abs(i)
                    dx = i
                    dy = r - magn
                    positions.add((dx, dy))
                    positions.add((dx, -dy))
            return positions
        else:
            return set()

    @classmethod
    def default(cls):
        return cls('None')
