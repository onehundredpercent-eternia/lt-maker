# Plan: Render map_maker MapPrefabs in the engine

## Goal

Add an alternate rendering pathway to the engine so a level can use a
`app/map_maker/map_prefab.py::MapPrefab` (rendered live via the existing
`app/map_maker/pygame_renderers/` pipeline) instead of a
`TileMapObject` built from tileset resources. The point of using the live
pipeline (rather than exporting a baked tileset) is **runtime terrain
modification**: the engine can change a tile's map_maker Terrain and the
painters/renderers re-render just the affected region.

## Decisions already made (do not re-litigate)

1. **Storage**: MapPrefabs become a new RESOURCES category
   (`resources/map_prefabs/` inside the `.ltproj`), loaded into
   `RESOURCES.map_prefabs`, referenced by nid.
2. **Level opt-in**: per-level. `LevelPrefab` gets a new optional field
   (e.g. `map_prefab: Optional[NID]`). If set, the engine uses the MapPrefab
   pathway for that level; `tilemap` is ignored for the main map.
3. **Rendering strategy**: hybrid. Full render once at level load, baked into
   cached surfaces shaped like `LayerObject` (base image +
   `AUTOTILE_FRAMES` autotile overlay images). Per-frame cost is then
   identical to `TileMapObject` (cull + blit). Runtime terrain changes
   re-run painters only on the dirty set (`MapPrefab.terrain_grid_to_update`,
   already maintained by `MapPrefab.set()`/`erase_terrain()`) and blit the
   changed tiles back into the cached surfaces. Changes are infrequent.
4. **Terrain mapping** (map_maker `Terrain` enum → DB terrain nid, needed for
   movement cost, minimap, AI, etc.): hardcoded default table (matching
   `default.ltproj` terrain nids) + optional per-project override editable in
   the editor.

## Key existing code

- `app/engine/objects/tilemap.py` — `TileMapObject` + `LayerObject`. Its
  public surface is the contract the new object must satisfy: `width`,
  `height`, `nid`, `autotile_fps`, `check_bounds`, `on_border`,
  `get_terrain` (returns **DB terrain nid**), `get_layer`,
  `background_layers`, `foreground_layers`, `get_full_image(cull_rect)`,
  `get_foreground_image(cull_rect)`, `update`, `save`/`restore`, `layers`
  (Data of LayerObject), `weather`, `animations`, `high_animations`,
  `save_screenshot`.
- `app/map_maker/pygame_renderers/draw_tilemap.py` — already renders a
  MapPrefab to a pygame Surface, incrementally (only dirty positions
  re-painted, results cached in `MapPrefab.tile_grid`), with autotile frame
  support (`determine_sprite(tilemap, pos, autotile_num)`).
- `app/map_maker/pygame_renderers/renderer_database.py` — `RENDERERS`
  Terrain→renderer map. **Bug for our purposes**: hardcodes
  `PALETTES.outdoor_palettes()[0]` / `indoor_palettes()[0]`, ignoring the
  prefab's saved `current_indoor_palette` / `current_outdoor_palette`.
- `app/map_maker/map_prefab.py` — `MapPrefab.save()/restore()` already
  round-trips nid, size, terrain_grid, autotile_set, cliff_markers, random
  seed, palette choices. Reuse this as the on-disk resource format
  (files produced by the map_maker's Save are directly importable).
- `app/map_maker/painters/mountain_painter.py` — already engine-safe:
  Qt import deferred, synchronous solve path exists
  (`_process_group_synchronously`, `gui_processing=False`).
- `app/engine/game_state.py:351` — where `TileMapObject.from_prefab` is
  called at level load. `app/engine/objects/level.py:131` — save/restore.
- `TileMapObject.build_from_scratch` (tilemap.py:202) is a vestigial hook
  from an earlier experiment; unused. Remove or repurpose, don't emulate.

## Phases

### Phase 1 — MapPrefab as a project resource

- New RESOURCES category `map_prefabs` in `app/data/resources/`
  (follow the pattern of an existing simple category). On-disk:
  `resources/map_prefabs/<nid>.json`, content = `MapPrefab.save()` dict.
- Wire into `RESOURCES.load`/`save`. Loaders must tolerate a missing
  directory (older projects). Bump `CURRENT_SERIALIZATION_VERSION` only if
  the loader framework requires it; no data migration needed.
- Constraint: the engine must stay importable without PyQt5.
  `app.map_maker.map_prefab` → `painter_database` → painters is currently
  Qt-free at module level (verified); keep it that way.

### Phase 2 — Terrain association table

- Default dict `Terrain → DB terrain nid` in an engine-safe module.
  Every member of the `Terrain` enum must have an entry; defaults match
  `default.ltproj` terrain nids (inspect that project's terrain.json and
  pick sensible matches; e.g. GRASS→Plains, FOREST→Forest, SEA→Sea…).
- Per-project override: small new DB table or dict
  (e.g. `DB.map_terrain_associations`), serialized in game_data. Lookup
  order: project override → default → `'0'`.
- Editor UI for the override table can be a later polish item; the data
  structure and lookup land now.

### Phase 3 — Engine object: `MapPrefabTileMapObject`

New file `app/engine/objects/prefab_tilemap.py` (must pass mypy strict).

- Holds a **deep copy** of the resource MapPrefab (runtime edits must not
  mutate `RESOURCES`).
- `from_prefab(prefab)`:
  - `map_utils.set_random_seed(saved seed)` for deterministic rendering.
  - Mark all positions dirty (`reset_all`), run the painters once
    (the "process dirty positions" part of `draw_tilemap`, factored so it
    can be called without producing a full Surface).
  - Bake into one `LayerObject`-shaped 'base' layer:
    - non-autotile positions → `layer.image`
    - positions in `prefab.autotile_set` → for each of `AUTOTILE_FRAMES`
      frames, `determine_sprite(prefab, pos, frame)` → blit into
      `layer.autotile_images[frame]`
  - Set `pixel_bounds`, colorkey handling consistent with however the baked
    surfaces are created (SRCALPHA from the renderers vs colorkey in
    TileMapObject — pick one internally; the external contract is just
    "blittable surface from get_full_image").
- Interface: prefer subclassing `TileMapObject` (inherit weather,
  animations, culling, layer fade machinery, `get_full_image`, etc.) and
  overriding construction, `get_terrain`, `save`, `restore`.
  `get_terrain(pos)` = terrain-association lookup of
  `prefab.terrain_grid.get(pos)`. `get_layer` returns 'base'.
- `change_terrain(pos, terrain: Optional[Terrain])`:
  - `prefab.set(...)` / `prefab.erase_terrain(...)` (maintains dirty set,
    flood fill, autotile_set).
  - Re-run painters on the dirty set; for each re-rendered position, clear
    that tile rect in the base image and each autotile frame, then blit the
    new sprite into the right surface(s). Update `autotile_set` membership
    changes in both directions.
  - Mountain/sea flood-fill groups redo their whole blob; mountain re-solve
    is synchronous — fine for infrequent changes, but note it.
- **Save/restore must carry modifications**: `save()` stores the *current*
  `prefab.save()` dict (terrain grid, autotile_set, seed, palettes), not
  just the nid. `restore()` rebuilds the MapPrefab from the saved dict and
  re-renders. This is what makes suspend/load and turnwheel game-over
  restore keep runtime edits.
- Fix the palette problem: renderer construction (or a
  `set_palette`-style call) must honor the prefab's
  `current_indoor_palette`/`current_outdoor_palette` instead of the
  module-level `RENDERERS` hardcoding `palettes[0]`. Per-map renderer
  instances are the cleanest route.
- Painter state caution: `PAINTERS` are process-wide singletons and some
  (mountain) hold per-position `organization` state. If the editor's
  "Test Chapter" runs the engine in the same process as the Qt editor,
  qt_renderers and pygame_renderers would share painter state
  (renderer_database.py's own comment warns one frontend per process).
  Investigate: either give the engine object its own painter instances, or
  verify Test Chapter is a separate process / editor never runs the
  map_maker painters. Resolve before shipping Phase 6.

### Phase 3 outcomes (implemented, reviewed)

- `MapPrefabTileMapObject` has per-instance painters/renderers
  (`create_painters()` / `create_renderers()` factories); the painter
  singleton risk is resolved — mutable painter state (`organization`,
  `current_threads`, `vertices`) moved to instance attributes.
- pygame `renderer_database`'s own module RENDERERS also got dedicated
  painters: importing it used to flip `MountainPainter.gui_processing` on
  the shared PAINTERS the Qt editor uses (import-order side effect, fixed).
- Fixed pre-existing pygame `FloorShadingRenderer.__init__` crash (never
  called `set_palette`). NOTE: qt_renderers has the identical latent bug,
  masked by map_editor's startup `*_palette_changed(0)` calls — follow-up.
- Phase 4 wiring note: `action.py` `ShowLayer`/`HideLayer` `_leave()` reads
  `layer.terrain` directly, which is empty on this map type — the planned
  no-op guard must cover that path too.

### Phase 4 — Level wiring

- `LevelPrefab` (app/data/database/levels.py): add optional
  `map_prefab: Optional[NID]`, serialize, default None on old data.
- `game_state.load_level`: branch — if `level_prefab.map_prefab`, build
  `MapPrefabTileMapObject` from `RESOURCES.map_prefabs`, else existing path.
- `LevelObject.save/restore` (app/engine/objects/level.py): tag the tilemap
  kind in the save dict and dispatch to the right class's `restore`.
- Audit engine touchpoints:
  - `map_view` — works via get_full_image/foreground (foreground empty).
  - minimap, game_board, fog of war, pathfinding — all consume
    `get_terrain` nids → work via the association table.
  - `show_layer`/`hide_layer` event commands — only a 'base' layer exists;
    make them a logged no-op on this map type.
  - `ChangeBGTileMap` action / `bg_tilemap` — out of scope, stays
    TileMapObject-only.

### Phase 5 — Runtime change: action + event command

- New reversible `Action` (app/engine/action.py):
  `ChangeMapMakerTerrain(pos, new_terrain)` storing the old terrain for
  `reverse()` (turnwheel). Calls `change_terrain` on the map object.
  Guard: only valid when the current tilemap is a MapPrefabTileMapObject.
- New event command (e.g. `change_map_terrain;pos;terrain_name`) wired
  through `app/events/` — remember the codegen step
  (`python -m app.engine.codegen.source_generator`) regenerates wrappers.

### Phase 5 outcomes (implemented, reviewed)

- `ChangeMapMakerTerrain` action: old-terrain captured in `__init__` (file
  convention); board refresh + unit handling mirror AddRegion's TERRAIN
  branch (`reset_pos` + `boundary.reset()`, and a unit standing on `pos`
  is left/arrived so its terrain status skill re-derives immediately).
  ltcache is handled generically by `Action.__init_subclass__`.
- `change_map_terrain` command: `Position` + optional `MapMakerTerrain`
  (omit = erase). Validator is a plain `Validator`, NOT `EnumValidator` —
  deliberate: the python-eventing wrapper auto-converts only EnumValidator
  params (by display value), which would hand the event function a live
  enum on one path and a string on the other.
- **Root fix**: `Terrain.__reduce_ex__` added — the namedtuple+Enum mixin
  could not pickle (anonymous namedtuple base shares the class name), and
  `Action.save_obj`'s fallback silently stored None (= this action's erase
  sentinel), so turnwheel-through-a-suspend-save erased tiles. Regression
  test covers the full pickle round trip.

### Phase 6 — Editor integration

- Level properties tab: picker for map prefab nid (from
  `RESOURCES.map_prefabs`) as an alternative to the tilemap picker;
  mutually exclusive.
- Import: editor menu action "Import map_maker map…" that copies a
  map_maker-saved json into `resources/map_prefabs/` and registers it.
- Editor map display: wherever the editor draws the level's map (level
  editor main view, unit placement, event preview), branch: if the level
  uses a map prefab, render via the existing Qt pipeline
  (`app/map_maker/editor/draw_tilemap.py` → pixmap). A static render
  (autotile frame 0) is fine in the editor initially.

### Phase 6 outcomes (implemented, reviewed)

- Qt `create_renderers(outdoor_palette, indoor_palette, painters=None)`
  factory added to qt_renderers/renderer_database.py, mirroring the pygame
  one. Asymmetry is deliberate and documented: the Qt module-level
  RENDERERS keeps the shared PAINTERS singleton (the map_maker editor
  wires state onto it); only the factory default builds fresh painters.
- Qt renderer `__init__` palette bugs fixed (`SimpleRenderer8` override
  removed, `FloorShadingRenderer` now calls `set_palette`) — renderers
  built outside the map_maker editor no longer depend on its startup
  `*_palette_changed(0)` calls.
- `app/editor/map_prefab_display.py`: static (frame 0) QPixmap render of
  a MapPrefab via `draw_tilemap_with_renderers` (new, renderer-
  parameterized variant in map_maker/editor/draw_tilemap.py), per-prefab
  renderer cache keyed on palette nids. Two gotchas handled: cache hit on
  a *reloaded* project (same nid, fresh MapPrefab object) must still
  `reset_all()` or the render is blank; the Qt MountainRenderer flips its
  painter to QThread solving, which a one-shot render must flip back
  (`gui_processing = False`) or mountains bake unsolved.
- Level properties tab: "Select Map Maker Map..." picker (list + preview
  dialog) + "Remove Map Maker Map"; choosing a tilemap clears
  `map_prefab` (mutual exclusion); button text shows the active choice.
- File > "Import Map Maker Map...": json → `MapPrefab.restore` →
  unique-nid via `str_utils.get_next_name` → `RESOURCES.map_prefabs`.
  Saved with the project automatically (already in `save_data_types`).
- map_view.py: `resolve_level_map(level)` / `get_map_pixmap(map)` helpers
  branch all four resolution sites + both terrain-hover sites
  (association-table lookup for prefabs). Level list thumbnails branch
  too. Event preview (event_properties.py tilemap combo) deliberately
  NOT integrated — follow-up polish.

### Phase 7 — Tests + verification

- Mapping completeness test: every `Terrain` member resolves to a terrain
  nid present in `default.ltproj`.
- Headless engine-object test (pygame dummy video driver): build from a
  known MapPrefab json, assert surfaces exist, `get_terrain` returns mapped
  nids, `check_bounds`/`on_border` behave.
- Incremental-change correctness: change a tile, pixel-diff the patched
  cached surface against a from-scratch full render of the same grid
  (same technique used to verify the pygame renderer port).
- Save/restore round-trip with a modified terrain grid.
- Don't break `test_base_project_integrity`; run the full suite
  (`python -m unittest discover -s app/tests -p 'test*.py'`).
- Remember tests share the global `game` singleton — seed everything read.

## Risks / open items

- Mountain Algorithm-X synchronous solve time on large ranges at load and
  on runtime change — measure; acceptable at load, watch runtime hitch.
- Painter singleton sharing between Qt editor and in-process engine
  (Test Chapter) — investigate in Phase 3/6, see above.
- `renderer_database` palette hardcoding must be fixed for palettes other
  than index 0 to work at all.
- Weather/animation/fog interactions expected to Just Work via the
  TileMapObject subclass, but verify fog of war grids build correctly from
  the associated terrain.
