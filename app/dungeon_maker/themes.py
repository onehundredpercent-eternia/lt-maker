from typing import List, Tuple

class Theme:
    size: Tuple[int, int] = (30, 18)
    section_grid: Tuple[int, int] = (4, 2)
    room_chance: float = 0.6
    hallway_chance: float = 0.4
    wide_hallway_chance: float = 0.5
    use_forest: bool = False
    sparse_forest_chance: float = 0.15
    room_size_min_x: int = 3
    room_size_min_y: int = 3
    pillar_arrangements: List[str] = ["NoPillars", "NoPillars", "NoPillars", "OnEdge", "FourCorners", "NearEdge"]
    odd_only_pillar_arrangements: List[str] = ["Middle", "Middle"]
    even_only_pillar_arragements: List[str] = []
    small_floor_section_size: int = 2

class DefaultTheme(Theme):
    pass

class ForestTheme(Theme):
    use_forest: bool = True

themes = {
    'default': DefaultTheme,
    'forest': ForestTheme,
}
