from dataclasses import dataclass

from app.utilities.data import Data, Prefab

@dataclass
class HexType(Prefab):
    nid: str = None
    name: str = None

    color: tuple = (0, 0, 0)

    movement_cost: str = None

    def restore_attr(self, name, value):
        if name == 'color':
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

class HexTypeCatalog(Data[HexType]):
    datatype = HexType
