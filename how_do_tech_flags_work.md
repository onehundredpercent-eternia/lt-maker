How TechFlag('farm_resource_bonus', 5, combine=sum) unlocks + what follows

Where it lives. The flag isn't unlocked on its own — it's one effect inside a TechPrefab in DB.techs. E.g.:
TechPrefab('FarmImprovement', renown_cost=150,
           effects=[TechFlag('farm_resource_bonus', 5, combine=sum)])
(Authored in techs.json; the editor tab is Phase 7, not built — so today it's hand-authored or scripted.)

The unlock — action.do(action.UnlockTech(team, 'FarmImprovement')). That's the one mechanism. Three ways to reach it:
- Tech-tree UI (Phase 6, not built): player spends renown; UI calls tech_funcs.can_unlock then dispatches the action.
- Event command unlock_tech;<team>;<tech> (Phase 5, not built): scripted/story unlock.
- Today (Phases 0–4 done): dispatch the UnlockTech action directly. Fully functional, just no player-facing entry yet.

What UnlockTech.do() does (all reversible sub-actions):
1. Idempotent guard (already owned → no-op).
2. ChangeRenown(team, -150) — pays the cost (this tech has no GrantSkill, so no per-unit skills materialize).
3. Appends 'FarmImprovement' to team.research.
4. tech_funcs.invalidate_flag_cache(team) — marks the flag cache dirty.

How the flag becomes readable. Next game.get_tech_value(team, 'farm_resource_bonus'):
- cache is dirty → _rebuild_flag_cache scans team.research, finds the TechFlag, folds it by combine: sum → cache['farm_resource_bonus'] = 5. Cached; O(1) reads until the next unlock invalidates it.

The gameplay effect (per city turn). At player-turn start StatusUpkeepState → city_funcs.run_city_upkeep(city) → building_system.on_upkeep(city) fans out to every building → for the worked Farm, ResourcePerTurn.on_upkeep:
- get_output(city): base food:5 + (Farm has tag Farm) game.get_tech_value(city.team, 'farm_resource_bonus') = 5 + 5 = 10.
- action.do(action.ChangeCityFood(city, 10)) — city gains 10 food that turn, not 5.
- The city-menu Work tab shows the boosted 10 too (same get_output path → display and income never diverge).

Gating for it to actually fire: the Farm must be built in a city and worked (on_upkeep self-gates on city.is_worked), and the tech is per-team (city.team), so only that team's cities benefit.

Stacking (combine=sum): unlock Farm Improvement 1/2/3 (each +5, same key) → cache = 15 → Farm yields 5+15 = 20/turn.

Turnwheel: rewinding past the unlock turn refunds the 150 renown, drops the tech from research, re-invalidates the cache → bonus reverts to 0. Fully symmetric.

Same story for Mine (mine_resource_bonus→production) and Artisan (artisan_resource_bonus→gold).