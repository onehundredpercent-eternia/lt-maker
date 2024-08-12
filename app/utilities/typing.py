from typing import Dict, List, Tuple, Union

Pos = Tuple[int, int]

Point = Tuple[int, int]
Segment = Tuple[Point, Point]

NID = str
UID = int
Color3 = Tuple[int, int, int]
Color4 = Tuple[int, int, int, int]

Primitive = Union[int, str, float, bool, None]
NestedPrimitiveDict = Dict[str, Union[Primitive, 'NestedPrimitiveDict']]