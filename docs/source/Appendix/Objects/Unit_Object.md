Unit Object
========

**Unit Objects** are the combatant objects in the game. They are split into **defined units**, as the usual playable characters, and **generic units**, as units built from classes.

If a character isn't playable, it doesn't has to be have its own **unit object**.

---------------------

## Index
* [Properties](#properties)
* [Functions](#functions)
  * [Get HP](#get-hp)
  * [Get Max HP](#get-max-hp)
  * [Get Mana](#get-mana)
  * [Get Max Mana](#get-max-mana)
  * [Get Fatigue](#get-fatigue)
  * [Get EXP](#get-exp)
  * [Get Stat](#get-stat)
  * [Get Weapon](#get-weapon)
  * [Get Internal Level](#get-internal-level)

---------------------

## Properties

|Property|Type|Role/expected value
|--|--|--
|`nid`|str|-
|`position`|tuple[int, int]|Coordinate in (x, y) format.
|`team`|str|`player`, `other`, `enemy` or `enemy2`.
|`party`|str|Party NID.
|`klass`|str|Class NID.
|`variant`|str|Animation variant.
|`level`|int|-
|`generic`|bool|`True` if the unit is a generic.
|`ai`|str|AI NID
|`ai_group`|str|-
|`faction`|str|Faction NID
|`name`|str|-
|`desc`|str|-
|`tags`|list[str]|-
|`stats`|dict[str: int]|Base stats and respective values.
|`growths`|dict[str: int]|Growth rates and respective values.
|`wexp`|dict[str: int]|Weapon EXP and respective values.
|`portrait_nid`|str|-
|`affinity`|str|Affinity NID
|`notes`|list[tuple[str, str]]|-
|`items`|list[ItemObject]|Personal inventory.
|`skills`|list[SkillObject]|All active skills, including debuffs and skills that have the `global` component.
|`finished`|bool|`True` if the unit cannot act at the current turn.
|`dead`|bool|`True` if the unit died.
|`traveler`|str|NID of rescued/paired unit. Can be `None`.

---------------------

## Functions

### Get HP
``` Text
[UnitObject].get_hp()
  -> 'int'
```

Returns the current HP value of an unit.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_hp()` → Returns the <u>unit</u> object current HP value.
* `u('Eirika').get_hp()` → Returns <u>Eirika</u>'s current HP value.
</p></details>

---------------------

### Get Max HP
``` Text
[UnitObject].get_max_hp()
  -> 'int'
```

Returns the maximum HP value of an unit at its current state.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_max_hp()` → Returns the <u>unit</u> object maximum HP value.
* `u('Eirika').get_max_hp()` → Returns <u>Eirika</u>'s maximum HP value.
</p></details>

---------------------

### Get Mana
``` Text
[UnitObject].get_mana()
  -> 'int'
```

Returns the current MANA value of an unit.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_mana()` → Returns the <u>unit</u> object current MANA value.
* `u('Eirika').get_mana()` → Returns <u>Eirika</u>'s current MANA value.
</p></details>

---------------------

### Get Max Mana
``` Text
[UnitObject].get_max_hp()
  -> 'int'
```

Returns the maximum MANA value of an unit at its current state.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_max_hp()` → Returns the <u>unit</u> object maximum MANA value.
* `u('Eirika').get_max_hp()` → Returns <u>Eirika</u>'s maximum MANA value.
</p></details>

---------------------

### Get Fatigue
``` Text
[UnitObject].get_fatigue()
  -> 'int'
```

Returns the fatigue value of an unit at its current state.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_fatigue()` → Returns the <u>unit</u> object fatigue value.
* `u('Eirika').get_fatigue()` → Returns <u>Eirika</u>'s fatigue value.
</p></details>

---------------------

### Get EXP
``` Text
[UnitObject].get_exp()
  -> 'int'
```

Returns the current exp value of an unit.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_fatigue()` → Returns the <u>unit</u> object current EXP value.
* `u('Eirika').get_fatigue()` → Returns <u>Eirika</u>'s current EXP value.
</p></details>

---------------------

### Get Stat
``` Text
[UnitObject].get_stat(stat_nid)
  -> '<Stat>'
```

Returns the combined value of a base stat with all of its modifiers.

**Args**:
* `stat_nid`: Stat NID.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_stat('MAG')` → Returns the total <u>INT</u> of the <u>unit</u> object.
* `target.get_stat('SPD')` → Returns the total <u>SPD</u> of the <u>target</u> object.
* `u('Eirika').get_stat('LCK')` → Returns the <u>Eirika</u>'s total <u>LCK</u> value.
</p></details>

### Get Weapon

``` Text
[UnitObject].get_weapon()
  -> '[ItemObject]'
```

Returns the weapon **instance** equipped by the unit object.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_weapon()` → Returns the weapon equipped by the <u>unit</u> object.
* `target.get_weapon()` → Returns the weapon equipped by the <u>target</u> object.
* `u('Eirika').get_weapon()` → Returns the weapon equipped by <u>Eirika</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* It is possible to use direct object reference in any part of the engine that has access to it, such as the `condition` and `combat condition` skill components and the event editor.
* Weapon that have the `spell` item component aren't equipped, even if they're the only eligible weapon in the inventory. In that case, the function will return `None`.
</p></details>

---------------------

### Get Internal Level

``` Text
[UnitObject].get_internal_level()
  -> 'int'
```

Returns the unit object's internal level, the sum of all levels an unit obtained through its natural promotion path.

<details><summary><strong>Examples</strong>:</summary><p>

* `unit.get_internal_level()` → Returns the <u>unit</u> object internal level value.
* `u('Eirika').get_internal_level()` → Returns <u>Eirika</u>'s internal level value.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* Pre-promoted units have the value calculated as if promoted only at its previous classes maximum levels.
</p></details>
