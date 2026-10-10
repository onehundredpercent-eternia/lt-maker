from typing import List, Optional
from app.utilities.typing import NID, Pos

from app.data.database.database import DB
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
        food (int): The city's current food store, spent when buying units/buildings.
        production (int): The city's current production store, spent when buying units/buildings.
        produced_this_turn (bool): Whether the city has already bought its one unit or
            building this turn. Cleared at the start of the city's upkeep.
        razed (bool): Whether the city has been destroyed. A razed city is off the map
            for good but stays registered, so `game.cities` leaves it out while
            `game.get_city` still finds it.
    """

    def __init__(self, nid: NID, name: str, position: Pos = None, team: NID = "player",
                 population: int = 1, buildings: List = None, influence: int = 1, inn: List[NID] = None,
                 food: int = 0, production: int = 0,
                 icon_nid: NID = None, icon_index: tuple = (0, 0),
                 produced_this_turn: bool = False, razed: bool = False):
        self.nid = nid
        self.name = name
        self.position = position
        self.team = team
        self.population: int = population

        self.influence = influence
        self.buildings: List[BuildingObject] = buildings or []
        self.inn: List[NID] = inn or []

        self.food: int = food
        self.production: int = production
        self.produced_this_turn: bool = produced_this_turn
        self.razed: bool = razed

        self.icon_nid: NID = icon_nid
        self.icon_index: tuple = icon_index

        self.data = {}

    @classmethod
    def from_prefab(cls, prefab):
        # Lazy, like the rest of the engine's game_state reads: game_state imports the
        # object modules, so a module-level import here would cycle.
        from app.engine.game_state import game
        self = cls(prefab.nid, prefab.name,
                   tuple(prefab.position) if prefab.position else None,
                   prefab.team, prefab.population, [], prefab.influence,
                   icon_nid=prefab.icon_nid, icon_index=prefab.icon_index)
        # Instantiate the building placements assigned to the city in the editor
        for building_nid, position in (prefab.buildings or []):
            building_prefab = DB.buildings.get(building_nid)
            if not building_prefab:
                continue
            building = BuildingObject.from_prefab(building_prefab)
            building.position = tuple(position) if position else None
            building.owner_nid = self.nid
            self.buildings.append(building)
        # A team's city_pop_bonus techs apply to every city it gains, not only the ones
        # it owned when the tech unlocked.
        self.population += game.get_tech_value(prefab.team, 'city_pop_bonus')
        return self

    @property
    def center(self) -> Optional[BuildingObject]:
        """The building at the heart of the city (its Outpost or Town Hall): the one
        that carries the CityCenter component."""
        for building in self.buildings:
            if building.city_center:
                return building
        return None

    @property
    def is_outpost(self) -> bool:
        """Whether the city is still an outpost: its center carries the Outpost
        component. An outpost drafts no units and builds only OutpostBuildable buildings."""
        center = self.center
        return bool(center and center.outpost)

    @property
    def center_positions(self) -> List[Pos]:
        """Every tile of the city's center: the footprint of its center building. A
        city with no center building has the one-tile center of its own position."""
        center = self.center
        if center and center.position:
            return center.occupied_positions
        return super().center_positions

    def save(self) -> dict:
        serial_dict = {}
        serial_dict['nid'] = self.nid
        serial_dict['name'] = self.name
        serial_dict['position'] = self.position
        serial_dict['influence'] = self.influence
        serial_dict['team'] = self.team
        serial_dict['buildings'] = [building.uid for building in self.buildings]
        serial_dict['inn'] = self.inn

        serial_dict['population'] = self.population
        serial_dict['food'] = self.food
        serial_dict['production'] = self.production
        serial_dict['produced_this_turn'] = self.produced_this_turn
        serial_dict['razed'] = self.razed

        serial_dict['icon_nid'] = self.icon_nid
        serial_dict['icon_index'] = self.icon_index

        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def restore(cls, dat: dict, game):
        self = cls(dat['nid'], dat['name'], dat['position'], dat['team'],
                   dat['population'], [], dat['influence'],
                   dat['inn'], dat['food'], dat['production'],
                   dat.get('icon_nid'), dat.get('icon_index', (0, 0)),
                   dat.get('produced_this_turn', False),
                   dat.get('razed', False))
        self.buildings = [game.get_building(building_uid) for building_uid in dat['buildings']]
        self.buildings = [b for b in self.buildings if b]
        self.data = dat['data']
        return self
