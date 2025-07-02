from typing import Any, Dict, Tuple

from app.utilities.data import Data
from app.utilities.typing import NID

from app.dungeon_maker.themes import ThemeParameter

theme_parameters = Data(
    ThemeParameter('size', "Map Size", (30, 18), Tuple[int, int]),
)

theme_presets: Dict[str, Dict[NID, Any]] {
    "Default": {},
}

def get_default_theme() -> Dict[NID, Any]:
    new_theme = {}
    for parameter in theme_parameters:
        new_theme[parameter.nid] = parameter.value
    return new_theme

def get_theme(preset: NID) -> Dict[NID, Any]:
    """Given a theme preset's nid, return the theme
    parameters for it"""
    base_theme = get_theme("Default")
    theme_preset = theme_presets[preset]
    base_theme.update(theme_preset)
    return base_theme
