"""Color-conversion tables for building map sprites.

Framework-agnostic (no pygame, no Qt) so both the engine renderer
(`app/engine/building_sprite.py`) and the editor's map view can build the same
table and stay in sync.

A building sprite is authored in one reference ramp, stored as a combat palette
under `REFERENCE_PALETTE_NID`: the colorkey, then `NUM_MAP_COLORS` map colors,
then `NUM_TEAM_COLORS` team colors, 16 entries in all. Of its non-colorkey colors:

* the first `NUM_MAP_COLORS` vary with the tilemap's building style
  (`TileMapPrefab.building_style_nid` -> another combat palette), and
* the last `NUM_TEAM_COLORS` vary with the owning team
  (`Team.building_color_primary` / `building_color_secondary`).
"""

import logging
from typing import Dict, List, Optional

from app.constants import COLORKEY
from app.utilities.typing import Color3, NID

REFERENCE_PALETTE_NID = 'building_ref'
NUM_MAP_COLORS = 13
NUM_TEAM_COLORS = 2
# What `palette_colors` should return for the reference ramp: everything but the colorkey
NUM_REFERENCE_COLORS = NUM_MAP_COLORS + NUM_TEAM_COLORS


def palette_colors(palette_nid: Optional[NID]) -> List[Color3]:
    """The colors of a combat palette, in order, with the colorkey dropped."""
    from app.data.resources.resources import RESOURCES
    palette = RESOURCES.combat_palettes.get(palette_nid)
    if not palette:
        return []
    return [color for color in palette.get_colors() if tuple(color) != tuple(COLORKEY)]


def get_conversion_dict(style_nid: Optional[NID], team_nid: Optional[NID]) -> Dict[Color3, Color3]:
    """Maps every reference ramp color onto the color it should be drawn as.

    Missing style colors and missing team colors each fall through to the
    reference color, so a half-configured project draws in the reference ramp
    rather than crashing or drawing transparent.
    """
    from app.data.database.database import DB

    reference = palette_colors(REFERENCE_PALETTE_NID)
    if not reference:
        return {}
    if len(reference) != NUM_REFERENCE_COLORS:
        # Too short and the team colors land on the wrong entries, or go missing
        logging.error("Building reference palette %s has %d colors, expected %d "
                      "(the colorkey, %d map colors, then %d team colors)",
                      REFERENCE_PALETTE_NID, len(reference), NUM_REFERENCE_COLORS,
                      NUM_MAP_COLORS, NUM_TEAM_COLORS)

    conversion: Dict[Color3, Color3] = {}

    style = palette_colors(style_nid)
    for idx, ref_color in enumerate(reference[:NUM_MAP_COLORS]):
        if idx < len(style):
            conversion[tuple(ref_color)] = tuple(style[idx])

    team = DB.teams.get(team_nid)
    if team:
        team_colors = [team.building_color_primary, team.building_color_secondary]
        team_refs = reference[NUM_MAP_COLORS:NUM_MAP_COLORS + NUM_TEAM_COLORS]
        for ref_color, team_color in zip(team_refs, team_colors):
            if team_color:
                conversion[tuple(ref_color)] = tuple(team_color)

    return conversion
