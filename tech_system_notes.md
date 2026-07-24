# Renown / Tech ("Unlock") System — Design Spec

4X-genre progression layer. Player earns **renown** (clear dungeons, conquer cities, find
relics, defeat heroes, achievements) and spends it to unlock **techs** — flavored as generic
"unlocks", not techs. Techs "infect" many systems, must be designer-configurable, and cheap
at runtime.

Design borrows the **decomposition** of Civ6's Modifier system (Effect × Collection ×
Arguments × Requirement × Attachment, plus a once/continuous flag) — but expresses it as
plain prefab data over LT's *existing* component machinery. **No 4th codegen system.**

---

## 1. Core model

A **Tech** owns no logic. It is a bag of references (`effects`) plus unlock gating
(`renown_cost`, `requires`, `conditions`). Two effect kinds cover the whole list:

- **`TechFlag`** — a named key/value the engine reads at a **single call site** (`has_tech` /
  `get_tech_value` / `get_tech_set`). O(1), no per-unit skill, no combat fan-out. **Default
  choice.** (Civ6 "continuous" modifier, but cheap because it's a lookup, not a re-evaluated
  condition.)
- **`GrantSkill`** — materialize an existing skill onto a **collection** of units at unlock
  (and onto future/qualifying units). Pays once at a cold state-change; zero per-hook cost
  after. Use **only** when the effect must ride per-unit through combat/skill machinery.
  (Civ6 "RunOnce/Permanent" modifier.)

> **Rule of thumb (perf-driven):** default to `TechFlag` (single-site read). Escalate to
> `GrantSkill` only when the effect genuinely needs to be a live skill on the unit. Never
> use condition-gated global skills — that's the expensive path.

### Collection (Civ6's best axis — "who it hits")
Only meaningful for `GrantSkill`. Small enum scoped to 4X needs:

| Collection | Subjects |
|---|---|
| `TEAM_UNITS` | every unit on the tech's team |
| `TEAM_CITIES` | every city the team owns |
| `UNITS_WITH_TAG` (arg: tag) | team units whose class carries `tag` |
| `SELF_TEAM` | the team object itself (team-level skill/stat) |

### Arguments + combine (Civ6 ModifierArguments)
`TechFlag` carries `value` + a **combine policy** for when multiple unlocked techs write the
same key:

| combine | use |
|---|---|
| `sum` | additive stacks — exp +10%×3, pop-cap +5×3 |
| `max` | tiered replace — weapon tier 1→2→3 |
| `set` | accumulate a set — draftable classes, buildable buildings |
| `or` | boolean any — a plain on/off flag |

---

## 2. Data model (design-time, `DB.techs`)

New catalog `app/data/database/techs.py`, registered on `DB`, versioned into serialization.

```python
# app/data/database/techs.py
from dataclasses import dataclass, field
from typing import List, Any
from app.utilities.typing import NID

class Collection(enum.Enum):
    TEAM_UNITS      = 'team_units'
    TEAM_CITIES     = 'team_cities'
    UNITS_WITH_TAG  = 'units_with_tag'
    SELF_TEAM       = 'self_team'

class Combine(enum.Enum):
    SUM = 'sum'; MAX = 'max'; SET = 'set'; OR = 'or'

@dataclass
class TechFlag:
    kind: str = 'flag'
    key: NID = ''                       # engine reads this key at its call site
    value: Any = True
    combine: Combine = Combine.OR

@dataclass
class GrantSkill:
    kind: str = 'grant_skill'
    skill_nid: NID = ''                 # an existing DB.skills prefab (the verb + args)
    collection: Collection = Collection.TEAM_UNITS
    collection_arg: str = ''            # e.g. tag name for UNITS_WITH_TAG

TechEffect = Union[TechFlag, GrantSkill]   # tagged by .kind on (de)serialize

@dataclass
class TechPrefab(Prefab):
    nid: NID
    name: str = ''
    desc: str = ''
    icon_nid: NID = None
    renown_cost: int = 0
    requires: List[NID] = field(default_factory=list)   # prerequisite tech nids (ALL)
    conditions: List[str] = field(default_factory=list) # optional extra eval predicates (ALL)
    effects: List[TechEffect] = field(default_factory=list)

class TechCatalog(CategorizedCatalog[TechPrefab]):
    datatype = TechPrefab
```

`requires` = prerequisite tech nids (the only requirement kind the source table actually uses).
`conditions` = escape hatch for exotic unlock gates (`"game.get_num_cleared_dungeons(team) >= 3"`).
Both ALL-tested (Civ6 `TEST_ALL`); add a `requirement_mode` later if ANY is ever needed.

---

## 3. Runtime state (per-team)

Renown and unlocked techs live on **`TeamObject`** — each team has its own tree.
`TeamObject.research: List[str]` **already exists** on this branch (reuse as unlocked-tech
nids). Add `renown`.

```python
# app/engine/objects/team.py  (additions)
self.renown: int = renown                 # + in save()/restore()
self.research: List[str] = research or []  # already present — unlocked tech nids
self._tech_flag_cache = None               # NOT serialized; rebuilt on change
```

### Helpers (`app/engine/tech_funcs.py` — new, interpreted, no codegen)
```python
def has_tech(team, tech_nid) -> bool
def get_tech_value(team, key, default=0)   # scan team.research → flags[key], apply combine
def get_tech_set(team, key) -> set         # combine=set keys
def can_unlock(team, tech_nid) -> bool     # not owned; all requires owned; conditions pass; renown >= cost
def _rebuild_flag_cache(team)              # precompute {key: combined_value} once per change
```
`get_tech_value` reads a per-team precomputed dict (`_tech_flag_cache`), rebuilt only when the
unlocked set changes (on `UnlockTech` do/reverse). So T1 reads are a dict lookup, not a scan.

### `game` accessors (`game_state.py`)
`game.has_tech(team, nid)`, `game.get_tech_value(team, key)`, `game.get_tech_set(team, key)`,
`game.get_renown(team)`.

---

## 4. Actions (turnwheel-safe, `action.py`)

- **`ChangeRenown(team, amount)`** — team.renown += amount; reverse subtracts. `save_obj`
  already resolves `('team', nid)`.
- **`UnlockTech(team, tech_nid)`**
  - **do:** assert `can_unlock`; `ChangeRenown(team, -cost)`; append nid to `team.research`;
    invalidate flag cache; for each `GrantSkill` effect, `AddSkill` on every unit currently in
    its collection (sub-actions, so reversal is automatic).
  - **reverse:** remove nid; refund; `RemoveSkill`; invalidate cache.

`GrantSkill` for **future** units: extend the unit-add skill path (sibling of
`unit_funcs.get_global_skills`) with `get_tech_skills(unit)` — scans `unit.team`'s unlocked
techs for `GrantSkill` effects whose collection matches this unit, returns skills to add. No
per-unit tracking; re-derived on add, exactly like global skills.

---

## 5. Engine integration points (T1 flag reads — one line each)

Each is a single `if game.has_tech(...)` / `get_tech_value(...)` at the natural fork:

| Tech key | Site |
|---|---|
| `weapon_tier` | item usability / draft-equip (grant iron/steel/mithril access) |
| `city_pop_cap_bonus` | `city_funcs` population cap |
| `exp_mult_bonus` | exp calc |
| `upkeep_bonus_<tag>` | `city_funcs.run_city_upkeep` |
| `dungeon_sight_bonus` / `overworld_sight_bonus` | fow / sight range |
| `road_move_bonus` | terrain movement cost |
| `draft_unlock` (set) | `city_funcs` draftable-classes query |
| `build_unlock` (set) | `city_funcs` buildable query |
| `farm_/mine_/artisan_resource_bonus` | `ResourcePerTurn` / building resource |
| `hero_pool_tier` | tavern hero generation |
| `recruit_chance` | overworld neutral-enemy resolution |
| `elite_promote_<tag>` | promotion: grant klass skill |

`GrantSkill` sites: unlock action + `get_tech_skills(unit)` on unit-add. That's all.

---

## 6. Renown accrual (designer-wired, via events)

No engine "achievement system." Existing event triggers already cover the sources
(unit death → conquered/hero, region cleared → dungeon/relic, promotion, level-clear).
Designer awards renown in event scripts:

- New event command **`add_renown;<team>;<amount>`** → `ChangeRenown` action.
- Optional **`unlock_tech;<team>;<tech>`** for scripted/story unlocks and testing.

---

## 7. UI

`TechTreeState` — full-screen `State` modeled on `CityMenuState`/`InfoMenuState` (this
branch's established pattern: `in_level = show_map = False`, `PanoramaBackground`,
`transition_in`, own `FluidScroll`). Renders the prereq DAG, renown balance, per-tech cost /
locked / unlocked / **why-locked** (composable `requires`+`conditions` make the reason
renderable — a Civ6 win over an opaque eval string). Entry: an AUX/menu hook, same pattern as
the city menu.

## 8. Editor

`tech_editor/` tab (catalog tab + model + properties), mirroring existing editors. The
`effects` list needs a **bespoke multi-field table widget** (per the CLAUDE.md note: stock
component types can't express a list-of-rows) — follow the `UnitDraftList` / `ProducesUnits`
template: enum + delegate + list model + `get_display_widget` branch. `requires` = a
multi-select of other tech nids; `conditions` = string list.

---

## 9. Worked examples

Show a spread across both effect kinds, all combine policies, multi-effect techs, and prereq
chains. (Costs illustrative.)

### Iron / Steel / Mithril — tiered flag, `combine=max`, prereq chain
```yaml
Iron Weapons:      { cost: 100, effects: [ {flag, key: weapon_tier, value: 1, combine: max} ] }
Steel Weapons:     { cost: 250, requires: [Iron Weapons],
                     effects: [ {flag, key: weapon_tier, value: 2, combine: max} ] }
Mithril Weapons:   { cost: 500, requires: [Steel Weapons],
                     effects: [ {flag, key: weapon_tier, value: 3, combine: max} ] }
```
Engine (item usability / equip): `tier = game.get_tech_value(unit.team, 'weapon_tier'); grant
iron if tier>=1, steel if >=2, mithril if >=3`. `max` means only the highest unlocked tier
matters — no double-counting.

### Increase City Cap 1/2/3 — additive flag, `combine=sum`
```yaml
Increase City Cap 1: { cost: 150, effects: [ {flag, key: city_pop_cap_bonus, value: 5, combine: sum} ] }
Increase City Cap 2: { cost: 300, requires: [Increase City Cap 1],
                       effects: [ {flag, key: city_pop_cap_bonus, value: 5, combine: sum} ] }
Increase City Cap 3: { cost: 450, requires: [Increase City Cap 2],
                       effects: [ {flag, key: city_pop_cap_bonus, value: 5, combine: sum} ] }
```
Engine (`city_funcs`): `cap = 5 + game.get_tech_value(city.team, 'city_pop_cap_bonus')` →
5 / 10 / 15 / 20 as the chain unlocks.

### Increase Experience Gain 1/2/3 — additive multiplier
```yaml
Increase Experience Gain 1: { cost: 120, effects: [ {flag, key: exp_mult_bonus, value: 0.10, combine: sum} ] }
# 2 requires 1, 3 requires 2, each +0.10
```
Engine (exp calc): `exp *= 1 + game.get_tech_value(team, 'exp_mult_bonus')`.

### Mercenary Contracts / Horsemanship / Mounted Archers — draft unlocks, `combine=set`
```yaml
Mercenary Contracts: { cost: 100, effects: [ {flag, key: draft_unlock, value: Mercenary, combine: set} ] }
Horsemanship:        { cost: 100, effects: [ {flag, key: draft_unlock, value: Cavalier,  combine: set} ] }
Mounted Archers:     { cost: 200, effects: [ {flag, key: draft_unlock, value: Nomad,     combine: set} ] }
```
Engine (`city_funcs` draftable query): `class draftable if base_draftable or class_nid in
game.get_tech_set(team, 'draft_unlock')`.

### Mage Training 1 — MULTI-effect tech (Civ6 modularity: one tech, several modifiers)
```yaml
Mage Training 1:
  cost: 200
  effects:
    - {flag, key: draft_unlock, value: Mage,    combine: set}   # can draft Mages
    - {flag, key: build_unlock, value: Library, combine: set}   # can build Library
```
### Cleric Training — same shape
```yaml
Cleric Training:
  cost: 200
  effects:
    - {flag, key: draft_unlock, value: Cleric, combine: set}
    - {flag, key: build_unlock, value: Church, combine: set}
```

### Farm / Mine / Artisan Improvement — resource bonus flags
```yaml
Farm Improvement:    { cost: 150, effects: [ {flag, key: farm_resource_bonus,    value: 1, combine: sum} ] }
Mine Improvement:    { cost: 150, effects: [ {flag, key: mine_resource_bonus,    value: 1, combine: sum} ] }
Artisan Improvement: { cost: 150, effects: [ {flag, key: artisan_resource_bonus, value: 1, combine: sum} ] }
```
Engine (`ResourcePerTurn` on the relevant building): add
`game.get_tech_value(city.team, 'farm_resource_bonus')` to farm output.

### Better Torches / Better Scouting — sight bonuses
```yaml
Better Torches:  { cost: 100, effects: [ {flag, key: dungeon_sight_bonus,   value: 2, combine: max} ] }
Better Scouting: { cost: 100, effects: [ {flag, key: overworld_sight_bonus, value: 2, combine: max} ] }
```

### Faster Roads — movement flag
```yaml
Faster Roads: { cost: 120, effects: [ {flag, key: road_move_bonus, value: 1, combine: max} ] }
```

### Recruitment — % chance flag
```yaml
Recruitment: { cost: 200, effects: [ {flag, key: recruit_chance, value: 0.25, combine: max} ] }
```
Engine (overworld neutral resolution): `if random < game.get_tech_value(team,'recruit_chance'): recruit`.

### More Hero Options 1/2 → Legendary Heroes — tiered pool, prereq chain
```yaml
More Hero Options 1: { cost: 150, effects: [ {flag, key: hero_pool_tier, value: 1, combine: max} ] }
More Hero Options 2: { cost: 300, requires: [More Hero Options 1],
                       effects: [ {flag, key: hero_pool_tier, value: 2, combine: max} ] }
Legendary Heroes:    { cost: 600, requires: [More Hero Options 2],
                       effects: [ {flag, key: hero_pool_tier, value: 3, combine: max} ] }
```

### Elite Infantry/Cavalry/Air/Mage — flag read at promotion
```yaml
Elite Infantry: { cost: 200, effects: [ {flag, key: elite_promote_infantry, value: true, combine: or} ] }
Elite Cavalry:  { cost: 200, effects: [ {flag, key: elite_promote_cavalry,  value: true, combine: or} ] }
```
Engine (promotion): `if game.has_tech-style get_tech_value(team, f'elite_promote_{tag}'):
add the class's elite skill`. (Flag, not a live global skill — avoids per-hook condition cost.)

### Iron Weapons done as `GrantSkill` instead — the OTHER path (for contrast)
```yaml
# Alternative authoring if you'd rather it be a real skill than an item-usability flag:
Iron Weapons (skill variant):
  cost: 100
  effects:
    - {grant_skill, skill_nid: IronWeaponAccess, collection: TEAM_UNITS}
```
`UnlockTech` AddSkills `IronWeaponAccess` to every current team unit; `get_tech_skills` adds it
to future team units on add. Costs a real skill slot per unit but composes with the skill
system. **Prefer the flag version** unless you need the skill behavior.

### Composable unlock condition — the `conditions` escape hatch
```yaml
Legendary Dungeon Reward:
  cost: 800
  requires: [Legendary Heroes]
  conditions: ["game.get_num_cleared_dungeons(team) >= 5"]   # ALL of requires + conditions
  effects: [ ... ]
```

---

## 10. Phasing

0. **Data model** — `TechPrefab`/`TechEffect`/`TechCatalog`, `DB.techs`, serialization version
   bump + migrator. `TeamObject.renown` (+ save/restore; `research` already there).
1. **Runtime helpers** — `tech_funcs.py` (`has_tech`/`get_tech_value`/`get_tech_set`/
   `can_unlock`/flag cache) + `game` accessors.
2. **Actions** — `ChangeRenown`, `UnlockTech` (materialize `GrantSkill`), turnwheel.
3. **GrantSkill plumbing** — `get_tech_skills(unit)` on unit-add.
4. **T1 flag reads** — wire each engine site in §5 (one line each).
5. **Events** — `add_renown`, `unlock_tech` commands.
6. **UI** — `TechTreeState` + entry point.
7. **Editor** — `tech_editor/` tab + bespoke effects-list widget.

Phases 0–4 make techs fully functional (scriptable via events); 5–7 are authoring/UX.

## 11. Explicit non-goals
- **No 4th codegen/component-hook system.** `TechEffect` is plain data interpreted by
  `tech_funcs`; the *effects* reuse existing skill/building components.
- **No condition-gated global skills** (the per-hook cost you flagged).
- **No relational modifier DB** (Civ6's storage) — take the decomposition, not the tables.
- **No engine achievement system** — renown is awarded by designer events.
