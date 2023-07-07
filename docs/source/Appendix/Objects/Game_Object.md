Game Object
========

The game object is a very powerful source of information about the state of the game. It keeps track of all units in the current level as well as all non-generic units ever loaded into the game (whether alive or dead).

------------------

## Index
* [Properties](#properties)
* [Functions](#functions)
  * [Check Alive/Dead](#check-alive-dead)
  * [Get Unit](#get-unit)
  * [Get Region](#get-region)
  * [Get Party](#get-party)
  * [Get All Units](#get-all-units)
  * [Get Player Units](#get-all-units)
  * [Get Enemy Units](#get-enemy-units)
  * [Get All Units in Party](#get-all-units-in-party)
  * [Get Units in Party](#get-units-in-party)
  * [Get Money](#get-money)

---------------------

## Properties

|Property|Type|Role/expected value
|--|--|--
|`game_vars`|dict|Every game variable and their values.
|`level_vars`|dict|Every level variable and their values.
|`playtime`|float|Save playtime.
|`turncount`|int|Current turn.
|`units`|list|Contains all units tracked in the game.
|`mode`|[DifficultyModeObject]|Current difficulty mode.
|`level`|[LevelObject]|Current level.
|`tilemap`|[TileMapObject]|Current tilemap.
|`party`|[PartyObject]|Current party.

---------------------

## Functions

### Check Alive/Dead
``` Text
check_alive(str) / check_dead(str)
  -> 'bool'
```

Returns `True` if the unit is alive/dead.

**Args**:
* **str**: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `check_alive('Seth')` →  Checks if the unit <u>Seth</u> is alive.
* `check_dead('Orson')` →  Checks if the unit <u>Orson</u> is dead.
</p></details>

---------------------

### Get Unit
``` Text
get_unit()
  -> '[UnitObject]'
```

Returns a Unit with the given nid.

**Args**:
* **str**: Unit NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_unit('Eirika')` → Returns <u>Eirika</u>'s unit object.
</p></details>

---------------------

### Get Region
``` Text
get_region()
  -> '[RegionObject]'
```

Returns the party with the given nid.

**Args**:
* **str**: Region NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_region('NorthReinforcements')` → Returns <u>NorthReinforcements</u> region object.
</p></details>

---------------------

### Get Party
``` Text
get_party(str)
  -> '[PartyObject]'
```

Returns the party with the given nid.

**Args**:
* **str**: Party NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_party('Ephraim')` → Returns <u>Ephraim's party</u> object.
</p></details>

---------------------

### Get All Units
``` Text
get_all_units()
  -> 'List[UnitObject]'
```

Returns all alive units on the map.

---------------------

### Get Player Units
``` Text
get_player_units()
  -> 'List[UnitObject]'
```

Returns all alive player units on the map.

---------------------

### Get Enemy Units
``` Text
get_enemy_units()
  -> 'List[UnitObject]'
```

Returns all alive enemy units on the map.

---------------------

### Get All Units in Party
``` Text
get_all_units_in_party(str)
  -> 'List[UnitObject]'
```

Returns all alive non-generic player units in the given party.

**Args**:
* **str** <u>Optional</u>: Party NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_units_in_party()` → Returns a list containing all non-generic player units in the <u>current</u> party.
* `get_units_in_party('Ephraim')` → Returns a list containing all non-generic player units in <u>Ephraim's party</u>.
</p></details>

---------------------

### Get Units in Party
``` Text
get_units_in_party(str)
  -> 'list'
```

Returns all alive non-generic player units in the given party.

**Args**:
* **str** <u>Optional</u>: Party NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `get_units_in_party()` → Returns a list containing all <u>alive</u> non-generic player units in the <u>current</u> party.
* `get_units_in_party('Ephraim')` → Returns a list containing all <u>alive</u> non-generic player units in <u>Ephraim</u>'s party.
</p></details>

---------------------

### Get Money
``` Text
get_money()
  -> 'int'
```

Returns the funds value from the current party.
