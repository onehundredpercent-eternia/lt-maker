from __future__ import annotations
from app.engine.game_menus.menu_components.generic_menu.simple_menu_wrapper import SimpleMenuUI

from typing import Callable, List, Tuple

from app.engine.game_menus.menu_components.generic_menu.simple_menu import \
    ChoiceTable
from app.engine.game_state import game
from app.engine.graphics.ui_framework.ui_framework import UIComponent
from app.engine.graphics.ui_framework.ui_framework_layout import convert_align
from app.engine.icons import get_icon, get_icon_by_nid
from app.engine.objects.unit import UnitObject
from app.utilities.enums import Alignments
from app.utilities.typing import NID


class ChoiceMenuUI(SimpleMenuUI):
    def __init__(self, data: List[str] | Callable[[], List] = None, data_type: str = 'str',
                 title: str = None, rows: int = 0, cols: int = 1, row_width: int = -1,
                 alignment: Alignments = Alignments.CENTER, bg: str = 'menu_bg_base'):
        # set in super constructor
        self.table: ChoiceTable = None
        super().__init__(data=data, data_type=data_type,
                         title=title, rows=rows, cols=cols,
                         row_width=row_width, alignment=alignment, bg=bg)

    def create_table(self, base_component, rows, cols, title, row_width, bg) -> ChoiceTable:
        return ChoiceTable('table', base_component, num_rows=rows, num_columns=cols, title=title, row_width=row_width, background=bg)

    def get_selected(self):
        return self.table.get_selected()

    def move_up(self):
        self.table.move_up()

    def move_down(self):
        self.table.move_down()

    def move_right(self):
        self.table.move_right()

    def move_left(self):
        self.table.move_left()

    def draw(self, surf, should_draw_cursor = 1): # should_draw_cursor allows us to stop updating the cursor
        self.table.set_draw_cursor(should_draw_cursor)
        ui_surf = self.base_component.to_surf()
        surf.blit(ui_surf, (0, 0))
        return surf
