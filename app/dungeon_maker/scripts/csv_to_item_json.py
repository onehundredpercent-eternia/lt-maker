from typing import List

import csv, json

# Make sure file is saved with all items in the same json

fn = "items.csv"
proj = "west_march.ltproj"

with open(fn, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')

@dataclass
class Item:
    nid: str
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
for row in reader[1:]
    if len(row) == 0:
        continue  # Skip empty lines
    nid = row[0]
    tier = row[1]
    weapon_type = row[2]
    mt = int(row[3])
    hit = int(row[4])
    crit = int(row[5])
    weight = int(row[6])
    uses = int(row[7])
    value = int(row[8])
    desc = row[10]
    item = Item(nid, tier, weapon_type, mt, hit, crit, weight, uses, value, desc)
    items.append(item)

item_json_loc = os.path.join(proj, "game_data", "items.json")
with open(item_json_loc) as fp:
    item_data = json.load(fp)

for item in items:
    # Remove any item from data with the same nid
    if item.nid in [d["nid"] for d in data]:
        idx = [d["nid"] for d in data].index(item.nid)
        data.pop(idx)

    s_dict = {
        "nid": item.nid,
        "name": item.nid.replace('_', ' '),
        "desc": item.desc,
        "icon_nid": "Sword",
        "icon_index": [0, 0],
        "components": [
            ["item_prefab", f"{item.weapon_type}_Prefab"],
            ["damage", item.mt],
            ["hit", item.hit],
            ["crit", item.crit],
            ["weight", item.weight],
            ["value", item.value],
            ["uses", item.uses],
            ["uses_options", {"lose_uses_on_miss": False, "one_loss_per_combat": False}],
            ["item_tags", [f"{item.weapon_type}", f"{item.tier}"]]
        ]
    }
    data.append(s_dict)

with open(manifest, 'w') as fp:
    json.dump(data, fp, indent=4)
