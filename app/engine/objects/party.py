from app.utilities.data import Prefab

from app.engine.game_state import game

class PartyObject(Prefab):
    def __init__(self, nid, name, leader_nid, units=None, money=0, convoy=None, bexp=0, rations=0, special=0, crystals=0):
        self.nid = nid
        self.name = name
        self.leader_nid = leader_nid
        self.units = units or []  # Unit nids (Pretty sure this list is never USED)
        # Rather the units themselves know which party they belong to
        # And we just iterate over all units when we need to check
        self.money = money
        if convoy:
            # Actually the item, not just a uid reference
            self.convoy = [game.get_item(item_uid) for item_uid in convoy]
            self.convoy = [i for i in self.convoy if i]
        else:
            self.convoy = []
        self.bexp: int = bexp
        self.rations: int = rations
        self.special: int = special
        self.crystals: int = crystals

    @property
    def items(self):
        return self.convoy

    def save(self):
        return {'nid': self.nid,
                'name': self.name,
                'leader_nid': self.leader_nid,
                'units': self.units,
                'money': self.money,
                'convoy': [item.uid for item in self.convoy],
                'bexp': self.bexp,
                'rations': self.rations,
                'special': self.special,
                'crystals': self.crystals}

    @classmethod
    def restore(cls, s_dict):
        party = cls(s_dict['nid'], s_dict['name'], s_dict['leader_nid'],
                    s_dict['units'], s_dict['money'], s_dict['convoy'],
                    s_dict['bexp'], s_dict.get('rations', 0),
                    s_dict.get('special', 0), s_dict.get('crystals', 0))
        return party
