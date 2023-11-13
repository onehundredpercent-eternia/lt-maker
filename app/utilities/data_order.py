import json
from pathlib import Path
from typing import List

def parse_order_keys_file(fname: Path) -> List[str]:
    with open(fname) as load_file:
        okeys = json.load(load_file)
    # TODO(mag): this is migration code; remove it on 1/1/2024
    if isinstance(okeys, dict):
        ordering = okeys.keys()
        ordering = sorted(ordering, key=lambda k: okeys.get(k, 99999))
        return ordering
    # correct code
    elif isinstance(okeys, list):
        return okeys