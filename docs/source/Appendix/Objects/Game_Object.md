Game Object
========

The game object is a very powerful source of information about the state of the game. It keeps track of all units in the current level as well as all non-generic units ever loaded into the game (whether alive or dead).

---------------------

## Properties

|Property|Type|Role/expected value
|--|--|--
|`game_vars`|dict|Every game variable and their values.
|`game_vars`|dict|Every level variable and their values.
|`playtime`|float|Save playtime.
|`turncount`|int|Current turn.
|`units`|list|Contains all units tracked in the game.
|`mode`|[DifficultyModeObject]|Current difficulty mode.
|`level`|[LevelObject]|Current level.
|`tilemap`|[TileMapObject]|Current tilemap.
|`party`|[PartyObject]|Current party.

---------------------

## Functions

```
 #check_dead(str) -> bool
 #check_alive(str) -> bool
get_unit(str) -> UnitObject  # Returns a Unit with the given nid
get_region(str) -> RegionObject  # Returns a Region with the given nid
get_party(str) -> PartyObject # Returns the party with the given nid

get_all_units() -> list  # Returns all alive units on the map
get_player_units() -> list  # All alive player units on the map
get_enemy_units() -> list  # All alive enemy units on the map
get_all_units_in_party(str?) -> list  # All non-generic player units in the given party (defaults to current party)
get_units_in_party(str?) -> list  # All alive non-generic player units in the given party (defaults to current party)
 #get_money() -> int  # money of current party
```

### Check Alive/Dead
``` Text
check_alive(str) / check_dead(str)
  -> 'bool'
```

Returns `True` if the unit is alive/dead.

**Examples**:
* `check_alive('Seth')` →  Checks if the unit <u>Seth</u> is alive.
* `check_dead('Orson')` →  Checks if the unit <u>Orson</u> is dead.

---------------------

### Get Unit
``` Text
get_unit()
  -> '[UnitObject]'
```

Returns .

**Examples**:
*

---------------------

### Get Money
``` Text
get_money()
  -> 'int'
```

Returns the funds value from the current party.
