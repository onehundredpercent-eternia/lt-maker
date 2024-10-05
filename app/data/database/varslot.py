from app.utilities.data import Data
from app.utilities import prefab, str_utils

class VarSlot(prefab.Prefab):
    nid: str = None
    desc: str = None

class VarSlotCatalog(Data[VarSlot]):
    datatype = VarSlot

    def add_new_default(self, db):
        nid = str_utils.get_next_name("New Slot", self.keys())
        new_tag = VarSlot(nid)
        self.append(new_tag)
        return new_tag