from typing import List

import os
import csv, json
from dataclasses import dataclass

# Make sure file is saved with all items in the same json

csv_fn = os.path.abspath("spells.csv")
proj = "../../../../west_march/west_march.ltproj"

@dataclass
class Item:
    nid: str
    row: int
    col: int
    tier: str
    rng: str
    weapon_type: str
    mt: int
    hit: int
    uses: int
    value: int
    desc: str

items: List[Item] = []
with open(csv_fn, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
        print(row)
        if len(row) == 0:
            continue  # Skip empty lines
        nid = row[0]
        ro = int(row[1])
        col = int(row[2])
        weapon_type = row[3]
        tier = row[4]
        rng = str(row[5])
        mt = int(row[6]) if row[6] != '--' else None
        hit = int(row[7]) if row[7] != '--' else None
        uses = int(row[8])
        value = int(row[9])
        desc = row[10]
        item = Item(nid, ro, col, tier, rng, weapon_type, mt, hit, uses, value, desc)
        items.append(item)

item_json_loc = os.path.abspath(os.path.join(proj, "game_data", "items.json"))
new_item_json_loc = os.path.abspath(os.path.join(proj, "game_data", "items.json"))
with open(item_json_loc) as fp:
    json_data = json.load(fp)

for item in items:
    # Remove any item from data with the same nid
    if item.nid in [d["nid"] for d in json_data]:
        idx = [d["nid"] for d in json_data].index(item.nid)
        json_data.pop(idx)
    tags = [f"{item.weapon_type}", f"{item.tier}", "Spell"]

    s_dict = {
        "nid": item.nid,
        "name": item.nid.replace('_', ' '),
        "desc": item.desc,
        "icon_nid": item.weapon_type + "Icons",
        "icon_index": [item.col, item.row],
        "components": [
            ["item_prefab", f"{item.weapon_type}_Spell_Prefab"],
            ["value", item.value],
            ["uses", item.uses],
            ["uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}],
            ["item_tags", tags]
        ]
    }
    if item.hit is not None:
        s_dict["components"].append(["hit", item.hit])
    if item.mt is not None:
        s_dict["components"].append(["damage", item.mt])
    if item.rng == "Long":
        s_dict["components"].append(["min_range", 1])
        s_dict["components"].append(["max_equation_range", "SPELL_RANGE"])
    elif item.rng == "0":
        s_dict["components"].append(["min_range", 0])
        s_dict["components"].append(["max_range", 0])
    else:
        minim, maxim = [int(_) for _ in item.rng.split('-')]
        s_dict["components"].append(["min_range", minim])
        s_dict["components"].append(["max_range", maxim])

    # Add basic tag
    json_data.append(s_dict)

with open(new_item_json_loc, 'w') as fp:
    json.dump(json_data, fp, indent=4)
