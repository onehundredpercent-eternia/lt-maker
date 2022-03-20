from typing import Tuple, Dict

from app.utilities.data import Prefab
from app.utilities import hex_math

class HexPrefab(Prefab):
    def __init__(self, pos: hex_math.Hex, name: str = '', hex_type: str = None):
        self.pos: hex_math.Hex = pos
        self.name: str = name
        self.hex_type: str = hex_type

    def get_position_label(self) -> str:
        return "(q: %s, r: %s, s: %s)" % (self.pos.q, self.pos.r, self.pos.s)

    def save_attr(self, name, value):
        if name == 'pos':
            value = (value.q, value.r, value.s)
        else:
            value = super().save_attr(name, value)
        return value

    def restore_attr(self, name, value):
        value = super().restore_attr(name, value)
        if name == 'pos':
            value = hex_math.Hex(*value)
        return value

    @classmethod
    def default(cls):
        return cls(hex_math.Hex(0, 0, 0), '', None)

class OverworldHexCatalog(Dict[Tuple, HexPrefab]):
    def get_by_name(self, name):
        for hex_prefab in self.values():
            if hex_prefab.name == name:
                return hex_prefab
        return None
        
    def save(self):
        return [elem.save() for elem in self.values()]

    def restore(self, vals):
        self.clear()
        for s_dict in vals:
            new_hex = HexPrefab.restore(s_dict)
            self[new_hex.pos] = new_hex
