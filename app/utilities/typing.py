from typing import Iterable, Tuple, TypeVar, Union, List

Pos = Tuple[int, int]

Point = Tuple[int, int]
Segment = Tuple[Point, Point]

NID = str
UID = int
Color3 = Tuple[int, int, int]
Color4 = Tuple[int, int, int, int]

NestedString = Union[str, List['NestedString']]
FloatPoint = Tuple[float, float]
Vector = Tuple[float, ...]

Primitive = Union[int, str, float, bool, None]
NestedPrimitiveDictElement = Union[Primitive, dict[str, 'NestedPrimitiveDictElement'], List[Primitive]]