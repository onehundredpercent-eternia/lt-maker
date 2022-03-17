from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class HexEvent(Prefab):
    event_nid: str = None
    event_chance: float = 1.

@dataclass
class HexType(Prefab):
    nid: str = None
    name: str = None

    color: tuple = (0, 0, 0)

    movement_cost: str = None

    events: list = None  # Events and their chance to occur in this Hex Type

    def save_attr(self, name, value):
        if name == 'events':
            return [(event.event_nid, event.event_chance) for event in self.events]
        else:
            return super().save_attr(name, value)

    def restore_attr(self, name, value):
        if name == 'color':
            value = tuple(value)
        elif name == 'events':
            value = [HexEvent(*dat) for dat in value]
        else:
            value = super().restore_attr(name, value)
        return value

class HexTypeCatalog(Data[HexType]):
    datatype = HexType
