from app.utilities.data import Data
from app.utilities.typing import NID


def is_nid_in_db_func(catalog: Data):
    def f(nid: NID, _):
        return nid in catalog.keys()
    return f

def name_and_nid_list_from_db(catalog: Data):
    return [(getattr(obj, 'name', None), getattr(obj, 'nid')) for obj in catalog]

