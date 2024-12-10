from typing import List

import os
import csv, json
from dataclasses import dataclass

# Make sure file is saved with all items in the same json

fn = "items.csv"
proj = "west_march.ltproj"

with open(fn, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')

@dataclass
class Item:
    nid: str
    row: int
    col: int
    tier: str
    weapon_type: str
    mt: int
    hit: int
    crit: int
    weight: int
    uses: int
    value: int
    desc: str

items: List[Item] = []
for row in reader[1:]:
    if len(row) == 0:
        continue  # Skip empty lines
    nid = row[0]
    row = row[1]
    col = row[2]
    tier = row[3]
    weapon_type = row[4]
    mt = int(row[5])
    hit = int(row[6])
    crit = int(row[7])
    weight = int(row[8])
    uses = int(row[9])
    value = int(row[10])
    desc = row[12]
    item = Item(nid, row, col, tier, weapon_type, mt, hit, crit, weight, uses, value, desc)
    items.append(item)

item_json_loc = os.path.join(proj, "game_data", "items.json")
with open(item_json_loc) as fp:
    json_data = json.load(fp)

for item in items:
    # Remove any item from data with the same nid
    if item.nid in [d["nid"] for d in json_data]:
        idx = [d["nid"] for d in json_data].index(item.nid)
        json_data.pop(idx)
    is_basic = any(k in item.nid for k in ["Bronze_", "Iron_", "Steel_", "Silver_", "Adamant_", "Mithril_"])
    tags = [f"{item.weapon_type}", f"{item.tier}"]
    if is_basic:
        tags.append("Basic")

    s_dict = {
        "nid": item.nid,
        "name": item.nid.replace('_', ' '),
        "desc": item.desc,
        "icon_nid": item.weapon_type + "Icons",
        "icon_index": [item.col, item.row],
        "components": [
            ["item_prefab", f"{item.weapon_type}_Prefab"],
            ["damage", item.mt],
            ["hit", item.hit],
            ["crit", item.crit],
            ["weight", item.weight],
            ["value", item.value],
            ["uses", item.uses],
            ["uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}],
            ["item_tags", tags]
        ]
    }
    # Add basic tag
    json_data.append(s_dict)

with open(item_json_loc, 'w') as fp:
    json.dump(json_data, fp, indent=4)
