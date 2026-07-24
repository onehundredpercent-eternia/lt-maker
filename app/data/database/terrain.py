from dataclasses import dataclass

from app.utilities.data import Data, Prefab
from app.utilities import str_utils

@dataclass
class Terrain(Prefab):
    nid: str = None
    name: str = None

    color: tuple = (0, 0, 0)
    minimap: str = None
    platform: str = None
    background: str = None

    mtype: str = None
    opaque: bool = False

    status: str = None

    food: int = 0
    production: int = 0
    gold: int = 0

    # Adjacency yield: resources granted to each orthogonally-adjacent tile
    # (e.g. a river giving neighbors +1 gold). Applied in city_funcs.get_tile_yield.
    adjacent_food: int = 0
    adjacent_production: int = 0
    adjacent_gold: int = 0

    def restore_attr(self, name, value):
        if name == 'color':
            value = tuple(value)
        else:
            value = super().restore_attr(name, value)
        return value

class TerrainCatalog(Data[Terrain]):
    datatype = Terrain

    def create_new(self, db):
        from app.data.resources.resources import RESOURCES
        nids = [d.nid for d in self]
        nid = name = str_utils.get_next_name("New Terrain", nids)
        terrain_mcost = db.mcost.terrain_types[0]
        platform = RESOURCES.get_platform_types()[0][0]
        new_terrain = Terrain(nid, name, (0, 0, 0), 'Grass', platform, mtype=terrain_mcost)
        self.append(new_terrain)
        return new_terrain
