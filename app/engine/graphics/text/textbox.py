from __future__ import annotations
from functools import lru_cache

from typing import Callable, Tuple

from app.engine import engine, text_funcs
from app.engine.base_surf import create_base_surf
from app.engine.graphics.text.text_renderer import font_height, render_text, rendered_text_width
from app.engine.graphics.ui_framework.utils import calc_align_position
from app.sprites import SPRITES
from app.utilities.enums import Alignments


class TextBox():
    padding = 2
    def __init__(self, name: str, text: Callable[[], str] | str, num_lines: int = 1, width: int = 0,
                 menu_bg: str = 'menu_bg_base', font: str = 'text', alignment: Alignments | Tuple[int, int] = None) -> None:
        self.name = name
        self.width = width
        self.font = font
        self.num_lines = num_lines
        self.text = text

        self.size = self._determine_size(self.width, self.num_lines, self.font, self.text)
        self.alignment = alignment

        self._cached_bg = self._render_bg(menu_bg, self.size)
        self._cached_text = self._render_text(self.font, text, self.size)

    @lru_cache(5)
    def _determine_position(self, size: Tuple[int, int], frame_size: Tuple[int, int], alignment: Tuple[int, int] | Alignments) -> Tuple[int, int]:
        if isinstance(alignment, tuple):
            return alignment
        # is alignment
        return calc_align_position(alignment, size, frame_size)

    def _determine_size(self, width, num_lines, font, text):
        dheight, dwidth = 0, 0
        if width == 0 and num_lines == 0: # customize both? preposterous
            num_lines = 1

        if width == 0:
            total_len = rendered_text_width([font], [text])
            # give a little padding
            len_per_line = total_len // num_lines
            dwidth = len_per_line
        else:
            dwidth = width

        if num_lines == 0:
            total_len = rendered_text_width([font], [text])
            num_lines = total_len // width
        else:
            dheight = num_lines * font_height(font)

        # round to nearest
        dwidth += 8 - (dwidth) % 8

        return dwidth, dheight

    def _render_bg(self, bg_name: str, size: Tuple[int, int]) -> engine.Surface:
        width, height = size
        padded_width, padded_height = width + self.padding * 2, height + self.padding * 4
        if 'menu_bg' in bg_name: # bg base
            return create_base_surf(padded_width, padded_height, bg_name)
        else: # normal sprite
            base_surf = engine.create_surface((padded_width, padded_height), True)
            sprite = SPRITES.get(bg_name)
            if not sprite:
                return base_surf
            x = (padded_width - sprite.get_width()) // 2
            y = (padded_height - sprite.get_height()) // 2
            engine.blit_center(base_surf, sprite, (x, y))
            return base_surf

    def _render_text(self, font: str, text: str, size: Tuple[int, int]) -> engine.Surface:
        width, _ = size
        lines = text_funcs.line_wrap(font, text, width)
        line_num = 0
        base_surf = engine.create_surface(size, True)
        for line in lines:
            y = line_num * font_height(font)
            render_text(base_surf, [font], [line], topleft=(0, y))
            line_num += 1
        return base_surf

    def _get_surf(self) -> engine.Surface:
        bg_surf = engine.copy_surface(self._cached_bg)
        engine.blit(bg_surf, self._cached_text, (self.padding, self.padding * 2))
        return bg_surf

    def update(self) -> bool:
        return True

    def draw(self, surf) -> engine.Surface:
        textbox_surf = self._get_surf()
        position = self._determine_position(self.size, surf.get_size(), self.alignment)
        engine.blit(surf, textbox_surf, position)
        return surf