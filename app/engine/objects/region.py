from typing import List, Tuple
from app.utilities.typing import NID

from app.events.regions import RegionType, Region

import logging

class RegionObject(Region):
    """
    Inherits from Region in order to access Region's helper funcs,
    like area and center
    """

    def __init__(self, nid: NID, region_type: RegionType, 
                 position: Tuple[int, int] = None, size: Tuple[int, int] = [1, 1], 
                 sub_nid: str = None, condition: str = 'True', 
                 only_once: bool = False, interrupt_move: bool = False):
        self.nid = nid
        self.region_type = region_type
        self.position = position
        self.size = size

        self.sub_nid = sub_nid
        self.condition = condition
        self.only_once = only_once
        self.interrupt_move = interrupt_move

        self.data = {}

    @classmethod
    def from_prefab(cls, prefab):
        return cls(prefab.nid, prefab.region_type, prefab.position, prefab.size,
                   prefab.sub_nid, prefab.condition, prefab.only_once, prefab.interrupt_move)

    def save(self) -> dict:
        serial_dict = {}
        serial_dict['nid'] = self.nid
        serial_dict['data'] = self.data
        return serial_dict

    @classmethod
    def restore(cls, level_prefab, dat: dict):
        prefab = level_prefab.regions.get(dat['nid'])
        if prefab:
            self = cls.from_prefab(prefab)
        else:
            logging.error("Could not locate region with nid %s in level %s" % (dat['nid'], level.nid))
            self = cls(dat['nid'], RegionType.NORMAL)
        self.data = dat['data']
        return self
