Useful Functions
========
<small>`Last Updated 2023-06-11`</small>

<div class="note">
The functions from <b>item_funcs</b> and <b>unit_funcs</b> weren't added to this page yet.
</div>

**Functions** are predefined set of commands. They can be recognized by the structure `function_name()`. Functions can be built to receive input values, known as `args`, to be used in their commands, those are declared inside the parenthesis `()` structure, such as `function_name(arg1, arg2)`. A function can have as many args as it needs, or none at all.

To call a function, you must write its name using the structure format, along arg values.

``` text
function_name(0, 'A')
function_name(arg2='A', arg1=0)
```

Values can be assigned either by using the order of arg declaration or by referencing the arg name directly. Both lines above yield the same result, but the first takes use of the declaration order. The declaration order is respected even if the value has been namely assigned.

Args can also be defined with a specific `type`, rendering other inputs invalid. In the case of `function_name(arg1, arg2: int)`, `arg2` only accepts whole numbers.

Some functions will have args with pre-defined values, as it is the case with `function_name(arg, optional_arg1='default_value', optional_arg2='default_value')`. By doing so, the arg becomes an optional element and can be skipped when calling the function.

``` text
function_name(0)
function_name(1, 'B')
function_name(1, optional_arg2='C')
function_name(1, 'B', optional_arg2='C')
```

The declaration order rule still applies, however you still need to fill in each arg between the last obligatory arg and the first optional arg you want in order for the function to work.

Functions can also return a value obtained from the commands within them. It can range from a simple `True` or `False` to a list of elements, such as all units in the map. This kind of function expects a certain type of result but sometimes that won't be possible due the circumstances, like trying to get an unit in an vacant tile. The most common exceptions are:
* _`Object` type - Returns `None` if no object matches the function input criteria.
* `List[]` - Returns an empty list, represented by `[]`, if no object matches the function input criteria.

At last, some functions are tied to (script) classes and can only be accessed through the class itself or their object instances.

``` text
object_name.function_name()
object_name.function_name(2)
```

------------------

## Index
* [Achievements](#achievements)
  * [Has Achievements](#has-achievements)
* [Combat](#combat)
  * [Can Counterattack](#can-counterattack)
  * [Compute Advantage](#compute-advantage)
* [Items](#items)
  * [Get Item](#get-item)
  * [Get Weapon](#get-weapon)
  * [Has Item](#has-item)
  * [Weapon Type](#weapon-type)
* [Map Functions](#map-functions)  
  * [Region](#region)
    * [Any Unit in Region](#any-unit-in-region)
    * [Get Allies Within Distance](#get-allies-within-distance)
    * [Get Closest Allies](#get-closest-allies)
    * [Get Terrain](#get-terrain)
    * [Get Units in Area](#get-units-in-area)
    * [Get Units in Region](#get-units-in-region)
    * [Get Units Within Distance](#get-units-within-distance)
  * [Skills](#skills)
    * [Get Debuff Count](#get-debuff-count)
    * [Get Skill](#get-skill)
    * [Has Skill](#has-skill)
  * [Units](#units)
    * [Get Support Rank](#get-support-rank)
    * [Is Dead](#is-dead)
    * [U](#u)
  * [Variables](#variables)
    * [V](#v)

------------------

In this page you'll get a pletora of useful functions that can be employed in events, skills and regions.

## Achievements

#### Has Achievement
``` text
has_achievement(nid)
  -> 'bool'
```

Returns `True` if the achievement is completed.

**Args**:
* `nid`: Achievement NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `has_achievement('Ironman')` →  Checks if the <u>achievement</u> was completed.
</p></details>


---------------------

## Combat

#### Can Counterattack
``` Text
combat_calcs.can_counterattack(attacker, aweapon, defender, dweapon)
  -> bool
```

Returns `True` if the defender can counterattack.

**Args**:
* `attacker`: Attacker NID.
* `aweapon`: Attacker weapon object.
* `defender`: Defender NID.
* `dweapon`: Defender weapon object.

<details><summary><strong>Examples</strong>:</summary><p>

* `combat_calcs.can_counterattack(unit, unit.get_weapon(), target, target.get_weapon())` → Checks if the <u>target</u> object can counterattack the <u>unit</u> object while both are using their equipped weapons.
* `combat_calcs.can_counterattack(u('Eirika'), u('Eirika').get_weapon(), unit, unit.get_weapon())` → Checks if <u>Eirika</u> can counterattack the <u>unit</u> object while both are using their equipped weapons.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* The first example and its opposition are the most common application for this function.
</p></details>

---------------------

#### Compute Advantage
``` Text
compute_advantage(unit1, unit2, item1, item2, advantage=True)
  -> 'bool'
```

Returns the calculation result of weapon type advantage of an unit over another.

**Args**:
* `unit1`: Attacker unit NID.
* `unit2`: Defender unit NID.
* `item1`: Attacker weapon NID.
* `item2`: Defender weapon NID.
* `advantage` <u>(optional)</u>: Set to `False` to check for disadvantage.

<details><summary><strong>Examples</strong>:</summary><p>

* `combat_calcs.compute_advantage(unit, unit.get_weapon(), target, target.get_weapon())` → Checks if the <u>unit</u> has weapon advantage against <u>target</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* In most of the cases, both `item1` and `item2` args will be fed with the `.get_weapon()` function referencing to the corresponding unit object.
* Type advantage and disadvantage may appear or disappear based on how they are set, as it is possible to disable them through their rank levels.
* Since weapons have two lists for type vantages and disadvantages, changing `unit1` and `unit2` in the args may not result in the desired result. Some projects will require the `advantage` arg to check it properly. Alternatively, it is possible for a weapon to have both advantages and disadvantages against another time simultaneously.
</p></details>

---------------------

## Items

#### Get Item
``` text
get_item(unit, item)
  -> '[ItemObject]'
```

Returns an item object **instance** owned by an unit through the item NID.

**Args**:
* `unit`: Unit NID. Use `'convoy'` to check the convoy.
* `item`: Item NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_item('Eirika', 'Rapier')` → Returns the <u>Rapier</u> instance carried by <u>Eirika</u>.
* `get_item('convoy', 'Heal')` → Returns a <u>Heal</u> instance from the <u>convoy</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* Since the function can only access a single item object, it isn't very effective when dealing with multiple instance of the same item in a single unit, or the convoy as a whole.
</p></details>

---------------------

#### Get Weapon
Private function from [Unit Object](/source/Appendix/Objects/Unit_Object#Get-Weapon). Returns the weapon **instance** equipped by the unit object.

---------------------

#### Has Item
``` text
has_item(item, nid=None, team=None, tag=None, party=None)
  → bool
```

Returns `True` if an item is being held by an unit, based on parameters used. Require that one of the optional <u>arg</u> has a value to return `True`.

**Args**:
* `item`: Item NID.
* `nid` <u>(optional)</u>: Used to check a specific unit NID.
* `team` <u>(optional)</u>: Used to check for team. Must be `player`, `enemy`, `enemy2` or `other`.
* `tag` <u>(optional)</u>: Used to check for tag.
* `party` <u>(optional)</u>: Used to check for party.

<details><summary><strong>Examples</strong>:</summary><p>

* `has_item("Iron Sword", team="player")` → Checks if any <u>player</u> unit is carrying an <u>Iron Sword</u> item.
* `has_item("Iron Sword", tag='Flying', team="player",)` → Checks if any <u>player</u> unit with the <u>Flying</u> tag is carrying an <u>Iron Sword</u> item.
* `has_item("Sacred Stone", party='Eirika')` → Checks if <u>Eirika</u>'s party has the item <u>Sacred Stone</u>.
</p></details>

---------------------

### Weapon Type
``` Text
item_system.weapon_type(unit, item)
  -> '<WeaponType>'
```

Returns the type of a weapon held by an unit.

**Args**:
* `unit`: Unit object. Doesn't accept NID.
* `item`: Item object. Doesn't accept NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `item_system.weapon_type(unit, unit.get_weapon())` → Returns the weapon type of the weapon equipped by the <u>unit</u> object.
* `item_system.weapon_type(u('Eirika'), u('Eirika').get_weapon())` → Returns the weapon type of the weapon equipped by the <u>Eirika</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* Unknown if it has any practical application aside checking the weapon type of the unit equipped weapon, for <u>-Faire</u> and <u>Breaker</u> like skills.
</p></details>

---------------------

## Map Functions

### Region

#### Any Unit In Region
``` text
any_unit_in_region(region, nid=None, team=None, tag=None)
  -> 'bool'
```

Returns `True` if any unit matching the criteria for the given region.

**Args**:
* `region`: Region NID.
* `nid` <u>(optional)</u>: Used to check a specific unit NID.
* `team` <u>(optional)</u>: Used to check for team. Must be `player`, `enemy`, `enemy2` or `other`.
* `tag` <u>(optional)</u>: Used to check for tag.

<details><summary><strong>Examples</strong>:</summary><p>

* `any_unit_in_region('NorthReinforcements')` → Checks if the <u>NorthReinforcements</u> region is being occupied by one or more units.
* `any_unit_in_region('NorthReinforcements', team='player')` → Checks if the <u>NorthReinforcements</u> region is being occupied by one or more <u>player</u> units.
* `any_unit_in_region('WestReinforcements', tag='Flying', team='player')` → Checks if the <u>WestReinforcements</u> region is being occupied by one or more <u>player</u> units that has the <u>Flying</u> tag.
* `any_unit_in_region('WestReinforcements', nid='Eirika')` → Checks if <u>Eirika</u> is in the <u>WestReinforcements</u> region.
</p></details>

---------------------

#### Get Allies Within Distance

``` text
get_allies_within_distance(position, dist: 'int' = 1)
  -> 'List[Tuple[UnitObject, int]]'
```

Returns a list containing all `player` units and relative distance within a radius from the given coordinate.

**Args**:
* `position`: Coodinates or unit NID.
* `dist` <u>(int, optional)</u>: Radius size to search. Defaults to `1`, as a single tile space.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_allies_within_distance('Eirika', 2)` → Returns a list containing <u>Eirika</u> and `player` units adjacent to her.
* `get_allies_within_distance((5,5))` → Returns a list containing the `player` unit at the coordinate (5,5), or an empty list if none apply.
* `get_allies_within_distance((0,2), 5)` → Returns a list containing all `player` units within 5 a tile radius to the coordinate (0,2).
</p></details>

---------------------

#### Get Closest Allies
``` text
get_closest_allies(position, num: 'int' = 1)
  -> 'List[Tuple[UnitObject, int]]'
```

Returns a list containing a definable amount of `player` units and their relative distance from the given coordinate, based on proximity.

**Args**:
* `position`: Coordinate or unit NID.
* `num` <u>(int, optional)</u>: Number of units to search for. Defaults to `1`.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_closest_allies('Eirika', 3)` → Returns a list containing the 3 nearest `player` units to <u>Eirika</u>'s position, including <u>Eirika</u> if eligible.
* `get_closest_allies((5,5))` → Returns a list containing the nearest `player` unit to the coordinate (5,5).
* `get_closest_allies((0,2), 5)` → Returns a list containing the 5 nearest `player` units to the coordinate (0,2).
</p></details>

---------------------

#### Get Terrain
``` text
get_terrain(pos)
  -> '[NID]'
```

Returns the terrain NID at position coordinate.

**Args**:
* `pos`: Coordinate or `unit`

<details><summary><strong>Examples</strong>:</summary><p>

* `get_terrain('Eirika')` → Checks the terrain NID of the tile that <u>Eirika</u> is standing on.
* `get_terrain((5,5))` → Checks the terrain NID of the tile at coordinate (5,5).
</p></details>

---------------------

#### Get Units in Area
``` text
get_units_in_area(position_corner_1: 'Tuple[int, int]', position_corner_2: 'Tuple[int, int]')
  -> 'List[UnitObject]'
```

Returns a list contaning all units within a rectangular area, defined by two coordinate points.

**Args**:
* `position_corner_1` and `position_corner_2` <u>(Tuple[int, int])</u>: Coordinate (x,y).

<details><summary><strong>Examples</strong>:</summary><p>

* `get_units_in_area((0,0),(2,5))` → Returns a list containing all units within the 18 tiles area of X0 to X2 and Y0 to Y5.
* `get_units_in_area((1,2),(2,3))` → Returns a list containing all units within the 4 tiles area of X1 to X2 and Y2 to Y3.
</p></details>

---------------------

#### Get Units in Region
``` text
get_units_in_region(region, nid=None, team=None, tag=None)
  -> 'List[UnitObject]'
```

Returns a list containing all units within the given region, filtered by parameters.

**Args**:
* `region`: Region NID.
* `nid` <u>(optional)</u>: Used to check a specific unit NID.
* `team` <u>(optional)</u>: Used to check for team. Must be `player`, `enemy`, `enemy2` or `other`.
* `tag` <u>(optional)</u>: Used to check for tag.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_units_in_region('NorthReinforcements')` → Returns a list containing all units occupying the <u>NorthReinforcements</u> region.
* `get_units_in_region('NorthReinforcements', team='player')` → Returns a list containing all `player` units occupying the <u>NorthReinforcements</u> region.
* `get_units_in_region('WestReinforcements', tag='Flying', team='player')` → Returns a list containing all `player` units that has the <u>Flying</u> tag occupying the <u>NorthReinforcements</u> region.
* `get_units_in_region('WestReinforcements', nid='Eirika')` → Returns a list containing <u>Eirika</u> if she exists in the <u>WestReinforcements</u> region.
</p></details>

---------------------

#### Get Units Within Distance

``` text
get_units_within_distance(position, dist: 'int' = 1, nid=None, team=None, tag=None, party=None)
  -> 'List[Tuple[UnitObject, int]]'
```

Returns a list containing all units and relative distance within a radius from the given coordinate.

**Args**:
* `position`: Coodinates or unit NID.
* `dist` <u>(int, optional)</u>: Radius size to search. Defaults to `1`, as a single tile space.
* `nid` <u>(optional)</u>: Used to check a specific unit NID.
* `team` <u>(optional)</u>: Used to check for team. Must be `player`, `enemy`, `enemy2` or `other`.
* `tag` <u>(optional)</u>: Used to check for tag.
* `party` <u>(optional)</u>: Used to check for party.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_units_within_distance('Eirika', 2)` → Returns a list containing <u>Eirika</u> and adjacent units.
* `get_units_within_distance((5,5))` → Returns a list containing the the unit at the coordinate (5,5), or an empty list if none apply.
* `get_units_within_distance('Eirika', 5, tag='Flying', team='player')` → Returns a list containing all `player` units within 4 tiles from <u>Eirika</u> that have the `Flying` tag.
* `get_units_within_distance((0,2), 5)` → Returns a list containing all units within 5 a tile radius to the coordinate (0,2).
</p></details>

---------------------

## Skills

#### Get Debuff Count
``` text
get_debuff_count(unit)
  -> 'int'
```

Returns the number of skills with the `negative` skill component that the unit has.

**Args**:
* `unit`: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_debuff_count('Eirika')` → Returns the number of debuffs <u>Eirika</u> has.
</p></details>

---------------------


#### Get Skill
``` text
get_skill(unit, skill)
  -> '[SkillObject]'
```

Returns a skill object **instance** by the skill NID.

**Args**:
* `unit`: Unit NID.
* `skill`: Skill NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_skill('Eirika', 'Astra')` → Returns an instance of <u>Astra</u> from <u>Eirika</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* Since the function can only access a single item object, it isn't very effective to take multiple instances of a same skill nor to check how many of them the unit has.
</p></details>

---------------------

#### Has Skill
``` text
has_skill(unit, skill)
  -> 'bool'
```

Returns `True` if the unit has an instance of a skill.

**Args**:
* `unit`: Unit NID.
* `skill`: Skill NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_skill('Eirika', 'Astra')` → Checks if <u>Eirika</u> has <u>Astra</u>.
</p></details>

---------------------

## Units

For private functions, check the [Unit Object](/source/Appendix/Objects/Unit_Object) page.

---------------------

#### Get Support Rank
``` Text
get_support_rank(unit1, unit2)
  -> '<SupportRank>'
```

Returns the last valiadated support rank value between two units.

**Args**:
* `unit1` and `unit2`: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_support_rank('Eirika', 'Seth')` → Returns the last valiadated support rank of <u>Eirika</u> and <u>Seth</u>.
</p></details>

---------------------

#### Is Dead
``` Text
is_dead(unit)
  -> 'bool'
```

Returns `True` if unit is dead

**Args**:
* `unit`: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `is_dead('Eirika')` → Checks if <u>Eirika</u> is dead or alive.
</p></details>

---------------------

#### U
```
u(unit)
  -> '[UnitObject]'
```

Shorthand for `game.get_unit`. Returns the unit object **instance** through an unit NID.

**Args**:
* `unit`: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `u('Eirika')` → Returns <u>Eirika</u>'s unit object.
</p></details>

---------------------

## Variables

#### V
```
v(varname, fallback=None)
  -> 'Any'
```

Shorthand for `game.level_vars.get` and `game.game_vars.get`. Returns a variable value. If a the same variable name is used in `level_vars` and `game_vars`, the first will be taken.

**Args**:
* `varname`: Variable name.
* `fallback`: Predefined value if the engine fails to find the variable.

<details><summary><strong>Examples</strong>:</summary><p>

* `v('KillStreak')` → Returns the variable value.
* `v('KillStreak', 0)` → Returns the variable value. If the variable doesn't exist, returns `0` instead.
</p></details>
