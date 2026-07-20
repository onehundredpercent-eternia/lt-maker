# World Maker Improvement Plan (Civ 4-style outdoor map generation)

This plan upgrades `app/world_maker/` (outdoor/overworld map autogeneration) using techniques
researched from Civilization IV's actual map generation source (`CvMapGeneratorUtil.py`,
`CvMapGenerator.cpp`, `Highlands.py`, shipped with the game). Each phase is self-contained and can
be handed to an implementing agent independently, but the **dependency order matters**:

- Phase 1 → Phase 2 → Phase 3 (strict order)
- Phase 4 requires Phases 1–2 (should land after 3, see ordering note in Phase 4)
- Phase 5 requires Phase 2; independent of 3–4
- Phase 6 requires Phase 1 only
- Phase 7 goes last (after whichever other phases are done)

Each phase lists: goal, algorithm spec, exact parameter names, acceptance criteria, and pitfalls.
Do not implement beyond the phase you were given. Do not refactor neighboring code
opportunistically unless the phase says to.

---

## Section 0: Context for the implementing agent (read this first, always)

### What this code is

`app/world_maker/` generates outdoor tile maps for a Fire Emblem-style engine. Two files:

- `app/world_maker/terrain_generation.py` — the generator. Entry point `generate_terrain(theme, seed)`
  returns a `WorldTileMap` whose `terrain_grid: Dict[Pos, Terrain]` maps `(x, y)` to a `Terrain` enum.
- `app/world_maker/themes.py` — declares `theme_parameters` (a `Data` of `ThemeParameter`) and
  `theme_presets`. A "theme" at runtime is a plain `Dict[NID, Any]` of parameter nid → value.

The UI caller is `app/map_maker/editor/autogenerate_outdoor_map.py` (Qt dialog). It calls
`terrain_generation.generate_terrain(theme, seed)` and applies the result to the open tilemap.
Theme parameters declared in `themes.py` appear automatically in that dialog — adding a
`ThemeParameter` is all that's needed for UI exposure.

Terrain enum: `app/map_maker/terrain.py`. Outdoor-relevant members:
`GRASS, LIGHT_GRASS, NOISY_GRASS, SAND, ROAD, SPARSE_FOREST, FOREST, THICKET, CLIFF, HILL,
MOUNTAIN, RIVER, SEA, DESERT, DESERT_CLIFF, DESERT_ROCK, BRIDGEH, BRIDGEV, HOUSE, CASTLE, RUINS`.
There is no snow/tundra terrain.

Noise: `app/map_maker/simplex_noise.py` provides
`gen_noise_map(size, seed, starting_frequency, amplitude, octaves, lacunarity, gain) -> Dict[Pos, float]`
and `normalize_noise_map`. The elevation noise map is generated at `(width + 2, height + 2)` and
shifted so it covers `(-1, -1)` to `(width, height)` — a 1-tile border ring outside the map. Several
loops rely on that ring existing (they index `noise_map[pos]` for out-of-bounds `pos` without
checking). Preserve the ring; do not "fix" those lookups by clamping.

### Current pipeline (before this plan)

1. One simplex elevation field, normalized to [0, 1], plus `elevation` additive modifier and
   optional `water_border` radial falloff.
2. Sink fill: raise any tile below all 4 cardinal neighbors to the min neighbor value.
3. Fixed absolute thresholds classify terrain: `>= 0.75` MOUNTAIN, `0.70–0.75` HILL,
   `0.40–0.70` NOISY_GRASS, `0.35–0.40` SAND, `< 0.35` SEA.
4. Rivers: greedy strictly-downhill walks from high-elevation tiles to low.
5. Cliffs: Sobel edge detection on the elevation field, applied to NOISY_GRASS tiles.
6. Forests: second noise field, absolute thresholds, applied to NOISY_GRASS tiles.

### The Civ 4 techniques being adopted (summary)

1. **Percentile thresholds**: Civ's `getHeightFromPercent(p)` derives every threshold from the
   noise field's own value distribution, so "35% water" is exact for every seed.
2. **Independent noise fields per concern**: land/water, hills, peaks, forests, lakes, desert each
   get their own field with their own frequency ("grain"). Nothing correlates unless you want it to.
3. **Hills as percentile *bands*, peaks nested inside hill bands**: a band (level set) of a
   continuous noise field is a long snaking ridge, not a blob. This is how Civ gets mountain
   *ranges* with hill skirts.
4. **River seeding with per-landmass quotas + spacing constraints + deterministic per-tile jitter**
   (from `CvMapGenerator.cpp::addRivers/doRiver/getRiverValueAtPlot`): rivers distribute evenly and
   merge instead of crisscrossing.
5. **Lakes from a separate coarse field.**
6. **Climate as a decoupled "skin"** over topology (latitude axis + fuzz + own field).
7. **Macro-layout hints** (Civ's `HintedWorld`): a coarse designer-controlled block grid blended
   into the elevation field for guaranteed macro structure.
8. **Post-generation normalization** for gameplay fairness (Civ edits the map around starting
   plots; we guarantee passability/connectivity).

### House rules (project conventions — follow these)

- Determinism is mandatory: same theme + same seed ⇒ byte-identical `terrain_grid`. Never use the
  global `random` module in generation logic (the existing `random.seed(time.time())` for seed
  == -1 selection is the one grandfathered exception). Use `self.random` (`static_random.LCG`),
  the map seed, or deterministic hashes of tile coordinates.
- Module-level imports only (no imports inside functions) unless there is a real cycle.
- No defensive `getattr`/`hasattr` probing; no speculative `try/except`. If an attribute or key
  must exist, index it and let it fail loud.
- Copy lists with `.copy()` or `[:]`, not `list(...)`.
- Write type hints on new code. Do NOT run mypy.
- Do not break `app/tests/test_base_project_integrity.py` (don't touch `.ltproj` data).
- Comments state constraints code can't show — never narrate what the next line does.

### How to verify work (headless, no Qt needed)

```python
# scratch script — run with: python -m <path.to.script>  or  python -c "..."
from app.world_maker import themes, terrain_generation
from app.map_maker.terrain import Terrain

CHARS = {Terrain.SEA: '~', Terrain.SAND: '.', Terrain.NOISY_GRASS: ' ', Terrain.HILL: 'n',
         Terrain.MOUNTAIN: 'A', Terrain.RIVER: 'r', Terrain.CLIFF: '#', Terrain.FOREST: 'f',
         Terrain.THICKET: 'F', Terrain.DESERT: 'd', Terrain.GRASS: ' ', Terrain.BRIDGEH: '=',
         Terrain.BRIDGEV: 'H'}

theme = themes.get_theme("Default")
tm = terrain_generation.generate_terrain(theme, 42)
for y in range(tm.height):
    print(''.join(CHARS.get(tm.get_terrain((x, y)), '?') for x in range(tm.width)))
```

Also render a few seeds at size (25, 25) and (40, 30). For final visual confirmation only, the Qt
dialog can be used via `python run_map_maker.py` (user will do this part).

There is currently no test module for world_maker. Phase 1 creates
`app/tests/test_world_maker.py`; later phases extend it. Run with
`python -m unittest app.tests.test_world_maker`. Tests must not import Qt.

---

## Phase 1 — Percentile thresholds (small diff, do first)

**Goal**: replace fixed absolute thresholds with thresholds computed from the elevation field's own
value distribution, so terrain ratios are exact for every seed.

### Spec

1. Add a helper in `terrain_generation.py`:

```python
def get_threshold_from_percent(noise_map: Dict[Pos, float], percent: float,
                               width: int, height: int) -> float:
    """Value v such that `percent`% of in-bounds tiles have noise < v.
    Mirrors Civ 4's CyFractal.getHeightFromPercent. Only in-bounds tiles
    (0 <= x < width, 0 <= y < height) count; the border ring is excluded."""
```

   Implementation: collect in-bounds values, sort ascending, index
   `min(len - 1, int(len * percent / 100))`. `percent <= 0` returns a value below the minimum
   (e.g. `min - 1.0`) so nothing qualifies; `percent >= 100` returns above max.

2. Replace the classification in `generate_terrain_grid_from_noise` with cumulative percentile
   thresholds. New theme parameters (in `themes.py`), replacing the roles of the hardcoded
   constants (defaults chosen to match today's average look):

   - `sea_percent` (default 35, type `percent`) — "Portion of map that is sea"
   - `sand_percent` (default 5) — "Portion of map that is beach/sand (above sea)"
   - `hill_percent` (default 5) — "Portion of map that is hills"  *(replaced in Phase 2)*
   - `mountain_percent` (default 25) — "Portion of map that is mountains"  *(replaced in Phase 2)*

   Classification: sort once, compute thresholds at cumulative percents
   `sea`, `sea+sand`, `100-mountain-hill`, `100-mountain`. Tiles below `sea` threshold → SEA, next
   band → SAND, top band → MOUNTAIN, band under it → HILL, everything else → NOISY_GRASS.

3. Compute percentiles **after** the `elevation` modifier, `water_border` falloff, and sink fill —
   i.e. on the final field. (This makes `water_border` and hints in Phase 6 compose without
   breaking ratios; note that with percentile seas, the existing `elevation` parameter no longer
   changes land fraction — that is intended and fine, leave the parameter alone.)

4. Keep `MOUNTAIN_THRESHOLD`/`SEA_THRESHOLD` constants temporarily: `generate_rivers_from_noise`
   still uses them as start/end candidate bounds. Change those two uses to the freshly computed
   percentile threshold *values* (pass them in as arguments). Delete the module constants once
   nothing references them.

5. Keep the retry-on-None loop in `generate_terrain` as-is.

### Tests (create `app/tests/test_world_maker.py`)

- Determinism: two calls with same theme/seed produce equal `terrain_grid` dicts.
- Ratio exactness: for 10 seeds at size (25, 25), fraction of SEA tiles within 2 percentage points
  of `sea_percent`; same for MOUNTAIN with `mountain_percent`.
- Ratio tracking: set `sea_percent` to 10 and to 60; observed sea fraction moves accordingly.

### Pitfalls

- The noise map covers the border ring; percentile must be computed over in-bounds tiles only, but
  classification still only writes in-bounds tiles (existing behavior — keep).
- `percent` theme type exists in `app/dungeon_maker/themes.py` (imported by `world_maker/themes.py`)
  — reuse it, don't invent a new type.

---

## Phase 2 — Independent noise fields; hills/peaks as bands (the mountain-range phase)

**Goal**: decouple mountains/hills from the elevation field so they form elongated ranges anywhere
on land, exactly as Civ 4's `FractalWorld.generatePlotTypes` does with `hillsFrac`/`peaksFrac`.

### Spec

1. The elevation field now decides **only**: SEA / SAND / land (land defaults to NOISY_GRASS).
   Remove `hill_percent`/`mountain_percent` cumulative logic from Phase 1's classification.

2. Generate two new noise fields sized `(width, height)` (no border ring needed), from the same
   `seed` but distinct derived seeds (`seed + 1`, `seed + 2` — document the offsets as constants):

   - **hill field** — one new theme param: `hill_frequency` (default 0.15)
   - **pass field** — no new params: `pass_frequency = hill_frequency * 2` (finer than hills so a
     low patch cuts *across* a ridge rather than tracking it)

   *(Revised: Civ's peak field as a direct classifier was implemented and rejected — a field
   independent of the hill field varies **along** a ridge rather than across it, splitting each
   range into all-mountain and all-hill stretches instead of a spine with hill skirts. The
   second field survives as the pass field, which modulates spine width instead of classifying
   tiles; see step 3.)*

   Octaves/lacunarity/gain are **not** theme params — frequency is the only knob with a visible,
   explainable effect (Civ likewise exposes only grain). Module constants `NOISE_LACUNARITY = 2.0`,
   `NOISE_GAIN = 0.5`, plus a helper:

   ```python
   def derive_octaves(frequency: float) -> int:
       """Octaves whose wavelength falls below ~2 tiles (the tile Nyquist limit)
       add nothing visible, so octave depth follows from frequency."""
       return max(1, math.ceil(math.log2(0.5 / frequency)))
   ```

   All noise fields in this plan get their octave count from `derive_octaves(frequency)` and
   their lacunarity/gain from the shared constants.

3. Band classification, applied only to tiles the elevation pass left as NOISY_GRASS (not SEA, not
   SAND):

   - `highland_percent` theme param (default 30): total portion of *land* that is hills+mountains.
   - Two bands centered at the 25th and 75th percentile of the hill field (Civ's
     `hillGroupOneBase = 25`, `hillGroupTwoBase = 75`). Band half-width in percentile terms is
     `highland_percent / 4` (two bands × two half-widths). A tile is *highland* if its hill-field
     value falls inside either band. Compute band edges with `get_threshold_from_percent` over the
     hill field's land tiles.
   - `peak_percent` theme param (default 40): mountains are the **most-central slice of each
     band**, modulated by the pass field. Per highland tile compute centrality
     `c = |percentile − center| / half_width` (0 on the ridge crest, 1 at the band edge) and score
     `s = c / pass_noise**PASS_STRENGTH` (constant, 2.0 — the exponent biases the hill budget
     toward carving passes over thinning skirts); tiles with the lowest `peak_percent` percentile
     of `s` (over highland
     tiles) become MOUNTAIN, the rest HILL. Every range is a mountain spine flanked by hill
     skirts; where the pass field nears zero the score diverges and the spine pinches off into an
     all-hill gap — a mountain pass. Percentile-thresholding `s` keeps mountain coverage exactly
     `peak_percent` regardless of the pass field's distribution.

4. Rivers and cliffs keep reading the elevation field for now (Phase 3 replaces river logic;
   cliffs stay Sobel-on-elevation permanently — they represent elevation discontinuities, which is
   still the right semantic).

5. Remove the now-dead `hill_percent`/`mountain_percent` params from `themes.py`; add the new ones.
   Collapse the pre-existing noise knobs the same way: keep `starting_frequency` and
   `forest_starting_frequency`, delete `octaves`/`lacunarity`/`gain` and
   `forest_octaves`/`forest_lacunarity`/`forest_gain`, and route the elevation and forest fields
   through `derive_octaves` + the shared constants. Preset `"Default"` stays `{}`.

### Tests

- Coverage: over 10 seeds, highland fraction of land within 3 points of `highland_percent`;
  mountain fraction of highland within 5 points of `peak_percent`.
- Determinism test still passes.
- Shape (weak automated proxy for "ranges not blobs"): mean size of 4-connected MOUNTAIN+HILL
  components > 1.5 tiles AND at least one component with bounding-box aspect ratio ≥ 3:1 in at
  least half of 10 seeds. Also render 5 seeds as ASCII in the test's docstring-driven manual check
  (print when run with `-v` is fine) — the human will eyeball.

### Pitfalls

- Bands are on the *hill field's* percentiles, not the elevation field's.
- All band edges (outer and nested mountain band) are percentiles over **land tiles**. Getting the
  pool wrong silently skews coverage.
- Do not let hills/mountains overwrite SAND or SEA.
- Forest generation runs after this and only converts NOISY_GRASS — unchanged, still correct.

---

## Phase 3 — River overhaul (port of Civ 4's addRivers/doRiver)

**Goal**: rivers that are evenly distributed per landmass, start in highlands, wander plausibly
across flat land, merge with each other instead of crossing, and terminate at water/map edge.
This **replaces** `generate_rivers_from_noise` entirely.

### Spec

Constants (module level): `RIVER_SOURCE_MIN_RIVER_RANGE = 4`, `RIVER_SOURCE_MIN_SEA_RANGE = 2`
(Chebyshev distance), `RIVER_JITTER = 10`.

Theme params: remove `river_incidence`; add `tiles_per_river_tile` (int, default 40) — "One river
tile is targeted per this many land tiles per landmass". 0 disables rivers.

**Landmass identification**: flood-fill 4-connected non-SEA tiles → `area_id` per tile, area sizes.

**Source selection — four passes** (Civ's loop, adapted from edges to tiles). A landmass is
*under quota* while `river_tiles_placed(area) < area_size // tiles_per_river_tile + 1`.
Iterate tiles in fixed row-major order (determinism); for each pass, a tile is a candidate source if:

- Pass 0: terrain is HILL or MOUNTAIN.
- Pass 1: not within `RIVER_SOURCE_MIN_SEA_RANGE` of SEA, and `self.random.randint(0, 7) == 0`.
- Pass 2: HILL or MOUNTAIN, and its landmass is under quota. Ranges halved.
- Pass 3: any land tile whose landmass is under quota. Ranges halved.

Every candidate must additionally be ≥ `RIVER_SOURCE_MIN_RIVER_RANGE` (halved in passes 2–3) from
any already-placed river tile and ≥ `RIVER_SOURCE_MIN_SEA_RANGE` (halved) from SEA — except pass 1
already encodes its own sea check, mirror Civ and apply both anyway. When a candidate qualifies,
run the flow walk immediately (so later spacing checks see its tiles).

**Flow walk** (replaces strictly-downhill rule; Civ's `doRiver` + `getRiverValueAtPlot`):

- Altitude class per tile: MOUNTAIN and CLIFF = 4, HILL = 3, land (grass/forest family) = 2,
  SAND = 1, SEA and RIVER = 0. Off-map = 0 for termination purposes but contributes 40 to
  neighbor sums (Civ's `NUM_PLOT_TYPES * 10` edge-avoidance).
- `river_value(pos) = altitude_class(pos) * 20 + sum(altitude_class of 8 neighbors)
  + jitter(pos)` where `jitter(pos) = (pos[0] * 43251267 + pos[1] * 8273903 + seed) % RIVER_JITTER`.
  Jitter must be a pure function of position and map seed — this is what makes two rivers
  approaching the same valley converge and merge (same tile always wins ties the same way).
- From the current tile, candidate steps are the 4 cardinal neighbors, excluding: the reverse of
  the previous step, the reverse of the river's *first* step (Civ's no-U-turn pair), any tile
  already in this river's path, and MOUNTAIN/CLIFF tiles (hard-excluded — a tile river drawn
  through a mountain reads as wrong in FE, unlike Civ's edge rivers).
- Step to the candidate with minimum `river_value`. If no candidates, the river ends (dead end —
  keep what was placed if length ≥ 3, else erase it).
- Terminate successfully when stepping onto SEA, onto an existing RIVER tile (merge), or off-map.
- Safety cap: `width * height` steps.
- Write RIVER onto every path tile whose terrain is HILL, NOISY_GRASS, SAND, FOREST, SPARSE_FOREST,
  or THICKET (rivers may cut through forest). Note: this phase runs **before** forest generation in
  the current pipeline order — reorder so rivers run **after** forests and cliffs, matching Civ
  (plots → terrain → rivers → features is Civ's order, but our forests are terrain-mutating, so:
  elevation classes → hills/peaks → cliffs → forests → rivers → (Phase 4 moves lakes before
  rivers)). Update `_generate_terrain_process` accordingly.

### Tests

- Quota: for 10 seeds, every landmass of size ≥ `tiles_per_river_tile` has ≥ 1 river tile.
- Sources spaced: no two river *source* tiles within Chebyshev 2 of each other (track sources in a
  return value or module-inspectable attribute for the test).
- Termination: every generated river path ends at SEA / RIVER / off-map or was erased (length < 3).
- Determinism.
- `tiles_per_river_tile = 0` produces zero RIVER tiles.

### Pitfalls

- Iterate positions and directions in fixed order everywhere; `Dict` iteration order is insertion
  order — build position lists with explicit `range` loops.
- The old code's "no 4 consecutive same-direction steps" filter is being deleted with the rest —
  don't port it; the no-U-turn rule plus jitter replaces it.
- Spacing checks must see tiles from rivers placed earlier in the *same* pass.
- `utils.flatten_list` over all rivers inside the walk loop was O(n²) in the old code — track
  placed river tiles in a `set` instead.

---

## Phase 4 — Lakes

**Goal**: inland water bodies. Modeled on `Highlands.py`'s dedicated lake fractal (blob lakes), not
Civ's core random-single-tile method.

### Spec

- New coarse noise field: `lake_frequency` (default 0.08), octaves via `derive_octaves` (= 3 at
  the default) with the shared lacunarity/gain constants, derived seed `seed + 3`.
- Theme param `lake_percent` (default 3, type `percent`); 0 disables.
- A tile becomes SEA (lakes are SEA terrain — the autotiler handles inland sea; if visual check
  shows bad coast transitions on tiny lakes, that is a tileset issue to report, not code to hack
  around) if: lake-field value below the `lake_percent` percentile (computed over land tiles),
  current terrain is NOISY_GRASS / SAND / FOREST / SPARSE_FOREST / THICKET / HILL, and Chebyshev
  distance to existing SEA > 2 (so lakes don't fuse into the coastline).
- **Ordering**: run after forests, **before** rivers (improvement over Civ: rivers can then
  terminate in lakes naturally, since river termination already checks SEA). Final pipeline order
  after this phase: elevation classes → hills/peaks → cliffs → forests → lakes → rivers.

### Tests

- Lake tiles exist for `lake_percent = 8` on ≥ 8 of 10 seeds; zero for `lake_percent = 0`.
- No lake tile within Chebyshev 2 of pre-lake coastline SEA (test by running classification with
  lakes disabled, diffing).
- Determinism.

### Pitfalls

- Percentile pool = land tiles only, else sea tiles eat the lake budget.
- Distance-to-sea must be measured against the *pre-lake* SEA set (snapshot it), or the second lake
  tile placed measures distance to the first and self-blocks blobs.

---

## Phase 5 — Climate skin: deserts (gated on tileset verification)

**Goal**: decouple climate from topology, Civ `TerrainGenerator`-style. The tileset has
DESERT / DESERT_CLIFF / DESERT_ROCK but no snow/tundra, so scope = arid axis only.

**Gate first**: in the map maker UI, hand-paint DESERT adjacent to GRASS/NOISY_GRASS, SAND, SEA,
FOREST and confirm the autotiler produces acceptable transitions. If transitions are broken, stop
and report — do not implement around it. (Fallback design if partially broken: require a 1-tile
SAND buffer ring around desert regions; only implement if told to.)

### Spec

- Theme params: `climate_axis` (choice: `none` / `north_hot` / `south_hot` / `west_hot` /
  `east_hot`, default `none`), `desert_percent` (default 0, type `percent`).
- Latitude function, Civ's with fuzz: `lat(pos)` = normalized coordinate along the chosen axis in
  [0, 1] (1 = hot end), plus fuzz `(0.5 - variation_noise(pos)) * 0.2`, clamped to [0, 1].
  Variation field: frequency 0.15, derived seed `seed + 4`.
- Desert field: own noise (frequency 0.12, derived seed `seed + 5`). A land tile becomes desert if
  `lat(pos) >= 0.55` AND desert-field value falls in the top `desert_percent` percentile band
  (pool: land tiles with `lat >= 0.55`).
- Conversion map: NOISY_GRASS/GRASS/LIGHT_GRASS → DESERT; CLIFF → DESERT_CLIFF; HILL →
  DESERT_ROCK; FOREST/SPARSE_FOREST/THICKET → DESERT (climate kills forest); MOUNTAIN, SEA, SAND,
  RIVER unchanged.
- Ordering: after cliffs and forests, before lakes and rivers (rivers through desert are desirable;
  lakes in desert read as oases — both free wins from ordering).
- `climate_axis = none` or `desert_percent = 0` ⇒ phase is a no-op.

### Tests

- No-op when disabled (grid identical with/without the pass when `desert_percent = 0`).
- With `north_hot`, desert tiles' mean y significantly below map midline (or above, depending on
  y-axis direction — pin down which end is "north" in this codebase: y=0 is the top row, which
  this plan calls north).
- Determinism.

---

## Phase 6 — Macro-layout hints (HintedWorld analog)

**Goal**: guaranteed macro structure ("one big landmass", "sea on the east") with noise detail on
top — Civ's `HintedWorld` block-hint concept, adapted from fractal-seeding to field blending.

### Spec

- Block grid: `ceil(width / 5) × ceil(height / 5)` blocks (block size 5 fixed).
- A *layout* assigns each block a hint value in [0, 1]: land blocks `0.75 + rand*0.15`, water
  blocks `0.15 + rand*0.15`, unassigned `0.45 + rand*0.10` (rand from `self.random`, fixed
  iteration order).
- Layout algorithms (theme param `macro_layout`, choice, default `none`):
  - `none` — skip entirely (field unchanged).
  - `pangaea` — land seed at grid center, random-walk expansion (Civ's
    `expandContinentBy`: repeatedly pick a random owned block, random cardinal neighbor, claim it
    if unowned) until 55% of blocks are land; all other blocks water.
  - `continents` — two land seeds at (25%, 50%) and (75%, 50%) of the grid, each expanded to 27%
    of blocks; remainder water.
  - `coastal` — pick a random map edge; the two block-rows/columns along it are water, everything
    else land.
- Upsample hint grid to per-tile field with bilinear interpolation (block centers as sample
  points; clamp at edges).
- Blend into the elevation field **before** sink fill and percentile classification:
  `elevation[pos] = (1 - w) * elevation[pos] + w * hint[pos]` with theme param `hint_weight`
  (float, default 0.55). Because Phase 1 made all thresholds percentile-based, blending cannot
  break terrain ratios — sea stays exactly `sea_percent`; hints only decide *where* it goes.
- Update preset: `"Pangaea": {"macro_layout": "pangaea"}` (drop the `water_border: True` hack from
  the preset; leave the `water_border` parameter itself in place for users).

### Tests

- Pangaea: for 10 seeds, largest 4-connected land component contains ≥ 85% of all land tiles.
- Continents: for 10 seeds, ≥ 2 land components of ≥ 20 tiles each in ≥ 7 seeds (noise can bridge
  them sometimes; that's acceptable).
- `none` layout: grid identical to pre-phase behavior.
- Determinism.

### Pitfalls

- All randomness through `self.random` / derived seeds; layout expansion order must be
  deterministic (shuffle via `self.random`, not `random.shuffle`).
- Blend before the `water_border` falloff so both compose (falloff remains an outer multiplier).

---

## Phase 7 — Connectivity normalization (gameplay pass, run last)

**Goal**: every generated map is fully traversable by ground units — Civ normalizes the map around
starting plots; an FE map's equivalent invariant is "one connected passable region".

### Spec

- Passable terrain: everything except SEA, MOUNTAIN, CLIFF, DESERT_CLIFF. (RIVER counts as
  impassable for connectivity purposes too — FE infantry can't cross rivers; bridges fix it.)
- After all other generation: flood-fill 4-connected passable regions. Ignore regions smaller than
  4 tiles (convert them entirely to their surrounding impassable terrain's most common type — tiny
  pockets inside mountain ranges are noise, not gameplay).
- While more than one qualifying region remains: take the two largest, find the closest pair of
  tiles between them (BFS from the smaller region's border through impassable tiles), and carve
  the connecting path:
  - MOUNTAIN → HILL; CLIFF → NOISY_GRASS; DESERT_CLIFF → DESERT (a "mountain pass")
  - RIVER → BRIDGEH if the path through it runs horizontally, BRIDGEV if vertically
  - SEA: only carve if the water gap along the path is ≤ 3 tiles (BRIDGEH/BRIDGEV as above);
    if every candidate path needs a longer water crossing, leave the regions separate — island
    maps are legitimate. Prefer non-SEA paths in the BFS (weight SEA steps 5× — implement as a
    small Dijkstra rather than plain BFS).
- Iteration cap: number of initial regions (each merge reduces the count by ≥ 1).
- Theme param `ensure_connectivity` (bool, default True).

### Tests

- 25 seeds, default theme: exactly one passable region of size ≥ 4 (allowing legitimately
  unreachable island cases only when SEA gaps > 3 separate them — assert instead that no two
  regions are separated purely by MOUNTAIN/CLIFF/RIVER).
- Carve minimality: carved tile count per map ≤ 15 on 25×25 default maps (guards against the pass
  bulldozing terrain).
- `ensure_connectivity = False` ⇒ no-op.
- Determinism.

---

## Appendix A — Known quirks in the existing code (fix only when the touching phase says so)

- `generate_cliffs_from_noise`: `non_max_suppression` is defined but never called — dead code
  (delete whenever this function is next touched). `convolve` squares the kernel sum and the
  magnitude then applies `sqrt(x² + y²)` on already-squared values; mathematically muddled but
  produces usable edges — leave unless cliffs visibly misbehave.
- The old rivers' "no 4 consecutive same-direction steps" filter was actually correct (rejects only
  when the candidate equals the last three segment directions) — noted here because it *looks* like
  an `or`/`and` bug; it is deleted wholesale in Phase 3 regardless.
- Sink-fill comment says "lowest average" but the code takes the min of neighbors — the code
  behavior is the intended one; fix the comment if editing that function.
- `number_of_rivers` in the old code actually counted river *tiles*, not rivers (superseded by
  Phase 3's quota).

## Appendix B — Source references (for the human, not needed by implementers)

Civ 4 files this plan is derived from. Local install root (as of 2026-07):
`C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword`

- [CvMapGeneratorUtil.py (local)](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Sid%20Meier's%20Civilization%20IV%20Beyond%20the%20Sword/Assets/Python/CvMapGeneratorUtil.py)
  — `<root>\Assets\Python\CvMapGeneratorUtil.py`.
  FractalWorld hill/peak bands (`generatePlotTypes`, ~line 177), HintedWorld block hints
  (~line 219), TerrainGenerator latitude + fuzz (~line 970), FeatureGenerator (~line 1116).
  Web mirror: [K-Mod fork on GitHub](https://github.com/karadoc/Civ4-K-Mod/blob/master/Assets/Python/CvMapGeneratorUtil.py)
  (lightly modified fork; the classes above are intact).
- [CvMapScriptInterface.py (local)](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Sid%20Meier's%20Civilization%20IV%20Beyond%20the%20Sword/Assets/Python/EntryPoints/CvMapScriptInterface.py)
  — `<root>\Assets\Python\EntryPoints\CvMapScriptInterface.py`.
  "ORDER OF OPERATIONS" comment block = the full generation pipeline, including the
  normalizeAddRiver/normalizeRemovePeaks start-fairness hooks that inspired Phase 7.
- [CvMapGenerator.cpp (local)](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Sid%20Meier's%20Civilization%20IV%20Beyond%20the%20Sword/Beyond%20the%20Sword/Mods/Rhye's%20and%20Fall%20of%20Civilization/CvGameCoreDLL/CvMapGenerator.cpp)
  — `<root>\Beyond the Sword\Mods\Rhye's and Fall of Civilization\CvGameCoreDLL\CvMapGenerator.cpp`
  (SDK source shipped inside Rhye's mod; another copy in `The Road to War\CvGameCoreDLL\`).
  Lines 261–297 `addLakes`; 299–368 `addRivers` (4-pass sources, quota, spacing); 372–527
  `doRiver` (no-U-turn greedy descent); 1113–1164 `getRiverValueAtPlot` (altitude formula +
  deterministic per-tile jitter, the river-merging trick).
  Web mirror: [K-Mod's CvMapGenerator.cpp](https://github.com/karadoc/Civ4-K-Mod/blob/master/CvGameCoreDLL/CvMapGenerator.cpp)
  (same base code; line numbers will drift).
- [Highlands.py (local)](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Sid%20Meier's%20Civilization%20IV%20Beyond%20the%20Sword/PublicMaps/Highlands.py)
  — `<root>\PublicMaps\Highlands.py`.
  Closest analog to FE-scale maps: all-land regional map, dedicated lake fractal
  (`generatePlotTypes`, ~line 136), grain choice exposed as a "mountain style" user option
  (clustered / ridgelines / scattered).
- Further reading, not directly used by this plan:
  [Tectonics.py (local)](file:///C:/Program%20Files%20(x86)/Steam/steamapps/common/Sid%20Meier's%20Civilization%20IV%20Beyond%20the%20Sword/Beyond%20the%20Sword/PublicMaps/Tectonics.py)
  (plate-tectonics elevation model);
  `<root>\Beyond the Sword\Mods\Realism Invictus\PrivateMaps\RI_PerfectMongoose_v332.py`
  (PerfectWorld lineage: wind/rainfall simulation);
  [CivFanatics map scripts guide](https://civfanatics.com/civ4/map-scripts-guide/).

Plain-text root path is repeated above deliberately: `file://` links break if the plan is read
outside a link-aware viewer, and the install may move — search for the filename under the Steam
library if the links go stale.
