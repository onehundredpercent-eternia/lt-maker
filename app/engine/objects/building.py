from __future__ import annotations
from typing import List, Tuple

from app.utilities.data import Data
from app.utilities.typing import Pos

from app.data.database.database import DB
import app.engine.building_component_access as BCA

class BuildingObject():
    next_uid = 100

    def __init__(self, nid, name, desc, terrain, map_sprite_nid, starting_position=None,
                 components=None, size=(1, 1)):
        self.uid = BuildingObject.next_uid
        BuildingObject.next_uid += 1

        self.nid = nid
        self.name = name

        self.owner_nid = None
        self.desc = desc
        self.terrain = terrain

        self.map_sprite_nid = map_sprite_nid
        self.size: Tuple[int, int] = tuple(size)
        self.position = starting_position

        self.components = components or Data()
        for component_key, component_value in self.components.items():
            self.__dict__[component_key] = component_value
            # Assign parent to component
            component_value.building = self

        self.data = {}

    @property
    def occupied_positions(self) -> List[Pos]:
        """Every tile this building sits on. Empty when it is off the map."""
        if not self.position:
            return []
        return self.positions_at(self.position)

    def positions_at(self, position: Pos) -> List[Pos]:
        """The footprint this building would occupy if anchored at `position`.

        The anchor is the top left tile; the footprint extends right and down.
        """
        width, height = self.size
        return [(position[0] + dx, position[1] + dy)
                for dx in range(width) for dy in range(height)]

    @property
    def tags(self) -> set:
        """Arbitrary tags attached via the BuildingTag component (mirrors ItemObject.tags)."""
        all_tags = set()
        tag_comp = self.components.get('building_tags')
        if tag_comp:
            all_tags |= set(tag_comp.value)
        return all_tags

    @classmethod
    def from_prefab(cls, prefab, component_data=None):
        # Components NEED to be copies! Since they store individualized information
        components = Data()
        component_data = component_data or []

        if component_data:
            for component_nid, component_value in component_data:
                new_component = BCA.restore_component((component_nid, component_value))
                components.append(new_component, overwrite=True)

        else:
            for component in prefab.components:
                new_component = BCA.restore_component((component.nid, component.value))
                components.append(new_component, overwrite=True)

        return cls(prefab.nid, prefab.name, prefab.desc, prefab.terrain,
                   prefab.map_sprite_nid, prefab.starting_position, components,
                   prefab.size)

    # If the attribute is not found
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            return super().__getattr__(attr)
        return None

    def __str__(self):
        return "Building: %s %s" % (self.nid, self.uid)

    def __repr__(self):
        return "Building: %s %s" % (self.nid, self.uid)

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other: BuildingObject) -> bool:
        return isinstance(other, BuildingObject) and self.uid == other.uid

    def save(self):
        serial_dict = {}
        serial_dict['uid'] = self.uid
        serial_dict['nid'] = self.nid
        serial_dict['owner_nid'] = self.owner_nid
        serial_dict['position'] = self.position
        serial_dict['data'] = self.data
        components = [(component.nid, component.value) for component in self.components]
        serial_dict['components'] = components
        return serial_dict

    @classmethod
    def restore(cls, dat):
        prefab = DB.buildings.get(dat['nid'])
        if prefab:
            components = dat.get('components', [])
            self = cls.from_prefab(prefab, components)
        else:
            desc = 'This is a placeholder for %s generated when the database cannot locate a building' % dat['nid']
            self = cls(dat['nid'], 'Placeholder', desc, None, None)
        self.uid = dat['uid']
        self.owner_nid = dat['owner_nid']
        position = dat.get('position', self.position)
        # JSON has no tuples, so a saved position comes back as a list
        self.position = tuple(position) if position else position
        self.data = dat['data']
        return self
