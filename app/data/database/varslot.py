from dataclasses import asdict, dataclass

from app.data.serialization.dataclass_serialization import dataclass_from_dict
from app.utilities.data import Data, Prefab
from app.utilities import str_utils
from app.utilities.typing import NestedPrimitiveDict


@dataclass
class VarSlot(Prefab):
    nid: str = None
    desc: str = None

    def save(self) -> NestedPrimitiveDict:
        return asdict(self)

    @classmethod
    def restore(cls, s_tuple: NestedPrimitiveDict):
        return dataclass_from_dict(cls, s_tuple)

class VarSlotCatalog(Data[VarSlot]):
    datatype = VarSlot

    def add_new_default(self, db):
        nid = str_utils.get_next_name("New Slot", self.keys())
        new_tag = VarSlot(nid)
        self.append(new_tag)
        return new_tag