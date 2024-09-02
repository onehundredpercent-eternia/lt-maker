

from app.utilities.typing import NestedPrimitiveDict, NestedPrimitiveList

def recursive_list_comparison(list_a: NestedPrimitiveList, list_b: NestedPrimitiveList) -> bool:
    """
    Recursively compares two lists
    """
    if len(list_a) != len(list_b):
        return False

    for val_a, val_b in zip(list_a, list_b):
        if isinstance(val_a, list):
            if not recursive_list_comparison(val_a, val_b):
                return False
        elif isinstance(val_a, dict):
            if not recursive_comparison(val_a, val_b):
                return False
        elif val_a != val_b:
            return False
    return True

def recursive_comparison(dict_a: NestedPrimitiveDict, dict_b: NestedPrimitiveDict) -> bool:
    """
    Recursively compares two dictionaries
    """
    if len(dict_a) != len(dict_b):
        return False

    for key, val_a in dict_a.items():
        if key not in dict_b:
            return False
        val_b = dict_b[key]

        if isinstance(val_a, list):
            if not recursive_list_comparison(val_a, val_b):
                return False
        elif isinstance(val_a, dict):
            if not recursive_comparison(val_a, val_b):
                return False
        elif val_a != val_b:
            return False
    return True