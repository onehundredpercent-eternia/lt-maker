# Data Types

The data used in computing has a type assigned. This characteristic prevents certain values to be added at the wrong places, partially acting as a safety mechanism against statements with multiple interpretations.

A classic example is `9+9`. If we're taking each 9 as a **number**, the result will be `18`, however if they are **units of text**, the result should be `99`. By assigning data types, we ensure that the variable will always have the desired interpretation.

It is possible to force certain data types into different variables if they certain properties, though it is more likely that it will result in an error or undesirable outcome in your code.

|Type|Content|Casting|Examples
|--|--|--|--
|`bool`|`True`, `False`, `0` or `1`|`False`, `True`
|`int`|Whole numbers, positive or negative|`9`, `0`, `184`
|`float`|Non-integer numbers|`99.9`, `12`, `5`
|`string`|Text, within quotation marks|`"I'm a string value"`, `"Lex Talionis"`
|`list/tuple`|Collection of items from any other type|`["A","B","C"]`, `[1,2,4,8,16]`, `['Eirika', 'Seth']`

------------

## Index
* [Casting](#casting)
* [Numeric Types](#numeric-types)
  * [Operations](#operations)
* [Text Types](#text-types)
  * [Concatenation](#concatenation)
  * [Character Slicing](#character-slicing)
  * [Useful Methods](#useful-methods)
* [List/Tuple Types](#list-tuple-types)  
  * [Standard Operations](#standard-operations)
    * [Element at Index](#element-at-index)
    * [Index Interval](#index-interval)
    * [List Combining](#list-combining)
  * [List Comprehensions](#list-comprehensions)
    * [Base](#base)
    * [Property Filtering](#property-filtering)
    * [Conditional Filtering](#conditional-filtering)
    * [Item Replacement](#item-replacement)

------------

## Casting

It is possible to force a type into another by using a casting function. It is done by setting the value inside the type as if it were a function, as in `int(cast_value)`. The most common structures are `int()`, `float()` and `str()` for simple types and `list()`, `tuple()` and `set()` for iterables.

<details><summary><strong>Examples</strong>:</summary><p>

* `int("35")` → Converts the <u>string</u> "35" into an <u>int</u>.
* `str(9.9)` → Converts the <u>float</u> 9.9 into a <u>string</u>.
* `float(var_name)` → Converts the variable <u>var_name</u> into a <u>float</u>.
</p></details>


 ------------

## Numeric Types

### Operations

|Operation|Sign|Example|Result
|--|--|--|--
|**Addition**|`+`|6 + 2|8
|**Subtraction**|`-`|0.8 - 0.1|0.7
|**Multiplication**|`*`|0.8 * 3|2.4
|**Division**|`/`|6 / 3|2
|**Floor Division**|`//`|6 // 4|1
|**Exponentiation**|`**`|0.8 ** 2|36
|**Modulus**|`%`|6 % 4|2

------------

## Text Types

### Concatenation

``` python
"textA" + "textB"
```

Combines two strings into a new string.

<details><summary><strong>Examples</strong>:</summary><p>

``` python
lord_char = "Eirika"
paladin = "Seth"
```

* `"Hello" + "World` → Adds <u>"Hello"</u> in the front of <u>"World"</u>, resulting in <u>"HelloWorld"</u>
* `lord_char + " is the princess of Renais."` → Adds <u>lord_char</u> in the front of <u>" the princess of Renais."</u>, resulting in <u>"Eirika is the princess of Renais."</u>
* `"The party lord is " + lord_char` → Adds <u>"The party lord is "</u> in the front of <u>lord_char</u>, resulting in <u>"The party lord is Eirika"</u>
* `"Who is that? " + paladin + "?"` → Adds <u>"Who is that? "</u> in the front of <u>paladin</u> and <u>"?"</u> at the end, resulting in <u>"Who is that? Seth?"</u>
* `lord_char + " and " + paladin` → Adds <u>lord_char</u> in the front of <u>" and "</u> and <u>paladin</u> at the end, resulting in <u>"Eirika and Seth"</u>
* `lord_char + " level is " + str(10)` → Adds <u>lord_char</u> in the front of <u>" level is "</u> and adds the <u>converted the number 10</u> at the end, resulting in <u>"Eirika level is 10"</u>
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* Spaces are considered characters for strings and will only be added if they exist in the string or text. This can be seen in the first example as neither of the texts have a space and both words get fused in a single element.
</p></details>


------------

### Character Slicing

``` Text
variable_name[start_chararacter:end_character]`
```

Slices a string based on the `start_character` and `end_character` positions.

* `start_character`/`end_character`: Character index. If not provided, takes the first/last index value. Set to negative to move from the end to the start.

<details><summary><strong>Examples</strong>:</summary><p>

``` python
weapon1 = "Iron Sword"
weapon2 = "Iron Axe"
weapon3 = "Silver Sword"
```
* `weapon`<1/2/3>`[0:4]` → `Iron`, `Iron`, `Silv`
* `weapon`<1/2/3>`[:4]` → `Iron`, `Iron`, `Silv`
* `weapon`<1/2/3>`[5:10]` → `Sword`, `Axe`, `r Swo`
* `weapon`<1/2/3>`[-5:]` → `Sword`, `n Axe`, `Sword`
* `weapon`<1/2/3>`[-5:-2]` → `Swo`, `n A`, `Swo`
</p></details>


------------

### Useful Methods

```python
text = " the LT, wiki!  "
```

|Method|Description|Example Syntax|ExampleOutput
|--|--|--|--
|`capitalize()`|Converts the first character to upper case|`text.capitalize()`|`"  The LT, wiki!  "`
|`casefold()`|Converts string into lower case|`text.casefold()`|`"  the l t, wiki!  "`
|`replace(<old>, <new>)`|Returns a string where a specified value is replaced with a specified value.|`text.replace("wiki", "engine")`|`"  the LT, engine!  "`
|`split()`|Splits the string at the specified separator, and returns a list. Defaults to </u>blank spaces</u>.|`text.split()`<br/>`text.split(", ")`|`["the", "LT,", "Wiki!"]`<br/>`["the LT", "wiki!"`
|`strip()`|Remove all empty spaces both sides at a string, start and end. Use `lstrip()` (left) and `rstrip()` (right) to remove them from side side. Spaces between letters won't be removed.|`text.strip()`|`"the LT wiki!"`
|`title()`|Converts the first character of each word to upper case|`text.title()`|`"  The LT Wiki!  "`
|`upper()`|Converts a string into upper case|`text.upper()`|`"  THE LT WIKI!  "`

## List/Tuple Types

**List/Tuples** are array type data structures. They acts as a collection of variables inside a single variable, gaining the ability to store more than a single piece of data at once. If variables are boxes, arrays are shelves.

<div class="danger">
These terms may be used interchangeably outside the developer environment. Unless a page is referencing directly to a python script, take them as the same thing.
</div>

### Standard Operations

#### Element at Index

``` python
List[index_number]
```

Returns the value of a list element at the index position. Negative numbers are interpreted as moving from the end of the list to the start of the list.

* `index_number`: Item index. Set to negative to move from the end to the start.

<details><summary><strong>Examples</strong>:</summary><p>

``` python
char_list = ['Eirika', 'Seth', 'Vanessa', 'Moulder', 'Ross', 'Garcia']
int_var = 2
```
* `char_list[0]` → Returns the value of the first index of the list, <u>Eirika</u>.
* `char_list[1]` → Returns the value of the second index of the list, <u>Seth</u>.
* `char_list[-1]` → Returns the value of the last index of the list, <u>Garcia</u>.
* `char_list[-3]` → Returns the value of the third last index of the list, <u>Moulder</u>.
* `char_list[int_var]` → Returns the value of the index at the position of <u>int_var</u> value, being <u>Vanessa</u>.
* `char_list[-int_var]` → Returns the value of the index at the position of <u>int_var</u> negative value, being <u>Ross</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* It must have a valid index to work. Passing a non-integer value or a value greater than the final index of the list, either positive or negative, will result in an error.
* The first index of the list is `0`.
</p></details>


------------

#### Index Interval

``` python
List[start_index:end_index]
```

Returns a slice of the list containing elements within an index interval range.

* `start_index`/`end_index`: Item index. If not provided, takes the first/last index value. Set to negative to move from the end to the start.

<details><summary><strong>Examples</strong>:</summary><p>

``` python
char_list = ['Eirika', 'Seth', 'Vanessa', 'Moulder', 'Ross', 'Garcia']
int_var = 2
```
* `char_list[0:2]` → Returns a <u>list</u> containing the two first indexes of the list, <u>'Eirika', 'Seth'</u>.
* `char_list[4:5]` → Returns a <u>list</u> containing the value of the fifth index of the list, <u>'Ross'</u>.
* `char_list[1:-3]` → Returns a <u>list</u> containing the items from the second index to the forth last index, <u>'Seth', 'Vanessa'</u>.
* `char_list[2:]` → Returns a <u>list</u> containing the items from the third index onwards, <u>'Vanessa', 'Moulder', 'Ross', 'Garcia'</u>.
* `char_list[-3:-1]` → Returns a <u>list</u> containing the items from the third last item in the list to the second last, <u>'Moulder', 'Ross'</u>.
* `char_list[int_var:4]` → Returns a <u>list</u> containing the items from the <u>int_var</u> index position to the fifth index, being <u>'Vanessa', 'Moulder', 'Ross'</u>.
* `char_list[:]` → Returns a <u>list</u> containing all of the items in the list, <u>'Eirika', 'Seth', 'Vanessa', 'Moulder', 'Ross', 'Garcia'</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* It must have valid indexes to work. By being a range structure, <u>not assigning values</u> counts as a valid value.
* The <u>end_index</u> value isn't the last index it will take to the list but the first index it will ignore, so it must be 1 number higher than the actual index it will stop at, even if that value goes beyond the number of items in the list.
* This structure will return a list even if it only finds a single element in the specified range.
* Setting the starting index to be greater or equal to the end index won't result in an error, however no list will be formed out of it.
</p></details>


------------

#### List Combining

``` python
ListA + ListB
```

Combines two lists into a larger list taking the set order.

<details><summary><strong>Examples</strong>:</summary><p>

``` python
erika_party = ['Eirika', 'Seth']
ephraim_party = ['Ephraim', 'Kyle', 'Forde']
```

* `eirika_party + ['Vanessa', 'Moulder']` → Adds <u>'Vanessa', 'Moulder'</u> to the end of <u>Eirika's Party</u> list, resulting in <u>'Eirika', 'Seth', 'Vanessa', 'Moulder'</u>.
* `['Orson'] + ephraim_party` → Adds <u>'Orson'</u> to the start of <u>Ephraim's Party</u> list, resulting in <u>'Orson', 'Ephraim', 'Kyle', 'Forde'</u>.
* `ephraim_party[0:1] + eirika_party[0:2]` → Adds the first index of <u>Ephraim's Party</u> to the start of <u>Eirika's Party</u> slice of the first two items, resulting in <u>'Ephraim', 'Eirika', 'Seth'</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* All values must be lists in order to combine them into a new list.
</p></details>

------------

### Lists Comprehensions

#### Base

``` python
[obj for obj in array_variable]
```

Builds a new list using an existing array, going through every item in the list provided.

------------

#### Property Filtering

``` python
[obj.prop for obj in array_variable]
```

Builds a new list taking a property value of an existing array items.

<details><summary><strong>Examples</strong>:</summary><p>

* `[un.name for un in game.level.units]` → Returns a list with the <u>names</u> of all units in the <u>level</u>.
* `[inv.nid for inv in u('Eirika').items]` → Returns a list with the <u>item NIDs</u> of all items in <u>Eirika</u>'s inventory.
* `["Skill_" + skl.nid for skl in u('Eirika').items]` → Returns a list with the <u>skill NIDs</u> of all skills that <u>Eirika</u> has, written in the format `Skill_`Skill NID ("Skill_Sol", "Skill_Luna", etc...).
</p></details>

------------

#### Conditional Filtering

``` python
[obj for obj in array_variable if <condition_statement>]
```

Builds a new list using an existing array containing items that match the condition criteria.

<details><summary><strong>Examples</strong>:</summary><p>

* `[un.name for un in game.level.units if un.team == 'other']` → Returns a list with the <u>names</u> of all <u>green units</u> in the <u>level</u>.
* `[inv.nid for inv in u('Eirika').items if inv.nid != 'Vulnerary']` → Returns a list with the <u>item NIDs</u> of all items in <u>Eirika</u>'s inventory that aren't a <u>Vulnerary</u>.
* `["Prepromo_" + un.name for un in game.level.units if 'Prepromo' in un.tags]` → Returns a list with all <u>units</u> in the <u>level</u> that have the <u>Prepromo</u> tag, written in the format `Prepromo_`Unit NID ("Prepromo_Seth", "Prepromo_Innes", etc...).
</p></details>

------------

#### Item Replacement

``` python
['new_item' if obj == 'old_item' else obj for obj in array_variable]
```

Builds a new list using replacing items that match the criteria with other items.

<details><summary><strong>Examples</strong>:</summary><p>

* `["Ephraim" if un.name == "Eirika" else un.name for un in game.level.units]` → Returns a list with the <u>names</u> of all <u>units</u> in the <u>level</u>, replacing <u>Eirika</u> with <u>Ephraim</u>.
* `['Sol' if skls.nid == 'Luna' else skls.nid for skls in u('Eirika').skills]` → Returns a list with the <u>skill NIDs</u> of all skills that <u>Eirika</u> has, replacing <u>Luna</u> with <u>Sol</u>.
</p></details><br/>

<details><summary><strong>Notes</strong>:</summary><p>

* If a list has duplicates, all of them will be replaced. While it is possible to replace a single duplicate in a list, it is process more complex that a syntax example can cover.
</p></details>
