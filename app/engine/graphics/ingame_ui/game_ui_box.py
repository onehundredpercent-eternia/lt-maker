from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.constants import TILEHEIGHT, TILEWIDTH
from app.engine import engine
from app.engine.game_state import game
from app.engine.graphics.ingame_ui.ui_components import draw_component_surf
from app.engine.interfaces.idrawable import IDrawable
from app.engine.objects.ui_object import UIObject
from app.utilities import utils

class UIBox(IDrawable):
    """Implements event drawing interface so that these can be used in events
    """

    def __init__(self, positions: List[Tuple[int, int]], ui_object: UIObject, local_args: Dict[str, Any] = None):
        self.positions = positions
        self.ui_object = ui_object
        self.local_args = local_args
        self.cached_surf: engine.Surface = None

    def redraw_surf(self):
        self.cached_surf = draw_component_surf(self.ui_object, local_args=self.local_args, log_errors=self.ui_object.log_errors)

    def update(self):
        self.redraw_surf()
        return True

    def position_ui_box(self):
        if len(self.positions) == 1:
            return self.positions[0]
        # if many positions are available, draw the box furthest from the cursor
        try:
            if game.cursor.visible and game.cursor.position:
                cursor_pos = game.cursor.position[0] * TILEWIDTH, game.cursor.position[1] * TILEHEIGHT
                max_dist = 0
                max_position = self.positions[0]
                for position in self.positions:
                    dist = utils.distance(position, cursor_pos)
                    if dist > max_dist:
                        max_dist = dist
                        max_position = position
                return max_position
        except:
            return self.positions[0]

    def draw(self, surf: engine.Surface):
        if not self.cached_surf:
            self.redraw_surf()
        surf.blit(self.cached_surf, self.position_ui_box())
        return surf
