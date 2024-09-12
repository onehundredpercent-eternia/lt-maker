from app.utilities.typing import NestedPrimitiveDict

def migrate(data: NestedPrimitiveDict) -> NestedPrimitiveDict:
    # migrated wexp gain to be a dataclass dict
    for unit in data.get("units", []):
        new_wexp_gain = {}
        for wexp_gain_nid, wexp_gain_tuple in unit.get('wexp_gain', {}).items():
            new_wexp_gain[wexp_gain_nid] = {
                'usable': bool(wexp_gain_tuple[0]),
                'wexp_gain': wexp_gain_tuple[1],
                'cap': wexp_gain_tuple[2]
            }
        unit['wexp_gain'] = new_wexp_gain
    for klass in data.get('classes', []):
        new_wexp_gain = {}
        for wexp_gain_nid, wexp_gain_tuple in klass.get('wexp_gain', {}).items():
            new_wexp_gain[wexp_gain_nid] = {
                'usable': bool(wexp_gain_tuple[0]),
                'wexp_gain': wexp_gain_tuple[1],
                'cap': wexp_gain_tuple[2]
            }
        klass['wexp_gain'] = new_wexp_gain
    return data