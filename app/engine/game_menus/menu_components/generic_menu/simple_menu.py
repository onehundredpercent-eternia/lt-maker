from __future__ import annotations
from app.engine.graphics.ui_framework.premade_components.plain_text_component import PlainTextLine

from app.engine.base_surf import create_base_surf, create_highlight_surf

from typing import List, TYPE_CHECKING, Tuple

from app.engine.graphics.ui_framework import (HeaderList, IconRow,
                                            ListLayoutStyle, UIComponent,
                                            UILayoutType )
from app.engine import engine
from app.sprites import SPRITES

class SimpleIconTable(UIComponent):
    def __init__(self, name: str, parent: UIComponent = None,
                 initial_data: List[str] | List[Tuple[engine.Surface, str, str]] = [],
                 num_columns: int = 1, num_rows: int = 0, row_width: int = -1,
                 background = 'menu_bg_base', title: str = None):
        super().__init__(name=name, parent=parent)

        self.num_columns = max(num_columns, 1)
        self.num_rows = num_rows
        self._row_width = row_width
        self._data = None
        self._title = None
        self._background = background
        self.column_data: List[List[IconRow]] = [list() for _ in range(self.num_columns)]

        # subcomponents and layout
        self.props.layout = UILayoutType.LIST
        self.props.list_style = ListLayoutStyle.COLUMN
        self.overflow = (20, 20, 12, 12)

        if not title:
            self.header: PlainTextLine = None
        else:
            self.header: PlainTextLine = PlainTextLine('header', self, title)
            self.add_child(self.header)

        self.table_container = UIComponent("table_container", self)
        self.table_container.props.layout = UILayoutType.LIST
        self.table_container.props.list_style = ListLayoutStyle.ROW
        self.table_container.overflow = (20, 20, 12, 12)
        self.column_components: List[HeaderList] = [HeaderList('', self, None, []) for _ in range(self.num_columns)]
        for col in self.column_components:
            col.overflow = (20, 20, 0, 0)
            self.table_container.add_child(col)

        self.add_child(self.table_container)

        self.set_title(title)
        self.set_data(initial_data)

        self._reset('init')

    def construct_row(self, datum: str | Tuple[engine.Surface | UIComponent, str]
                                       | Tuple[engine.Surface | UIComponent, str, str]) -> IconRow:
        if isinstance(datum, tuple):
            icon = datum[0]
            text = datum[1]
            if len(datum) == 3: # includes nid
                nid = datum[2]
            else:
                nid = datum[1]
            row = IconRow(text, text=text, icon=icon, data=nid)
        else:
            row =  IconRow(datum, text=datum, data=datum)
        row.overflow = (15, 0, 15, 0)
        return row

    def set_title(self, title: str):
        if title == self._title:
            return
        self._title = title
        if self.header:
            self.header.set_text(self._title)

    def set_data(self, data: List):
        if data == self._data:
            return
        self._data = data
        self.column_data = [list() for _ in range(self.num_columns)]
        for idx, item in enumerate(data):
            row_item = self.construct_row(item)
            self.column_data[idx % self.num_columns].append(row_item)
        self._reset('set_data')
        for idx, col in enumerate(self.column_components):
            col.set_data_rows(self.column_data[idx])

    def _reset(self, reason: str):
        """Pre-draw, basically; take all known props, and recalculate one last time."""
        row_width, table_height = self._autosize(self._row_width, self.num_rows)
        for column in self.column_components:
            column.width = row_width

        self.table_container.size = (self.num_columns * row_width, table_height)
        total_height = table_height
        if self.header:
            total_height += self.header.height
        self.size = (self.num_columns * row_width, total_height)
        # regenerate bg
        if self._background:
            if 'menu_bg' in self._background:
                menu_bg = create_base_surf(self.tsize[0] + 10, self.tsize[1] + 10, self._background)
                self.set_background(menu_bg)
            else: # not actually a tileable base bg
                menu_bg = SPRITES.get(self._background)
                self.set_background(menu_bg)

    def _autosize(self, force_row_width = 0, force_num_rows = 0) -> Tuple[int, int]:
        max_row_width = 0
        if not force_row_width > 0:
            for col in self.column_data:
                for row in col:
                    max_row_width = max(row.text.twidth + row.icon.twidth, max_row_width)
            if self.header:
                max_row_width = max(self.header.twidth / self.num_columns, max_row_width)
        else:
            max_row_width = force_row_width

        table_height = 0
        if force_num_rows > 0:
            table_height = self.num_rows * 16
        else:
            table_height = self.max_rows_in_cols * 16

        return max_row_width, table_height

    @property
    def max_rows_in_cols(self):
        max_rows_in_col = 0
        for col in self.column_data:
            max_rows_in_col = max(len(col), max_rows_in_col)
        return max_rows_in_col

class ChoiceTable(SimpleIconTable):
    def __init__(self, name: str, parent: UIComponent = None,
                 initial_data: List[str] | List[Tuple[engine.Surface, str, str]] = [],
                 num_columns: int = 1, num_rows: int = -1, row_width: int = -1,
                 background='menu_bg_base', title: str = None):
        super().__init__(name, parent=parent, initial_data=initial_data,
                         num_columns=num_columns, num_rows=num_rows, row_width=row_width,
                         background=background, title=title)
        self.cursor_sprite = SPRITES.get('menu_hand')
        self.cursor_offsets = [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        self.cursor_offset_index = 0
        self.selected_index = (0, 0)
        self.draw_cursor = 1 # 0 is no cursor, 1 is yes, 2 is yes but no move

    def should_redraw(self) -> bool:
        return True

    def update_cursor_and_highlight(self):
        x, y = self.selected_index
        cy = (y - self.column_components[x].scrolled_index) * self.column_components[x].row_height + 3
        self.cursor_offset_index = (self.cursor_offset_index + 1) % len(self.cursor_offsets)
        if self.draw_cursor == 1:
            cx = -15 + self.cursor_offsets[self.cursor_offset_index]
        else:
            cx = -11
        self.column_components[x].add_surf(self.cursor_sprite, (cx, cy), 1)
        highlight_surf = create_highlight_surf(self.column_components[x].width)
        self.column_components[x].add_surf(highlight_surf, (0, cy + 3), -1)

    def move_down(self):
        if self.any_children_animating():
            return
        x, y = self.selected_index
        self.selected_index = (x, min(y + 1, len(self.column_data[x]) - 1))
        if self.selected_index[1] > self.column_components[x].max_visible_rows + self.column_components[x].scrolled_index - 1:
            for hl in self.column_components:
                hl.scroll_down()

    def move_up(self):
        if self.any_children_animating():
            return
        x, y = self.selected_index
        self.selected_index = (x, max(y - 1, 0))
        if self.selected_index[1] < self.column_components[x].scrolled_index:
            for hl in self.column_components:
                hl.scroll_up()

    def move_left(self):
        x, y = self.selected_index
        new_col = max(x - 1, 0)
        self.selected_index = (new_col, min(y, len(self.column_data[new_col]) - 1))

    def move_right(self):
        x, y = self.selected_index
        new_col = min(x + 1, len(self.column_data) - 1)
        self.selected_index = (new_col, min(y, len(self.column_data[new_col]) - 1))

    def get_selected(self):
        x, y = self.selected_index
        return self.column_data[x][y].data

    def set_draw_cursor(self, should_draw_cursor):
        self.draw_cursor = should_draw_cursor

    def to_surf(self, no_cull=False, should_not_cull_on_redraw=True) -> engine.Surface:
        if self.draw_cursor != 0:
            for hl in self.column_components:
                if hl.manual_surfaces:
                    hl.manual_surfaces.clear()
            self.update_cursor_and_highlight()
        return super().to_surf(no_cull, should_not_cull_on_redraw)
