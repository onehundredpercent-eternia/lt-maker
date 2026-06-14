from typing import List
from app.utilities.typing import NID, Pos

from app.engine.objects.building import BuildingObject

from app.data.cities import City

class CityObject(City):
    """
    A city object in the game. Not the same as a City Prefab, which is the unchanging city you created in the level editor. 

    Inherits from the City Prefab to access City's helper functions.

    Attributes:
        nid (NID): The unique identifier for the city object.
        name (str): The name of the city
        position (Pos): The position of the city object. Defaults to None.
        team (NID): The nid of the team that owns the city
        population (int): The city's current population.
        buildings (List[BuildingObject]): The city's building object's attached.
        influence (int): The range of influence for the city
        inn (List[NID]): List of Unit Object NIDs that are stationed in this city
        production_queue (List): The units/buildings the city is currently working on. First in the queue is being built now.
        food (int): The city's current food.
        production (int): The city's current production.
    """

    def __init__(self, nid: NID, name: str, position: Pos = None, team: NID = "player",
                 population: int = 1, buildings: List = None, influence: int = 1, inn: List[NID] = None,
                 production_queue: List = None, food: int = 0, production: int = 0,
                 icon_nid: NID = None, icon_index: tuple = (0, 0)):
        self.nid = nid
        self.name = name
        self.position = position
        self.team = team
        self.population: int = population

        self.influence = influence
        self.buildings: List[BuildingObject] = buildings or []
        self.inn: List[NID] = inn or []
        self.production_queue: List = production_queue or []

        self.food: int = food
        self.production: int = production

        self.icon_nid: NID = icon_nid
        self.icon_index: tuple = icon_index

        self.data = {}

    @classmethod
    def from_prefab(cls, prefab):
        return cls(prefab.nid, prefab.name, prefab.position, prefab.team, prefab.population,
                   icon_nid=prefab.icon_nid, icon_index=prefab.icon_index)

    def save(self) -> dict:
        serial_dict = {}
        serial_dict['nid'] = self.nid
        serial_dict['name'] = self.name
        serial_dict['position'] = self.position
        serial_dict['influence'] = self.influence
        serial_dict['team'] = self.team
        serial_dict['buildings'] = [building.uid for building in self.buildings]
        serial_dict['inn'] = self.inn

        serial_dict['production_queue'] = self.production_queue

        serial_dict['population'] = self.population
        serial_dict['food'] = self.food
        serial_dict['production'] = self.production

        serial_dict['icon_nid'] = self.icon_nid
        serial_dict['icon_index'] = self.icon_index

        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def restore(cls, dat: dict, game):
        self = cls(dat['nid'], dat['name'], dat['position'], dat['team'],
                   dat['population'], [], dat['influence'],
                   dat['inn'], dat['production_queue'], dat['food'], dat['production'],
                   dat.get('icon_nid'), dat.get('icon_index', (0, 0)))
        self.buildings = [game.get_building(building_uid) for building_uid in dat['buildings']]
        self.buildings = [b for b in self.buildings if b]
        self.data = dat['data']
        return self
