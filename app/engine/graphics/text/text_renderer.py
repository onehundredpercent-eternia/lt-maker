from __future__ import annotations

import re
from typing import List, Tuple, Optional

from app.engine import engine
from app.engine.fonts import FONT
from app.engine.icons import draw_icon_by_alias
from app.engine.jitter import get_jitter
from app.utilities.enums import HAlignment
from app.utilities.typing import NID

MATCH_TAG_RE = re.compile('<(.*?)>')
MATCH_CAPTURE_TAG_RE = re.compile('(<[^<]*?>)')

def font_height(font: NID):
    return FONT[font].height

def anchor_align(x: int, width: int, align: HAlignment, padding: Tuple[int, int] = (0, 0)) -> int:
    """Returns the appropriate anchor point for a specific align,
    given a specific box. For example, supposing the text box is
    this wide:

    padding[0] - A -------- B -------- C - padding[1]

    This will return A for left align, B for center align, and C for right align.
    Padding allows this to be offset.
    """
    if align == HAlignment.LEFT:
        return x + padding[0]
    if align == HAlignment.CENTER:
        return x + width // 2
    else:
        return width + x - padding[1]

def rendered_text_width(fonts: List[NID], texts: List[str]) -> int:
    """Returns the full rendered width (see render_text) of a text list.

    Args:
        fonts (List[NID]): List of fonts to use to write text.
        texts (List[str]): List of strings to write with corresponding fonts.

    Returns:
        int: Width of string if it were rendered
    """
    if not fonts:
        return 0
    if not texts:
        return 0
    if len(fonts) < len(texts):
        fonts += [fonts[-1] for i in range(len(texts) - len(fonts))]
    font_stack = list(reversed(fonts))
    text_stack = list(reversed(texts))

    base_font = fonts[-1]
    font_history_stack = []
    total_width = 0
    while text_stack:
        curr_text = text_stack.pop()
        curr_font = font_stack.pop()
        # process text for tags and push them onto stack for later processing
        any_tags = MATCH_TAG_RE.search(curr_text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag_font = any_tags.group().strip("<>")
            if '/' in tag_font:
                tag_font = font_history_stack.pop() if font_history_stack else base_font
            else:
                font_history_stack.append(curr_font)
            text_stack.append(curr_text[tag_end:])
            curr_text = curr_text[:tag_start]
            if tag_font in FONT or tag_font == 'icon':
                font_stack.append(tag_font)
            else:
                font_stack.append(curr_font)
        # actually render font
        if curr_font != 'icon':
            total_width += FONT[curr_font].width(curr_text)
        else:
            total_width += 16
    return total_width

def text_width(font: NID, text: str) -> int:
    """Simply determines the width of the text

    Args:
        font (NID): font to use to write text.
        text (str): string to write with corresponding font.

    Returns:
        int: Width of string if it were rendered
    """
    return rendered_text_width([font], [text])

def fix_tags(text_block: List[str]) -> List[str]:
    """Fixes unclosed tags.

    Example: ["You must push the <red>RED", "button</> or else you will die!"]
          -> ["You must push the <red>RED</>", "<red>button</> or else you will die!"]

    Args:
        text_block (List[str]): a chunk block of text that may have faulty tags

    Returns:
        List[str]: that same text block with tags properly closed
    """
    tag_stack = []
    fixed_text = []
    if not text_block:
        text_block = []
    for line in text_block:
        tags_in_line = re.findall(MATCH_TAG_RE, line)
        newline = line
        for tag in reversed(tag_stack):
            newline = "<%s>%s" % (tag, newline)
        for tag in tags_in_line:
            if '/' in tag: # closing, pop off the stack
                if tag_stack:
                    tag_stack.pop()
            else:
                tag_stack.append(tag)

        for tag in tag_stack:
            newline = "%s</>" % newline
        fixed_text.append(newline)
    return fixed_text

def remove_tags(text_block: List[str]) -> List[str]:
    """removes all tags.

    Example: ["You must push the <red>RED", "button</> or else you will die!"]
          -> ["You must push the RED", "button or else you will die!"]

    Args:
        text_block (List[str]): a chunk block of text that may have tags

    Returns:
        List[str]: that same text block with all tags removed
    """
    new_text_block = []
    for line in text_block:
        new_line = re.sub(MATCH_TAG_RE, '', line)
        new_text_block.append(new_line)
    return new_text_block

class TextEffect():
    def __init__(self):
        raise "TextEffect should not be directly instantiated"
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        pass

class NullEffect(TextEffect):
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return curr_color, curr_offset
    def __repr__(self):
        return "NullEffect"

class ColorEffect(TextEffect):
    def __init__(self, color: NID):
        self._color = color
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return self._color, curr_offset
    def __repr__(self):
        return f"{self._color}"

class JitterEffect(TextEffect):
    def __init__(self):
        self._jitter = get_jitter()
    def apply(self, curr_color: NID, curr_offset: Tuple[float, float]) -> Tuple[NID, Tuple[float, float]]:
        return curr_color, tuple(map(sum, zip(curr_offset, self._jitter)))
    def __repr__(self):
        return f"({self._jitter[0]:.2f},{self._jitter[1]:.2f})"

class TaggedText():
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

def _parse_text(text: str, default_font: NID, default_color: NID) -> List[TaggedText]:
    # process text for tags and push them onto stack for later processing
    print(f"input is: {text}, {default_font}, {default_color}")
    tagged_texts = []
    tag_history_stack = []
    keep_processing_tags = True
    while keep_processing_tags:
        any_tags = MATCH_TAG_RE.search(text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag = any_tags.group().strip("<>")
            curr_text = text[:tag_start]
            text = text[tag_end:]
            default_settings = tag_history_stack[-1] if tag_history_stack else (default_font, [ColorEffect(default_color)])
            curr_font = default_settings[0]
            curr_effect_list = list.copy(default_settings[1])
            if '/' in tag: # ending tag
                tag_history_stack.pop()
            else: # starting tag
                tag_font = curr_font
                tag_effect_list = list.copy(curr_effect_list)
                if tag in FONT or tag == 'icon': # special handling for fonts and icons
                    tag_font = tag
                elif tag == 'j':
                    tag_effect_list.append(JitterEffect())
                else: # we have a color tag
                    tag_effect_list.append(ColorEffect(tag)) # last ColorEffect pushed to list overrides
                tag_history_stack.append((tag_font, tag_effect_list))
            tagged_texts.append(TaggedText(curr_text, curr_font, curr_effect_list))
        else: # no more tags to process
            tagged_texts.append(TaggedText(text, default_font, [ColorEffect(default_color)]))
            keep_processing_tags = False

    print(f"output is: {tagged_texts}")
    return tagged_texts

def _tagged_text_width(tagged_texts: List[TaggedText]) -> int:
    total_width = 0
    for tagged_text in tagged_texts:
        curr_text = tagged_text.text
        curr_font = tagged_text.font
        if curr_font != 'icon':
            total_width += FONT[curr_font].width(curr_text)
        else:
            total_width += 16
    return total_width

def _render_text(surf: engine.Surface, tagged_texts: List[TaggedText], topleft: Tuple[int, int],
                  align: HAlignment = HAlignment.LEFT) -> engine.Surface:
    # for non-left alignments
    if align == HAlignment.CENTER or align == HAlignment.RIGHT:
        width = _tagged_text_width(tagged_texts)
        tx, ty = topleft
        if align == HAlignment.CENTER:
            tx -= width//2
        elif align == HAlignment.RIGHT:
            tx -= width
    else:
        tx, ty = topleft

    for tagged_text in tagged_texts:
        font = tagged_text.font
        text = tagged_text.text
        effects = tagged_text.effects
        if font == 'icon':
            draw_icon_by_alias(surf, text.strip(), (tx, ty))
            tx += 16
        else:
            curr_offset = (0, 0) # default offset
            curr_color = 'black' # default color
            for effect in effects:
                curr_color, curr_offset = effect.apply(curr_color, curr_offset)
            FONT[font].blit(text, surf, (tx, ty), curr_color, curr_offset)
            tx += FONT[font].width(text)

    return surf

def parse_text_and_render(surf: engine.Surface, text: str, default_font: NID,
                          default_color: Optional[NID], topleft: Tuple[int, int],
                          align: HAlignment = HAlignment.LEFT) -> engine.Surface:
    tagged_texts = _parse_text(text, default_font, default_color)
    return _render_text(surf, tagged_texts, topleft, align)

def render_text(surf: engine.Surface, fonts: List[NID], texts: List[str],
                colors: List[NID | None], topleft: Tuple[int, int],
                align: HAlignment = HAlignment.LEFT) -> engine.Surface:
    """An enhanced text render layer wrapper around BmpFont.
    Supports multiple fonts and multiple text sections, as well as
    embedded icons.

    Args:
        fonts (List[NID]): List of fonts to use to write text.
        texts (List[str]): List of strings to write with corresponding fonts.
        colors (List[str]): List of colors to write with corresponding fonts.

    Returns:
        engine.Surface: a surface that has text printed upon it.
    """
    if not fonts:
        return
    if not texts:
        return
    if not colors:
        colors = [None]
    if len(fonts) < len(texts):
        fonts += [fonts[-1] for i in range(len(texts) - len(fonts))]
    if len(colors) < len(texts):
        colors += [colors[-1] for i in range(len(texts) - len(colors))]
    font_stack = list(reversed(fonts))
    text_stack = list(reversed(texts))
    color_stack = list(reversed(colors))

    # for non-left alignments
    if align == HAlignment.CENTER or align == HAlignment.RIGHT:
        width = rendered_text_width(fonts, texts)
        tx, ty = topleft
        if align == HAlignment.CENTER:
            tx -= width//2
        elif align == HAlignment.RIGHT:
            tx -= width
    else:
        tx, ty = topleft

    base_font = fonts[-1]
    font_history_stack = []
    while text_stack:
        curr_text = text_stack.pop()
        curr_font = font_stack.pop()
        curr_color = color_stack.pop() if color_stack else None
        # process text for tags and push them onto stack for later processing
        any_tags = MATCH_TAG_RE.search(curr_text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag_font = any_tags.group().strip("<>")
            if '/' in tag_font:
                tag_font, tag_color = font_history_stack.pop() if font_history_stack else (base_font, None)
            else:
                if tag_font in FONT or tag_font == 'icon':
                    tag_color = curr_color
                else:
                    tag_color = tag_font
                    tag_font = curr_font
                font_history_stack.append((curr_font, curr_color))
            text_stack.append(curr_text[tag_end:])
            curr_text = curr_text[:tag_start]
            font_stack.append(tag_font)
            color_stack.append(tag_color)
        # actually render font
        if curr_font != 'icon':
            FONT[curr_font].blit(curr_text, surf, (tx, ty), curr_color, (0, 0))
            tx += FONT[curr_font].width(curr_text)
        else:
            draw_icon_by_alias(surf, curr_text.strip(), (tx, ty))
            tx += 16
    return surf
