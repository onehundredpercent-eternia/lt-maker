from typing import List, Tuple

class Theme:
    size: Tuple[int, int] = (30, 18)
    section_grid: Tuple[int, int] = (4, 2)
    room_chance: float = 0.6
    hallway_chance: float = 0.4  # Chance of single node room
    connection_chance: float = 1.0  # Chance to connect adjacent rooms together
    wide_hallway_chance: float = 0.5  # Chance of wide hallway
    floor_lower_chance = 0.5
    use_forest: bool = False
    use_water_chance: float = 0
    sparse_forest_chance: float = 0.15  # Chance that any lower floor position has a tree
    room_size_min_x: int = 3
    room_size_min_y: int = 3
    pillar_chance: float = 0.5  # Chance that any room has pillars
    pillar_arrangements: List[str] = ["OnEdge", "FourCorners", "NearEdge"]
    odd_only_pillar_arrangements: List[str] = ["Middle", "Middle"]
    even_only_pillar_arragements: List[str] = []
    small_floor_section_area: int = 2  # A section of flooring that is this area or smaller, will swap to other level
    horiz_symmetry: bool = False
    vert_symmetry: bool = False
    fill_in_empty_areas: bool = False
    use_global_section: bool = False

class DefaultTheme(Theme):
    pass

class ForestTheme(Theme):
    use_forest: bool = True

class LabyrinthTheme(Theme):
    size: Tuple[int, int] = (21, 25)
    section_grid: Tuple[int, int] = (4, 6)
    room_chance: float = 1.0
    hallway_chance: float = 0.0
    wide_hallway_chance: float = 0.0
    floor_lower_chance = 0.2
    use_forest: bool = True
    room_size_min_x: int = 2
    room_size_min_y: int = 2
    pillar_chance: float = 0.33
    horiz_symmetry: bool = True

class WindingHallwaysTheme(Theme):
    size: Tuple[int, int] = (27, 27)
    section_grid: Tuple[int, int] = (4, 4)
    room_chance: float = 0.5
    hallway_chance: float = 0.5
    connection_chance: float = 0.8
    wide_hallway_chance: float = 1.0
    floor_lower_chance = 0.25
    use_forest: bool = True
    sparse_forest_chance: float = 0.25  # Chance that any lower floor position has a tree
    pillar_chance: float = 0.5  # Chance that any room has pillars
    small_floor_section_size: int = 5
    fill_in_empty_areas: bool = True

class ComplexTheme(Theme):
    size: Tuple[int, int] = (26, 36)
    section_grid: Tuple[int, int] = (5, 6)
    room_chance: float = 0.45
    hallway_chance: float = 0  # Chance of single node room
    connection_chance: float = 0.8  # Chance to connect adjacent rooms together
    floor_lower_chance: float = 0
    use_forest: bool = True
    sparse_forest_chance: float = 0.25  # Chance that any lower floor position has a tree
    room_size_min_x: int = 3
    room_size_min_y: int = 2
    pillar_chance: float = 0.25  # Chance that any room has pillars
    use_global_section: bool = True

class SewersTheme(Theme):
    size: Tuple[int, int] = (25, 25)
    section_grid: Tuple[int, int] = (4, 4)
    room_chance: float = 0.55
    hallway_chance: float = 0.45  # Chance of single node room
    connection_chance: float = 0.8  # Chance to connect adjacent rooms together
    wide_hallway_chance: float = 1.0  # Chance of wide hallway
    floor_lower_chance: float = 0.75
    use_water_chance: float = 0.5
    room_size_min_x: int = 3
    room_size_min_y: int = 2
    pillar_chance: float = 0.5  # Chance that any room has pillars


themes = {
    'default': DefaultTheme,
    'forest': ForestTheme,
    'labyrinth': LabyrinthTheme,
    'winding': WindingHallwaysTheme,
    'complex': ComplexTheme,
    'sewers': SewersTheme,
}
