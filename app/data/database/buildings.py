from typing import Optional, Tuple

import app.engine.building_component_access as BCA
from app.data.category import CategorizedCatalog
from app.data.database.building_components import BuildingComponent
from app.utilities.data import Data, Prefab
from app.utilities.typing import NID, Pos
from app.utilities import str_utils


class BuildingPrefab(Prefab):
    nid: str
    name: str
    desc: str
    terrain: NID
    map_sprite_nid: NID
    size: Tuple[int, int]
    components: Data[BuildingComponent]
    starting_position = Optional[Pos]

    def __init__(self, nid, name, desc, terrain, map_sprite_nid=None, starting_position=None,
                 components=None, size=(1, 1)):
        self.nid = nid
        self.name = name
        self.desc = desc
        self.terrain = terrain

        self.map_sprite_nid = map_sprite_nid
        # Gameplay footprint in tiles, anchored at the top left. Deliberately
        # explicit rather than derived from the sprite's dimensions.
        self.size = tuple(size)
        self.starting_position = starting_position

        self.components = components or Data[BuildingComponent]()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value

    def add_component(self, component: BuildingComponent):
        self.components.append(component)
        self.__dict__[component.nid] = component

    def remove_component(self, component: BuildingComponent):
        self.components.delete(component)
        del self.__dict__[component.nid]

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __getitem__(self, key):
        return self.__dict__.get(key)

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def save(self):
        serial_dict = {'nid': self.nid,
                       'name': self.name,
                       'desc': self.desc,
                       'terrain': self.terrain,
                       'map_sprite_nid': self.map_sprite_nid,
                       'size': self.size,
                       'starting_position': self.starting_position,
                       'components': [c.save() for c in self.components]
                       }
        return serial_dict

    @classmethod
    def restore(cls, dat):
        building_components = Data()
        components = [BCA.restore_component(val) for val in dat['components']]
        components = [c for c in components if c]
        for component in components:
            building_components.append(component)
        i = cls(dat['nid'], dat['name'], dat['desc'], dat['terrain'],
                dat['map_sprite_nid'], dat['starting_position'],
                building_components, dat.get('size', (1, 1)))
        return i

class BuildingCatalog(CategorizedCatalog[BuildingPrefab]):
    datatype = BuildingPrefab

    def create_new(self, db):
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Building", nids)
        new_building = BuildingPrefab(nid, name, '', db.terrain[0].nid)
        self.append(new_building)
        return new_building
