# Region Object

## Properties

|Property|Type|Role/expected value
|--|--|--
|`nid`|str|-
|`region_type`|str|`normal`, `status`, `event` or `formation`.
|`position`|tuple[int, int]|Topleft position coordinate.
|`size`|tuple[int, int]|-
|`sub_nid`|str|-
|`condition`|str|Valid `python` expression.
|`only_once`|bool|-
|`interrupt_move`|bool|-
|`area`|int|-
|`center`|tuple[int, int]|-

---------------------

## Functions

### Contains
``` Text
[RegionObject].contains(tuple[int, int])
  -> 'bool'
```

Checks if a coordinate is inside the region area.

---------------------

### Get All Positions

``` Text
[RegionObject].get_all_positions()
  -> 'list[tuple[int, int]]'
```

Returns all coordinates inside the region area.
