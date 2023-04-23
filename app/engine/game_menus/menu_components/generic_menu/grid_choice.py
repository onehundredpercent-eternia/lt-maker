from __future__ import annotations
from typing import Any, List, Optional, Tuple, Type
from app.constants import WINHEIGHT, WINWIDTH
from app.editor.lib.math.math_utils import float_eq
from app.engine.base_surf import create_base_surf
from app.engine.game_menus.menu_components.generic_menu.cursor_hand import CursorDrawMode, CursorHand
from app.engine.game_menus.menu_components.generic_menu.menu_options import BasicOption, IMenuOption
from app.engine.graphics.text.text_renderer import font_height, render_text, text_width
from app.engine.graphics.ui_framework.ui_framework_layout import HAlignment, VAlignment, convert_align
from app.engine import engine

from app.utilities.enums import Alignments, Orientation
from app.utilities.typing import NID
from app.utilities.utils import clamp, sign

class LayoutManager():
  @staticmethod
  def align_to_screen_position(alignment: Alignments, margin: int, size: Tuple[int, int], window_size: Tuple[int, int] = (WINWIDTH, WINHEIGHT)) -> Tuple[int, int]:
    halign, valign = convert_align(alignment)
    x, y = 0, 0
    sw, sh = size
    screen_w, screen_h = window_size
    if halign is HAlignment.LEFT:
      x = margin
    elif halign is HAlignment.RIGHT:
      x = screen_w - sw - margin
    else:
      x = screen_w // 2 - sw // 2

    if valign is VAlignment.TOP:
      y = margin
    elif valign is VAlignment.BOTTOM:
      y = screen_h - sh - margin
    else:
      y = screen_h // 2 - sh // 2

    return x, y

class GridChoiceMenu():
  def __init__(self, data: List, display_values: Optional[List]=None, title: Optional[str]=None, data_type: str = "text",
               size: Optional[Tuple[int, int]] = None, row_width: int=0, alignment: Alignments | Tuple[int, int]=Alignments.CENTER,
               orientation: Orientation = Orientation.VERTICAL,
               bg: NID='menu_bg_base', text_align: HAlignment=HAlignment.LEFT) -> None:
    self._should_autosize = not bool(size)
    self._grid_size: Tuple[int, int] = size or self._autosize_grid(data)
    self._data_type: str = data_type
    self._row_width: int = row_width
    self._title: Optional[str] = title
    self._bg_name = bg
    self._orientation: Orientation = orientation
    self._alignment: Alignments | Tuple[int, int] = alignment

    self._option_data = self._build_data(data, display_values, self._data_type, self._row_width)
    self._item_size = self._determine_item_size(self._option_data, self._row_width)

    self._cursor_idx: int = 0

    self._scroll: Tuple[float, float] = (0, 0)
    self._scroll_to: Tuple[float, float] = (0, 0)

    self._cached_bg: engine.Surface = self._build_bg()
    self._cached_data_surf: engine.Surface = self._build_data_surf()

    self.cursor_hand = CursorHand()

  def set_data(self, data: List, display_values: Optional[List] = None):
    selected_idx = self.get_selected_idx()
    if self._should_autosize:
      self._grid_size: Tuple[int, int] = self._autosize_grid(data)
    self._option_data = self._build_data(data, display_values, self._data_type, self._row_width)
    self._item_size = self._determine_item_size(self._option_data, self._row_width)
    self._cached_bg: engine.Surface = self._build_bg()
    self._cached_data_surf: engine.Surface = self._build_data_surf()
    self.move_cursor(selected_idx)

  def set_cursor_mode(self, draw_mode: CursorDrawMode):
    self.cursor_hand.mode = draw_mode

  def move_right(self, first_push: bool = False):
    if first_push:
      next_idx = (self._cursor_idx + 1) % len(self._option_data)
    else:
      next_idx = min(self._cursor_idx + 1, len(self._option_data) - 1)
    self.move_cursor(next_idx)

  def move_left(self, first_push: bool = False):
    if first_push:
      next_idx = (self._cursor_idx - 1) % len(self._option_data)
    else:
      next_idx = max(0, self._cursor_idx - 1)
    self.move_cursor(next_idx)

  def move_up(self, first_push: bool = False):
    num_cols, num_rows = self._total_grid_size()
    if first_push:
      next_idx = self._cursor_idx - num_cols
      if next_idx < 0:
        next_idx += num_cols * num_rows
      while(next_idx >= len(self._option_data)):
        next_idx -= num_cols
    else:
      next_idx = self._cursor_idx - num_cols
      if next_idx < 0:
        return
    self.move_cursor(next_idx)

  def move_down(self, first_push: bool = False):
    num_cols = self._total_grid_size()[0]
    next_idx = self._cursor_idx + num_cols
    if next_idx >= len(self._option_data):
      if first_push:
        next_idx = next_idx % num_cols
      else:
        return
    self.move_cursor(next_idx)

  def move_cursor(self, idx):
    idx = clamp(idx, 0, len(self._option_data) - 1)
    self._cursor_idx = idx
    as_coord = self._get_coord_of_option_idx(idx)
    scroll_to = self._identify_minimum_scroll_to_loc(tuple(map(int, self._scroll)), tuple(map(float, as_coord)))
    self.scroll_to(scroll_to)

  def scroll_to(self, coord: Tuple[float, float]):
    self._scroll_to = coord

  def _total_grid_size(self) -> Tuple[int, int]:
    if self._orientation == Orientation.VERTICAL:
      # constraint on num_cols
      num_cols = self._grid_size[0]
      return num_cols, (len(self._option_data) // num_cols) + 1
    else:
      # constraint on num_rols
      num_rows = self._grid_size[1]
      return (len(self._option_data) // num_rows) + 1, num_rows

  def _get_index_of_coord(self, coord: Tuple[int, int]) -> int:
    nx, _ = self._total_grid_size()
    x, y = coord
    return x + y * nx

  def _get_coord_of_option_idx(self, idx: int) -> Tuple[int, int]:
    x, _ = self._total_grid_size()
    return idx % x, idx // x

  def _get_pixel_coord_of_coord(self, coord: Tuple[float, float]) -> Tuple[int, int]:
    iw, ih = self._item_size
    x, y = coord
    return int(x * iw), int(y * ih)

  def _get_pixel_size(self) -> Tuple[int, int]:
    title_width, title_height = 0, 0
    if self._title:
      title_width, title_height = text_width('text', self._title), font_height('text')
    num_horiz_options, num_vert_options = self._grid_size
    item_width, item_height = self._item_size
    total_height = num_vert_options * item_height + title_height
    total_width = max(num_horiz_options * item_width, title_width)
    return total_width, total_height

  def _get_screen_position(self) -> Tuple[int, int]:
    if isinstance(self._alignment, Alignments):
      return LayoutManager.align_to_screen_position(self._alignment, 10, self._get_pixel_size())
    return self._alignment

  def get_selected_idx(self) -> int:
    if self._cursor_idx < len(self._option_data):
      return self._cursor_idx
    raise ValueError("Cursor at invalid index")

  def get_selected(self) -> Any:
    if self._cursor_idx < len(self._option_data):
      return self._option_data[self._cursor_idx].get()
    raise ValueError("Cursor at invalid index")

  def _autosize_grid(self, data: List[Any]):
    return (1, min(len(data), 1))

  def _resolve_data_type(self, data_type: str):
    return BasicOption

  def _build_bg(self) -> engine.Surface:
    tw, th = self._get_pixel_size()
    bg_surf = create_base_surf(tw, th + 8, self._bg_name)
    return bg_surf

  def _build_data(self, data: List[Any], display_values: Optional[List[Any]], data_type: str, row_width: int) -> List[IMenuOption]:
    display_values = display_values or data
    options: List[IMenuOption] = []
    for i in range(len(data)):
      value = data[i]
      disp_value = display_values[i]
      if data_type == 'text':
        if row_width:
          options.append(BasicOption(i, value, disp_value, row_width))
        else:
          options.append(BasicOption(i, value, disp_value))
      else:
        raise TypeError("Unknown Option Type")
    return options

  def _build_data_surf(self) -> engine.Surface:
    x, y = self._total_grid_size()
    iwidth, iheight = self._item_size
    width = x * iwidth
    height = y * iheight
    blank_surf = engine.create_surface((width, height), True)
    ox, oy = 0, 0
    for option in self._option_data:
      option.draw(blank_surf, ox, oy)
      ox += iwidth
      if ox == width:
        oy += iheight
        ox = 0
    return blank_surf

  def _determine_item_size(self, option_data: List[IMenuOption], row_width: int) -> Tuple[int, int]:
    if not option_data:
      # arbitrarily chosen as a typical field size
      return 80, 16
    max_height = 16
    max_width = 0
    for option in option_data:
      max_width = max(max_width, option.width())
      max_height = max(max_height, option.height())
    return row_width or max_width, max_height

  def _identify_minimum_scroll_to_loc(self, scroll: Tuple[float, float], loc: Tuple[float, float]) -> Tuple[float, float]:
    """Identifies the scroll location that allows loc to be visible with a minimum of net movement.
    """
    x, y = self._grid_size
    sx, sy = scroll
    lb, rb = sx, sx + x
    ub, db = sy, sy + y
    nx, ny = loc

    fx, fy = scroll
    if nx < lb:
      fx = nx
    elif nx >= rb:
      fx = nx - x + 1

    if ny < ub:
      fy = ny
    elif ny >= db:
      fy = ny - y + 1
    return fx, fy

  def _handle_scrolling(self):
    EPSILON = 0.2
    sx, sy = self._scroll
    goal_sx, goal_sy = self._scroll_to
    if not float_eq(sx, goal_sx, EPSILON):
      sx += EPSILON * sign(goal_sx - sx)
    else:
      sx = goal_sx

    if not float_eq(sy, goal_sy, EPSILON):
      sy += EPSILON * sign(goal_sy - sy)
    else:
      sy = goal_sy

    self._scroll = sx, sy

  def update(self):
    # handle cursor
    self.cursor_hand.update()
    # handle scrolling
    self._handle_scrolling()

  def _draw_data(self) -> engine.Surface:
    data_surf = engine.copy_surface(self._cached_data_surf)
    cursor_coord = self._get_coord_of_option_idx(self._cursor_idx)
    option_x, option_y = self._get_pixel_coord_of_coord(cursor_coord)
    option = self._option_data[self._cursor_idx]
    iw, ih = self._item_size
    option.draw_highlight(data_surf, option_x, option_y, iw)
    offset_x, offset_y = self._get_pixel_coord_of_coord(self._scroll)
    gx, gy = self._grid_size
    gridw, gridh = iw * gx, ih * gy
    return engine.subsurface(data_surf, (offset_x, offset_y, gridw, gridh))

  def _draw_cursor(self, surf, options_top_left) -> engine.Surface:
    selected_idx = self.get_selected_idx()
    sel_x, sel_y = self._get_coord_of_option_idx(selected_idx)
    scroll_x, scroll_y = self._scroll
    offset_coord = sel_x - scroll_x, sel_y - scroll_y
    px, py = self._get_pixel_coord_of_coord(offset_coord)
    bw, bh = self._get_pixel_size()
    # minor adjustments for visuals
    ox, oy = options_top_left
    if py < 0 or py > bh - (16 if self._title else 0):
      return
    if px < 0 or px > bw:
      return
    px = px + ox - 13
    py = py + oy + 3
    return self.cursor_hand.draw(surf, (px, py))

  def draw(self, surf) -> engine.Surface:
    # copy bg
    base = engine.copy_surface(self._cached_bg)
    # draw title and options
    options_surf = self._draw_data()
    options_y = 3
    if self._title:
      render_text(base, ['text'], [self._title], [None], (5, options_y))
      options_y += 16
    engine.blit(base, options_surf, (0, options_y))
    # draw arrows/scroll bar
    # TODO
    # draw moving cursor
    # copy onto screen
    left, top = self._get_screen_position()
    engine.blit(surf, base, (left, top))
    self._draw_cursor(surf, (left, top + options_y))
    return surf