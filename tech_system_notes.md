# Renown / Tech ("Unlock") System — Design Spec

> **Status (Phases 0–5 and 7 implemented; 6 remains).** Sections below are the original spec; places where the
> implementation intentionally diverges are marked **`[DEVIATION]`**. Every deviation is an
> improvement kept on purpose — the spec text is left in place so the reasoning is still
> readable. See §12 for the consolidated list.

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

**`[DEVIATION — supersedes most of §1/§2]` Effects are `TechComponent`s, not dataclasses.**
Phase 7 (the editor) forced this: the spec's free-text `TechFlag.key` plus designer-chosen
`combine` is a fine *runtime* design and a bad *authoring* one — `weapon_teir` silently no-ops
forever, and `combine=sum` on `weapon_tier` is always a bug because the engine read site, not
the designer, dictates the policy. So `TechEffect` became one component class per effect
(`app/engine/tech_components/base_components.py`), with `flag_key` and `combine` as **class
attributes**. The tagged union, `restore_effect` and the `.kind` discriminator are gone;
`TechPrefab.components: Data[TechComponent]` replaces `effects`, and `TechPrefab.restore` maps
the legacy `effects` list forward on load. There is still **no codegen'd dispatch module** —
tech components are read declaratively, never hook-dispatched — so the §11 non-goal holds in
substance. The payoff: the editor tab reuses `NewComponentProperties` wholesale, and nid
renames inside effects are handled by the existing `swap_values` machinery. The rest of §1 and
§2 below describes the original dataclass shape; read it for the reasoning, not the API.

**`[DEVIATION]` A third effect kind shipped: `UpgradeItems`.** Same "materialize at unlock"
family as `GrantSkill`, but instead of adding a skill it physically swaps every item in the
target units' inventories up its `UpgradesTo` chain (Iron→Steel→Mithril) to whatever the
team's current `weapon_tier` allows. Kept separate from the `TechFlag('weapon_tier', …)` that
sets the tier, so a designer can raise the tier without a retroactive sweep, or re-sweep
without changing the tier. See §9's weapon-tier example and §12.

> **Rule of thumb (perf-driven):** default to `TechFlag` (single-site read). Escalate to
> `GrantSkill` only when the effect genuinely needs to be a live skill on the unit. Never
> use condition-gated global skills — that's the expensive path.

### Collection (Civ6's best axis — "who it hits")
Only meaningful for `GrantSkill`. Small enum scoped to 4X needs:

**`[DEVIATION]` Named `GrantTarget`, not `Collection`** (fields `grant_target` /
`grant_target_arg`). "Collection" reads as a container type in a Python codebase; `GrantTarget`
says what it actually is — who the grant materializes onto. Applies to `UpgradeItems` too.

| GrantTarget | Subjects |
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

New catalog `app/data/database/techs.py`, registered on `DB`.

**`[DEVIATION]` No serialization version bump / migrator.** `DB.techs` is registered as an
**`optional_data_type`** (alongside `credit` and `map_terrain_associations`): a project with no
`techs.json` loads an empty catalog and writes the file on next save. A migrator is the wrong
tool for a purely-additive catalog — there is nothing to migrate.

```python
# app/data/database/techs.py  (as implemented)
from dataclasses import dataclass, field
from typing import List, Any
from app.utilities.typing import NID

class GrantTarget(enum.Enum):       # [DEVIATION] was `Collection`
    TEAM_UNITS      = 'team_units'
    TEAM_CITIES     = 'team_cities'
    UNITS_WITH_TAG  = 'units_with_tag'
    SELF_TEAM       = 'self_team'

class Combine(enum.Enum):
    SUM = 'sum'; MAX = 'max'; SET = 'set'; OR = 'or'

@dataclass
class TechFlag:
    key: NID = ''                       # engine reads this key at its call site
    value: Any = True
    combine: Combine = Combine.OR
    kind: str = 'flag'                  # discriminator last so the real fields are positional

@dataclass
class GrantSkill:
    skill_nid: NID = ''                 # an existing DB.skills prefab (the verb + args)
    grant_target: GrantTarget = GrantTarget.TEAM_UNITS
    grant_target_arg: str = ''          # e.g. tag name for UNITS_WITH_TAG
    kind: str = 'grant_skill'

@dataclass                              # [DEVIATION] third effect kind, not in the original spec
class UpgradeItems:
    grant_target: GrantTarget = GrantTarget.TEAM_UNITS
    grant_target_arg: str = ''
    kind: str = 'upgrade_items'

TechEffect = Union[TechFlag, GrantSkill, UpgradeItems]   # tagged by .kind on (de)serialize
# each kind owns save()/restore(); module-level restore_effect(dat) dispatches on dat['kind']

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
**`[DEVIATION]` The module ships more than the five above** — `invalidate_flag_cache(team)` /
`_get_cache(team)` (the dirty-flag half of the cache), plus the grant-target helpers the
`GrantSkill` / `UpgradeItems` paths need: `unit_matches_grant_target`, `get_grant_target_units`,
`get_tech_skills(unit)` (§4's future-unit hook lives here, not in `unit_funcs`). `get_tech_set`
returns a **copy** so a caller can't mutate the cache.
`get_tech_value` reads a per-team precomputed dict (`_tech_flag_cache`), rebuilt only when the
unlocked set changes (on `UnlockTech` do/reverse). So T1 reads are a dict lookup, not a scan.

### `game` accessors (`game_state.py`)
`game.has_tech(team, nid)`, `game.get_tech_value(team, key)`, `game.get_tech_set(team, key)`,
`game.get_renown(team)`.

**`[DEVIATION]` All four take a team *nid or* a live `TeamObject`** (`game._resolve_team`), so
call sites can pass `unit.team` / `city.team` (both nids) without a lookup dance, and they
degrade to the default when the team doesn't exist. Each accessor **lazy-imports `tech_funcs`
inside the method** — a module-level import cycles (`game_state → tech_funcs → evaluate →
combat_calcs → game_state`). That matches game_state's house style (~30 engine modules are
lazy-imported there for the same reason); `tech_funcs` and `action.py` themselves import at
module level.

---

## 4. Actions (turnwheel-safe, `action.py`)

- **`ChangeRenown(team, amount)`** — team.renown += amount; reverse subtracts. `save_obj`
  already resolves `('team', nid)`.
- **`UnlockTech(team, tech_nid)`**
  - **do:** ~~assert `can_unlock`~~ **`[DEVIATION]` no `can_unlock` gate** — the *caller* gates.
    The tech-tree UI checks `can_unlock` before dispatching; the `unlock_tech` event command
    deliberately force-unlocks so a designer can grant a tech regardless of cost/prereqs.
    Idempotent instead: a tech already in `team.research` is a no-op.
  - **`[DEVIATION]` ordering: `_record()` runs FIRST**, before the effect sub-actions are built.
    Appending the nid + invalidating the cache up front is what lets tier-dependent effects
    (`UpgradeItems` reading `weapon_tier`, the fog re-reveal reading `overworld_sight_bonus`)
    see the *new* flag value. Build them first and they read the stale pre-unlock tier and
    silently under-upgrade.
  - then: `ChangeRenown(team, -cost)`; per `GrantSkill` effect an `AddSkill` on every unit in
    its grant target; per `UpgradeItems` effect an `UpgradeItem` per upgradeable inventory item.
    All as sub-actions, so reversal is automatic.
  - **`[DEVIATION]` immediate fog re-reveal:** when `_fog_of_war` is live, append a reversible
    `UpdateFogOfWar` per on-field team unit, so a sight tech takes effect the instant it
    unlocks rather than on the unit's next move (board vision is cached state).
  - **reverse:** remove nid; reverse sub-actions (refund, `RemoveSkill`, item downgrade);
    re-invalidate cache. `execute()` (turnwheel redo) re-runs `_record` then replays the stored
    sub-actions.

- **`[DEVIATION]` `UpgradeItem(unit, item, new_item_nid)`** — new action backing the
  `UpgradeItems` effect. Swaps the item in place, preserving inventory slot, droppable flag and
  remaining uses (clamped to the new item's max); relies on `@recalculate_unit` for autoequip.

`GrantSkill` for **future** units: extend the unit-add skill path (sibling of
`unit_funcs.get_global_skills`) with `get_tech_skills(unit)` — scans `unit.team`'s unlocked
techs for `GrantSkill` effects whose grant target matches this unit, returns skills to add. No
per-unit tracking; re-derived on add, exactly like global skills. **`[DEVIATION]` both
materialization sites (unlock sweep and unit construction) use `source='game',
source_type=SourceType.GLOBAL`** — non-removable, non-displaceable game-rule skills that
serialize normally (only `AURA` is filtered from `UnitObject.save`), so there's no re-derivation
on load; turnwheel still undoes them because `AddSkill.reverse` is authoritative. `UpgradeItems`
has the same two sites: the unlock sweep, and `item_funcs.resolve_upgrade_nid_for_team` on unit
construction.

---

## 5. Engine integration points (T1 flag reads — one line each)

Each is a single `if game.has_tech(...)` / `get_tech_value(...)` at the natural fork:

| Tech key | Combine | Site (as implemented) | |
|---|---|---|---|
| `exp_mult_bonus` | sum | `SimpleCombat.calculate_exp` — `total_exp *= 1 + bonus` | ✅ |
| `road_move_bonus` | max | `movement_funcs.get_mcost` | ✅ |
| `city_pop_cap_bonus` | sum | `city_funcs.run_city_upkeep` growth loop, on top of the `city_pop_cap_base` constant | ✅ |
| `draft_unlock` / `build_unlock` | set | `city_funcs` gating via `_tech_gated_values(key)` | ✅ |
| `farm_/mine_/artisan_resource_bonus` | sum | `ResourcePerTurn.get_output` | ✅ |
| `upkeep_cost_<tag>` | sum | `city_funcs.get_unit_upkeep` | ✅ |
| `overworld_sight_bonus` | max | `game_board.get_fog_of_war_radius` | ✅ |
| `weapon_tier` | max | `item_funcs.resolve_upgrade_nid` + the `UpgradesTo` item component | ✅ |
| `dungeon_sight_bonus` | max | fow / sight range | ❌ not wired |
| `hero_pool_tier` | max | tavern hero generation | ❌ not wired |
| `recruit_chance` | max | overworld neutral-enemy resolution | ❌ not wired |
| `elite_promote_<tag>` | or | promotion: grant klass skill | ❌ not wired |

**`[DEVIATION]` `upkeep_bonus_<tag>` → `upkeep_cost_<tag>`** — it reduces a cost, and the key
reads at the site as what it modifies.

**`[DEVIATION]` `overworld_sight_bonus` reads at `game_board.get_fog_of_war_radius(team)`, not
`skill_system.sight_range`.** The tech is *per-team*; `sight_range` is per-unit,
component-driven, and **codegen'd** (an edit there is clobbered on regen). Every board-sight
computation is already `skill_system.sight_range(unit) + get_fog_of_war_radius(team)`, so the
radius function is the correct single chokepoint — one line.

**`[DEVIATION]` `weapon_tier` puts the upgrade chain on the *item*, not the tech.** An
`UpgradesTo` item component (`{target_item, required_tier}`) declares Iron→Steel→Mithril;
`item_funcs.resolve_upgrade_nid(item_nid, tier)` walks it (cycle-guarded) to the highest item
the team's tier unlocks. So the tech stays a one-line flag and designers author progression
where the items live. Convoy and map loot are deliberately **not** swept — only grant-target
inventories and newly-built units.

**`[DEVIATION]` `draft_unlock` / `build_unlock` semantics: opt-in per nid.** Via
`city_funcs._tech_gated_values(key)` — a class/building nid mentioned in **any** tech's set-flag
is locked until that team unlocks it; nids no tech ever mentions stay unconditional. That means
adding a tech is the only thing that locks content, so existing projects don't silently
regress.

**`[DEVIATION]` resource bonuses key off a `BuildingTag` component**, not the building nid.
`BuildingTag` (`nid='building_tags'`, `expose=(List, Tag)`) mirrors `ItemTag` and carries no
dispatch hooks; `ResourcePerTurn.get_output` maps tag → bonus key through `RESOURCE_BONUS_TAGS`.

**`[DEVIATION]` two new first-class schema fields, not `fields`-bag entries:**
`klass.upkeep_cost` (int) and `terrain.road` (bool, since a road's `mtype` is `Normal` rather
than a distinct type). Always-evaluated mechanics belong in the typed dataclass schema, like
`max_level` / `tier`. Plus a new `city_pop_cap_base` constant.

`GrantSkill` / `UpgradeItems` sites: the unlock action + unit construction (`get_tech_skills`,
`resolve_upgrade_nid_for_team`). That's all.

---

## 6. Renown accrual (designer-wired, via events)

No engine "achievement system." Existing event triggers already cover the sources
(unit death → conquered/hero, region cleared → dungeon/relic, promotion, level-clear).
Designer awards renown in event scripts:

- New event command **`add_renown;<team>;<amount>`** → `ChangeRenown` action. Amount may be
  negative. Unknown team nid → logged error, no-op.
- **`unlock_tech;<team>;<tech>[;free]`** for scripted/story unlocks and testing → `UnlockTech`
  action. Forces the unlock: prereqs, `conditions` and the renown balance are **not** checked.
  Unknown team/tech nid → logged error, no-op; a tech already owned → no-op.
  **`[DEVIATION]` the `free` flag** skips the renown payment (`UnlockTech(…, free=True)` omits
  the `ChangeRenown` sub-action). Without it a story unlock would charge the player for a tech
  they never bought, potentially driving renown negative. Both halves stay turnwheel-reversible.

New `Tech` validator in `event_validators.py` (validates against `DB.techs`, and populates the
editor's autocomplete for the keyword).

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

0. ✅ **Data model** — `TechPrefab`/`TechEffect`/`TechCatalog`, `DB.techs` (as an
   `optional_data_type`, **not** a version bump + migrator — see §2).
   `TeamObject.renown` (+ save/restore; `research` already there).
1. ✅ **Runtime helpers** — `tech_funcs.py` (`has_tech`/`get_tech_value`/`get_tech_set`/
   `can_unlock`/flag cache) + `game` accessors.
2. ✅ **Actions** — `ChangeRenown`, `UnlockTech` (materialize `GrantSkill`/`UpgradeItems`),
   `UpgradeItem`, turnwheel.
3. ✅ **GrantSkill plumbing** — `get_tech_skills(unit)` on unit-add.
4. 🟡 **T1 flag reads** — 8 of 12 §5 sites wired; `dungeon_sight_bonus`, `hero_pool_tier`,
   `recruit_chance`, `elite_promote_<tag>` still open (their host systems aren't built yet).
5. ✅ **Events** — `add_renown`, `unlock_tech` (+ `free` flag) commands, `Tech` validator.
6. ⬜ **UI** — `TechTreeState` + entry point.
7. ✅ **Editor** — `app/editor/tech_editor/` tab. **Not** the bespoke effects-list widget the
   spec called for: effects became components (see §1), so the tab reuses
   `NewComponentProperties` and the stock component row rendering instead.

Phases 0–5 and 7 are done: techs are fully functional, scriptable via events, and authorable
in the editor. Only Phase 6 (the in-game player-facing UI) remains, and it is deliberately
unspecified — the presentation may not be a browsable tree at all (one live possibility is a
rotating set of randomly offered techs the player buys every N turns).
Coverage: `app/tests/test_tech_system.py` (combine policies + cache invalidation, `can_unlock`
gating, `UnlockTech` do/reverse/redo, effect + prefab serialization round-trips, both event
commands incl. the classic parse path, the `Tech` validator). The §5 flag *read sites* are still
untested — each needs its host system stood up.

---

## 12. Deviations from spec (all intentional)

| # | Spec said | Implemented | Why |
|---|---|---|---|
| 1 | `Collection` / `collection` / `collection_arg` | **`GrantTarget`** / `grant_target` / `grant_target_arg` | "Collection" reads as a container type in Python; the enum names *who a grant lands on*. |
| 2 | two effect kinds | **third kind `UpgradeItems`** | Retroactive weapon-tier sweeps need a materialize-at-unlock effect that isn't a skill. Kept separate from `TechFlag('weapon_tier')` so tier and sweep are independently authorable. |
| 3 | serialization version bump + migrator | **`DB.techs` as an `optional_data_type`** | Purely-additive catalog; missing `techs.json` → empty catalog, written on next save. Nothing to migrate. |
| 4 | `UnlockTech` asserts `can_unlock` | **no gate; caller gates; idempotent** | UI checks `can_unlock`; the event command must be able to force-unlock for scripting/testing. |
| 5 | (unspecified order) | **`_record()` before effects are built** | Tier-dependent effects must read the *post*-unlock flag value or they under-upgrade. |
| 6 | — | **fog re-reveal inside `UnlockTech`** | Board vision is cached, so a sight tech would otherwise only take effect on the next move. |
| 7 | `upkeep_bonus_<tag>` | **`upkeep_cost_<tag>`** | Names what it modifies at the read site. |
| 8 | sight tech in `skill_system.sight_range` | **`game_board.get_fog_of_war_radius`** | The tech is per-team; `sight_range` is per-unit and codegen'd (edits clobbered on regen). |
| 9 | `weapon_tier` read at item usability | **`UpgradesTo` item component + `resolve_upgrade_nid`** | Puts the progression chain on the items, keeps the tech a one-line flag. |
| 10 | `draft_unlock`/`build_unlock` = "base_draftable or in set" | **`_tech_gated_values`: only nids some tech mentions are gated** | Adding a tech is the only thing that can lock content — no silent regression for existing projects. |
| 11 | resource bonus on "the relevant building" | **`BuildingTag` component + `RESOURCE_BONUS_TAGS`** | Tag-driven like `ItemTag`; designers group buildings without touching engine code. |
| 12 | — | **`klass.upkeep_cost`, `terrain.road`, `city_pop_cap_base`** as typed schema fields/constant | First-class always-evaluated mechanics belong in the typed schema, not the generic `fields` bag. |
| 13 | `game.*` accessors take a team | **accept a team nid *or* a `TeamObject`; lazy-import `tech_funcs`** | Call sites hold nids (`unit.team`, `city.team`); a module-level import cycles through `evaluate`/`combat_calcs`. |
| 14 | `GrantSkill` (source unspecified) | **`source='game'`, `SourceType.GLOBAL`, both sites** | Game-rule skills: non-removable, non-displaceable, serialize normally, still turnwheel-reversible. |
| 15 | `unlock_tech` charges the cost | **`free` flag on the command / `free=True` on the action** | A story unlock shouldn't bill the player for a tech they never bought. |
| 16 | `TechEffect` dataclasses + a bespoke editor widget | **`TechComponent` classes; `key`/`combine` are class attributes; editor reuses `NewComponentProperties`** | A free-text key and a designer-chosen combine are unsafe to author. Components make both unspellable-wrong, and the entire component editor comes for free. Still no codegen'd dispatch. |
| 17 | one `GrantSkill` per skill | **`GrantSkillEffect` holds a `skills` list**; `DraftUnlock`/`BuildUnlock` hold lists too | Components are nid-keyed so a tech cannot carry two of the same; list-valued fields restore that expressiveness without a bespoke rows table, and keep free nid-rename safety. |
| 18 | — | **`CustomFlag` escape hatch** | Keeps `dungeon_sight_bonus`/`hero_pool_tier`/`recruit_chance`/`elite_promote_<tag>` authorable until their read sites land in P4. |

## 11. Explicit non-goals
- **No 4th codegen/component-hook system.** `TechEffect` is plain data interpreted by
  `tech_funcs`; the *effects* reuse existing skill/building components.
- **No condition-gated global skills** (the per-hook cost you flagged).
- **No relational modifier DB** (Civ6's storage) — take the decomposition, not the tables.
- **No engine achievement system** — renown is awarded by designer events.
