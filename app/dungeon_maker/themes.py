from typing import Any, Dict, Tuple, Type

from dataclasses import dataclass
from enum import StrEnum

from app.utilities.data import Data
from app.utilities.typing import NID

from app.map_maker.terrain import Terrain

class PillarArrangement(StrEnum):
    NoPillars = "NoPillars"
    Middle = "Middle"
    OnEdge = "OnEdge"
    FourCorners = "FourCorners"
    NearEdge = "NearEdge"

@dataclass
class ThemeParameter:
    nid: NID
    name: str
    value: Any
    _type: Type
    desc: str = ""

theme_parameters = Data(
    ThemeParameter('size', "Map Size", (30, 18), Tuple[int, int]),
    ThemeParameter('section_grid', "Section Grid", (30, 18), Tuple[int, int], "Individual sections to fill with rooms"),
    ThemeParameter('room_chance', "Room Chance", 0.6, float, "Chance of a full size room in a section"),
    ThemeParameter('hallway_chance', "Hallway Chance", 0.4, float, "Chance of hallway (instead of a room) in a section"),
    ThemeParameter('connection_chance', "Connection Chance", 1.0, float, "Chance that adjacent rooms connect"),
    ThemeParameter('wise_hallway_chance', "Wide Hallway Chance", 0.5, float, "Chance that a given hallway is 2-wide"),
    ThemeParameter('floor_lower_chance', "Lower Floor Chance", 0.5, float, "Chance that a room is on the lower floor"),
    ThemeParameter('use_water_chance', "Pool Chance", 0, float, "Chance to use pool and pool bridge on lower floor"),
    ThemeParameter('room_size_min_x', "Minimum Width of Room", 3, int),
    ThemeParameter('room_size_min_y', "Mimumum Height of Room", 3, int),
    ThemeParameter('small_floor_section_size', "Minimum Size of Floor", 2, int, "Swap any areas of floor smaller than this to the other floor"),
    ThemeParameter('pillar_chance', "Pillar Chance", 0.5, float, "Chance that any room has pillars"),
    ThemeParameter('horiz_symmetry', "Horizontally Symmetric", bool, False),
    ThemeParameter('vert_symmetry', "Vertically Symmetric", bool, False),
    ThemeParameter('fill_in_empty_areas', "Fill in Empty Areas", bool, False, "Attempt to fill large areas of void with floor?"),
    ThemeParameter('use_global_section', "Fill Outside", bool, False, "Fill the outside of the map with lower floor"),
    ThemeParameter('convert_void_to_water', "Void -> Pool", bool, False, "Convert all void to pool terrain"),
    ThemeParameter('floor_upper', "Upper Floor Terrain", Terrain, Terrain.FLOOR_1, "Which terrain to use for the upper floor"),
    ThemeParameter('floor_lower', "Lower Floor Terrain", Terrain, Terrain.FLOOR_2, "Which terrain to use for the lower floor"),
)

themes: Dict[str, Dict[NID, Any]] = {
    "Default": {},
    "Labyrinth": {
        "size": (21, 25),
        "section_grid": (4, 6),
        "room_chance": 1.0,
        "hallway_chance": 0.0,
        "wide_hallway_chance": 0.0,
        "floor_lower_chance": 0.2,
        "room_size_min_x": 2,
        "room_size_min_y": 2,
        "pillar_chance": 0.33,
        "horiz_symmetry": True,
    },
    "Winding Hallways": {
        "size": (27, 27),
        "section_grid": (4, 4),
        "room_chance": 0.5,
        "hallway_chance": 0.5,
        "connection_chance": 0.8,
        "wide_hallway_chance": 1.0,
        "floor_lower_chance": 0.25,
        "pillar_chance": 0.5,
        "small_floor_section_size": 5,
        "fill_in_empty_areas": True,
    },
}

def get_theme() -> Dict[NID, Any]:
    new_theme = {}
    for parameter in theme_parameters:
        new_theme[parameter.nid] = parameter.value
    return new_theme

# class ThemeParameters:
#     size: Tuple[int, int] = (30, 18)
#     section_grid: Tuple[int, int] = (4, 2)
#     room_chance: float = 0.6
#     hallway_chance: float = 0.4  # Chance of single node room
#     connection_chance: float = 1.0  # Chance to connect adjacent rooms together
#     wide_hallway_chance: float = 0.5  # Chance of wide hallway
#     floor_lower_chance = 0.5  # Chance that a room is on the lower floor versus the upper floor
#     use_forest: bool = False
#     use_water_chance: float = 0  # Use water and waterbridges on lower floor
#     sparse_forest_chance: float = 0.15  # Chance that any lower floor position has a tree
#     room_size_min_x: int = 3
#     room_size_min_y: int = 3
#     pillar_chance: float = 0.5  # Chance that any room has pillars
#     pillar_arrangements: List[str] = ["OnEdge", "FourCorners", "NearEdge"]
#     odd_only_pillar_arrangements: List[str] = ["Middle", "Middle"]
#     even_only_pillar_arrangements: List[str] = []
#     small_floor_section_area: int = 2  # A section of flooring that is this area or smaller, will swap to other level
#     horiz_symmetry: bool = False
#     vert_symmetry: bool = False
#     fill_in_empty_areas: bool = False
#     use_global_section: bool = False
#     convert_void_to_water: bool = False

# class WindingHallwaysTheme(Theme):
#     size: Tuple[int, int] = (27, 27)
#     section_grid: Tuple[int, int] = (4, 4)
#     room_chance: float = 0.5
#     hallway_chance: float = 0.5
#     connection_chance: float = 0.8
#     wide_hallway_chance: float = 1.0
#     floor_lower_chance = 0.25
#     use_forest: bool = True
#     sparse_forest_chance: float = 0.25  # Chance that any lower floor position has a tree
#     pillar_chance: float = 0.5  # Chance that any room has pillars
#     small_floor_section_size: int = 5
#     fill_in_empty_areas: bool = True

# class ComplexTheme(Theme):
#     size: Tuple[int, int] = (26, 36)
#     section_grid: Tuple[int, int] = (5, 6)
#     room_chance: float = 0.45
#     hallway_chance: float = 0  # Chance of single node room
#     connection_chance: float = 0.8  # Chance to connect adjacent rooms together
#     floor_lower_chance: float = 0
#     use_forest: bool = True
#     sparse_forest_chance: float = 0.25  # Chance that any lower floor position has a tree
#     room_size_min_x: int = 3
#     room_size_min_y: int = 2
#     pillar_chance: float = 0.25  # Chance that any room has pillars
#     use_global_section: bool = True

# class SewersTheme(Theme):
#     size: Tuple[int, int] = (25, 25)
#     section_grid: Tuple[int, int] = (4, 4)
#     room_chance: float = 0.55
#     hallway_chance: float = 0.45  # Chance of single node room
#     connection_chance: float = 0.8  # Chance to connect adjacent rooms together
#     wide_hallway_chance: float = 1.0  # Chance of wide hallway
#     floor_lower_chance: float = 0.75
#     use_water_chance: float = 0.5
#     room_size_min_x: int = 3
#     room_size_min_y: int = 2
#     pillar_chance: float = 0.5  # Chance that any room has pillars

# class EntranceTheme(Theme):
#     size: Tuple[int, int] = (25, 15)
#     section_grid: Tuple[int, int] = (4, 3)
#     room_chance: float = 0.5
#     hallway_chance: float = 0.4  # Chance of single node room
#     connection_chance: float = 0.5  # Chance to connect adjacent rooms together
#     use_forest: bool = True
#     pillar_chance: float = 0.25  # Chance that any room has pillars
#     small_floor_section_area: int = 4  # A section of flooring that is this area or smaller, will swap to other level
#     convert_void_to_water: bool = True

# class CastleTheme(Theme):
#     size: Tuple[int, int] = (20, 30)
#     section_grid: Tuple[int, int] = (4, 4)
#     room_chance: float = 0.6
#     hallway_chance: float = 0.4  # Chance of single node room
#     connection_chance: float = 0.75  # Chance to connect adjacent rooms together
#     wide_hallway_chance: float = 1.0  # Chance of wide hallway
#     room_size_min_x: int = 3
#     room_size_min_y: int = 4
#     pillar_chance: float = 0.4  # Chance that any room has pillars
#     small_floor_section_area: int = 4  # A section of flooring that is this area or smaller, will swap to other level
#     fill_in_empty_areas: bool = True

# themes = {
#     'default': DefaultTheme,
#     'forest': ForestTheme,
#     'labyrinth': LabyrinthTheme,
#     'winding': WindingHallwaysTheme,
#     'complex': ComplexTheme,
#     'sewers': SewersTheme,
#     'entrance': EntranceTheme,
#     'castle': CastleTheme,
# }
