from __future__ import annotations
from typing import Any, List, Dict, Tuple, Optional, Union, Iterator

import re
import logging

from app.data.resources.resources import RESOURCES
from app.engine import engine
from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import (
    TextSettings,
    TextEffect,
    ColorEffect,
    CoordinatedTextEffect,
    TEXT_EFFECTS,
    COORDINATED_TEXT_EFFECTS,
)
from app.utilities.typing import NID

MATCH_TAG_RE = re.compile("<(.*?)>")
MATCH_CAPTURE_TAG_RE = re.compile("(<[^<]*?>)")


class TaggedTextChunk:
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item):
        return TaggedTextChunk(self.text[item], self.font, self.effects)

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"

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

        settings = TextSettings("", (0, 0))
        settings.apply(self.effects)
        FONT[self.font].blit(
            self.text,
            surf,
            (topleft[0] + settings.offset[0], topleft[1] + settings.offset[1]),
            settings.color,
        )
        return self.width()


class TaggedText:
    def __init__(self):
        self.size: int = 0
        self.chunks: List[TaggedTextChunk] = []

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

    def __repr__(self):
        s = ""
        for chunk in self.chunks:
            s += repr(chunk)
        return s

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

        if start == 0 and stop == self.size:
            return self

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

    def update(self):
        """update the internal state of all text effects, should be called once per frame"""
        # WARNING: this function relies on __eq__ not being implemented for TaggedTextChunk
        effects_updated = set()
        for chunk in self.chunks:
            for effect in chunk.effects:
                if effect not in effects_updated:
                    effect.update()
                    effects_updated.add(effect)


def _parse_arg(arg: str) -> Union[int, float, str]:
    try:
        val = int(arg)
        return val
    except Exception:
        pass
    try:
        val = float(arg)
        return val
    except Exception:
        pass
    return arg


def _parse_tag_id(tag: str) -> Optional[NID]:
    id_and_args = tag.split(" ")
    return id_and_args[0] if id_and_args else None


def _parse_tag_id_and_args(tag: str) -> Tuple[Optional[NID], Optional[Dict[str:Any]]]:
    id_and_args = tag.split(" ")
    if not id_and_args:
        # malformed tag
        return (None, None)
    # expect args in the exact form "arg=val"
    tag_id = id_and_args[0]
    args = [x.split("=") for x in id_and_args[1:]]
    for arg in args:
        if len(arg) != 2:
            # maformed arg
            return (tag_id, None)
    args = {x[0]: _parse_arg(x[1]) for x in args}
    return (tag_id, args)


def _preprocess_tags(text: str) -> str:
    """preprocesses text to decay CoordinateTextEffects into TextEffects
    "<wave>hi</>" -> ("<sin idx=0 x_amplitude=0 y_amplitude=3.5>h</>"
                      "<sin idx=0 x_amplitude=0 y_amplitude=3.5>i</>")

    Args:
        text (str): styled text with various tags

    Returns:
        str: styled text with CoordinatedTextEffect tags decayed to TextEffect tags
    """
    processed_text: List[str] = []
    # obligatory regex explanation: turns "A line.{w} With some <red>text</>."
    # into ["A line.", "{w}", " With some ", "<red>", "text", "</>", "."]
    # and then decomposes the non-command/tag elements into individual chars.
    text_split_by_tags: List[str] = re.split(MATCH_CAPTURE_TAG_RE, text)
    for block in text_split_by_tags:
        if block.startswith("<") and block.endswith(">"):
            processed_text.append(block)
        else:  # normal char str (e.g. "hello")
            processed_text += list(block)

    class Tag:
        def __init__(self, tag: str):
            self._effect: Optional[CoordinatedTextEffect] = None
            self.char_level: bool = False
            tag_id = _parse_tag_id(tag)
            if tag_id in COORDINATED_TEXT_EFFECTS:
                _, tag_args = _parse_tag_id_and_args(tag)
                try:
                    self._effect = COORDINATED_TEXT_EFFECTS[tag_id](**tag_args)
                    self.char_level = True
                    print(f"found char level effect {tag_id}")
                    input()
                except Exception:
                    # broken arguments
                    pass

        def get_tags(self) -> Tuple[str, str]:
            assert self.char_level
            return self._effect.next().as_tags()

    preprocessed_text: str = ""
    tag_stack: List[Tag] = []
    for token in processed_text:
        if len(token) > 1:  # tag
            tag = token.strip("<>")
            if tag.startswith("/"):  # closing tag
                if not tag_stack or not tag_stack.pop().char_level:
                    preprocessed_text += token
            else:  # starting tag
                tag_stack.append(Tag(tag))
                if not tag_stack[-1].char_level:
                    preprocessed_text += token
        else:
            tags_start = ""
            tags_end = ""
            for tag in tag_stack:
                if tag.char_level:
                    tag_start, tag_end = tag.get_tags()
                    tags_start += tag_start
                    tags_end += tag_end
            preprocessed_text += tags_start + token + tags_end

    return preprocessed_text


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
        TaggedText: TaggedText object representing parse styled text
    """
    # process text for tags and push them onto stack for later processing
    text = _preprocess_tags(text)
    tagged_text = TaggedText()
    tag_history_stack: List[Tuple[int, NID, List[TextEffect]]] = []
    while True:
        any_tags = MATCH_TAG_RE.search(text)
        if any_tags:
            tag_start, tag_end = any_tags.span()
            tag = any_tags.group().strip("<>")
            malformed_tag = None
            curr_text = text[:tag_start]
            text = text[tag_end:]
            default_settings = (
                tag_history_stack[-1]
                if tag_history_stack
                else (default_font, [ColorEffect(default_color)])
            )
            curr_font, curr_effect_list = default_settings
            if tag.startswith("/"):  # ending tag
                if tag_history_stack:
                    tag_history_stack.pop()
                else:
                    # orphaned closing tag with no opening tag
                    logging.warning("Ignoring orphaned closing tag")
                    malformed_tag = f"<{tag}>"
            else:  # starting tag
                tag_font = curr_font
                tag_effect_list = list.copy(curr_effect_list)
                # parse tag arguments
                tag_id, tag_args = _parse_tag_id_and_args(tag)
                if RESOURCES.fonts.get(tag_id) or tag_id == "icon":
                    # special handling for fonts and icons
                    # expect no args
                    if tag_args == {}:
                        tag_font = tag_id
                    else:
                        logging.warning("Ignoring font tag with args: %s", tag)
                        malformed_tag = f"<{tag}>"
                elif tag_id in RESOURCES.fonts.get(curr_font).palettes:
                    # last ColorEffect pushed to list overrides
                    # expect no args
                    if tag_args == {}:
                        tag_effect_list.append(ColorEffect(tag_id))
                    else:
                        logging.warning("Ignoring color tag with args: %s", tag)
                        malformed_tag = f"<{tag}>"
                elif tag_id in TEXT_EFFECTS:
                    try:
                        tag_effect_list.append(TEXT_EFFECTS[tag_id](**tag_args))
                    except TypeError:
                        logging.warning(
                            "Ignoring tag with malformed or nonexistent args: %s", tag
                        )
                        malformed_tag = f"<{tag}>"
                else:
                    logging.warning("Ignoring unknown tag: %s", tag)
                    malformed_tag = f"<{tag}>"
                if not malformed_tag:
                    tag_history_stack.append((tag_font, tag_effect_list))
            if curr_text:  # not empty string
                tagged_text.append(curr_text, curr_font, curr_effect_list)
            if malformed_tag:  # display malformed tag as text
                tagged_text.append(malformed_tag, curr_font, curr_effect_list)
        else:  # no more tags to process
            if text:  # not empty string
                default_settings = (
                    tag_history_stack[-1]
                    if tag_history_stack
                    else (default_font, [ColorEffect(default_color)])
                )
                curr_font, curr_effect_list = default_settings
                tagged_text.append(text, curr_font, curr_effect_list)
            break

    return tagged_text
