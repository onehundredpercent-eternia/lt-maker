from __future__ import annotations
from typing import Any, List, Dict, Tuple, Optional, Iterator

import re
import logging
from ast import literal_eval

from app.data.resources.resources import RESOURCES
from app.engine import engine
from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import (
    TextSettings,
    TextEffect,
    ColorEffect,
    TEXT_EFFECTS,
)
from app.utilities.typing import NID

MATCH_TAG_RE = re.compile("<(.*?)>")
MATCH_CAPTURE_TAG_RE = re.compile("(<[^<]*?>)")


class TaggedTextChunk:
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def width(self) -> int:
        """return the font width

        Returns:
            int: width
        """
        return FONT[self.font].width(self.text) if self.font != "icon" else 16

    def draw(self, surf: engine.Surface, topleft: Tuple[int, int]) -> int:
        """draw this TaggedTextChunk onto surf at topleft

        Args:
            surf (engine.Surface): surface to draw on
            topleft (Tuple[int, int]): top left location to begin drawing

        Returns:
            int: font width of the drawn TaggedTextChunk
        """
        if self.font == "icon":
            # not sure why but this import needs to go here to avoid a circular dependency
            from app.engine.icons import draw_icon_by_alias

            settings = TextSettings("", (0, 0))
            settings.apply(self.effects)
            draw_icon_by_alias(
                surf,
                self.text.strip(),
                (topleft[0] + settings.offset[0], topleft[1] + settings.offset[1]),
            )
            return self.width()

        has_bit_effect = False
        for effect in self.effects:
            if effect.is_char_level:
                # blit characters individually
                has_bit_effect = True

        if has_bit_effect:
            width = 0
            for idx, c in enumerate(self.text):
                settings = TextSettings("", (0, 0))
                settings.apply(self.effects, idx)
                FONT[self.font].blit(
                    c,
                    surf,
                    (
                        topleft[0] + width + settings.offset[0],
                        topleft[1] + settings.offset[1],
                    ),
                    settings.color,
                )
                width += FONT[self.font].width(c)
            return width
        else:
            settings = TextSettings("", (0, 0))
            settings.apply(self.effects)
            FONT[self.font].blit(
                self.text,
                surf,
                (topleft[0] + settings.offset[0], topleft[1] + settings.offset[1]),
                settings.color,
            )
            return self.width()

    def __eq__(self, other) -> bool:
        if not isinstance(other, TaggedTextChunk):
            return NotImplemented
        return (
            self.text == other.text
            and self.font == other.font
            and self.effects == other.effects
        )

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item):
        return TaggedTextChunk(self.text[item], self.font, self.effects)

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"


class TaggedText:
    def __init__(self):
        self.size: int = 0
        self.chunks: List[TaggedTextChunk] = []

    def append(self, text: str, font: NID, effects: List[TextEffect]):
        """add a chunk as parameters to TaggedTextChunk

        Args:
            text (str): raw text
            font (NID): associated font
            effects (List[TextEffect]): associated effects
        """
        chunk = TaggedTextChunk(text, font, effects)
        self.size += len(chunk)
        self.chunks.append(chunk)

    def append_chunk(self, chunk: TaggedTextChunk):
        """add a chunk as TaggedTextChunk

        Args:
            chunk (TaggedTextChunk): chunk to add
        """
        self.size += len(chunk)
        self.chunks.append(chunk)

    def width(self) -> int:
        """return the font width

        Returns:
            int: width
        """
        return sum([t.width() for t in self.chunks])

    def __eq__(self, other) -> bool:
        if not isinstance(other, TaggedText):
            return NotImplemented
        return self.size == other.size and self.chunks == other.chunks

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[TaggedTextChunk]:
        for chunk in self.chunks:
            yield chunk

    def __getitem__(self, item) -> TaggedText:
        if isinstance(item, slice):
            if item.step is not None:
                raise ValueError(
                    f"no support for indexing with a custom step {item.step}"
                )
            return self._get_slice(item.start, item.stop)
        else:
            if not isinstance(item, int):
                raise KeyError(f"only supports integer or slice keys not {type(item)}")
            return self._get_slice(item, item + 1)

    def _get_slice(self, start: Optional[int], stop: Optional[int]) -> TaggedText:
        if start is None:
            start = 0
        if stop is None:
            stop = len(self)

        if start < 0 or stop < 0:
            raise IndexError(f"no support for negative indexes {start}:{stop}")
        if start >= self.size or stop > self.size:
            raise IndexError(f"out of range {start}:{stop}")
        if stop < start:
            raise ValueError(f"no support for backwards slice {start}:{stop}")

        tagged_text = TaggedText()
        if start == stop:
            return tagged_text

        # process using a window (curr, total)
        # which represents the start and stop of the current tagged text
        curr = 0
        for chunk in self.chunks:
            total = curr + len(chunk)
            if total <= start:
                # skip this tagged text, we are not using it
                curr = total
                continue

            if curr <= start:
                if total >= stop:
                    # the entirety of the text we want to process is between the window
                    tagged_text.append_chunk(chunk[start - curr : stop - curr])
                    break
                else:
                    # grab the back portion after start
                    tagged_text.append_chunk(chunk[start - curr :])
                    curr = total
                    continue

            # here, curr > start
            if total < stop:
                tagged_text.append_chunk(chunk)
                curr = total
                continue
            else:
                # grab the first portion before stop
                tagged_text.append_chunk(chunk[: stop - curr])
                break

        return tagged_text

    def __repr__(self):
        s = ""
        for chunk in self.chunks:
            s += repr(chunk)
        return s

def _parse_tag_and_args(tag_args: str) -> Optional[Tuple[NID, Dict[str: Any]]]:
    """Parses a tag string into a tag and its args
    "wave amplitude=1" -> ("wave", {"amplitude": 1})

    Args:
        tag_args (str): _description_
    """
    tag_and_args = tag_args.split(" ")
    if not tag_and_args:
        # malformed tag
        return None
    tag = tag_and_args[0]
    args = [x.split("=") for x in tag_and_args[1:]]
    args = {x[0]: literal_eval(x[1]) for x in args}
    return (tag, args)

def parse_styled_text(
    text: str,
    default_font: NID,
    default_color: Optional[NID],
) -> TaggedText:
    """Parse styled text (text with no commands, only tags) into TaggedText

    Args:
        text (str): the styled text string to parse
        default_font (NID): front to parse text with no font tags as
        default_color (Optional[NID]): color to parse text with no color tags as
            None means text is parsed with default color associated with default_font

    Returns:
        TaggedText: TagedText object representing parse styled text
    """
    # process text for tags and push them onto stack for later processing
    tagged_text = TaggedText()
    tag_history_stack: List[Tuple[int, NID, List[TextEffect]]] = []
    length = 0
    while True:
        any_tags = MATCH_TAG_RE.search(text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag = any_tags.group().strip("<>")
            curr_text = text[:tag_start]
            length += len(curr_text)
            text = text[tag_end:]
            default_settings = (
                tag_history_stack[-1]
                if tag_history_stack
                else (0, default_font, [ColorEffect(default_color)])
            )
            curr_length, curr_font, curr_effect_list = default_settings
            if tag.startswith("/"):  # ending tag
                if tag_history_stack:
                    previous_tag_settings = tag_history_stack[-1]
                    for effect in previous_tag_settings[2]:
                        if effect.is_char_level:
                            effect.set_length(length - curr_length)
                    tag_history_stack.pop()
                else:
                    # orphaned closing tag with no opening tag
                    logging.warning("Ignoring orphaned closing tag")
            else:  # starting tag
                tag_font = curr_font
                tag_effect_list = list.copy(curr_effect_list)
                # parse tag arguments
                tag, args = _parse_tag_and_args(tag)
                if RESOURCES.fonts.get(tag) or tag == "icon":
                    # special handling for fonts and icons
                    tag_font = tag
                elif tag in RESOURCES.fonts.get(curr_font).palettes:
                    # last ColorEffect pushed to list overrides
                    tag_effect_list.append(ColorEffect(tag))
                elif tag in TEXT_EFFECTS:
                    tag_effect_list.append(TEXT_EFFECTS[tag](**args))
                else:
                    logging.warning("Ignoring unknown tag: %s", tag)
                tag_history_stack.append((length, tag_font, tag_effect_list))
            if curr_text:  # not empty string
                tagged_text.append(curr_text, curr_font, curr_effect_list)
        else:  # no more tags to process
            if text:  # not empty string
                length += len(text)
                default_settings = (
                    tag_history_stack[-1]
                    if tag_history_stack
                    else (0, default_font, [ColorEffect(default_color)])
                )
                curr_length, curr_font, curr_effect_list = default_settings
                for effect in curr_effect_list:
                    if effect.is_char_level:
                        effect.set_length(length - curr_length)
                tagged_text.append(text, curr_font, curr_effect_list)
            break

    return tagged_text
