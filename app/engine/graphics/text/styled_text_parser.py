from __future__ import annotations
from typing import Any, List, Dict, Tuple, Optional, Union, Iterator, NamedTuple

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

# this regex captures tags (strings enclosed with <>) lazily
MATCH_CAPTURE_TAG_RE = re.compile("(<[^<]*?>)")


class TaggedTextChunk:
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item) -> Optional[TaggedTextChunk]:
        substr = self.text[item]
        if substr:
            return TaggedTextChunk(substr, self.font, self.effects)
        else:
            return None

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"

    def width(self) -> int:
        """return the pixel width of this text chunk when rendered

        Returns:
            int: pixel width
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
        self.size: int = 0 # this is the total length of the individual chunks
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
        return "".join(repr(chunk) for chunk in self.chunks)

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

        chunk_idx = 0
        while stop > 0:
            curr_chunk = self.chunks[chunk_idx]
            subchunk = curr_chunk[start:stop]
            if subchunk:
                tagged_text.append_chunk(subchunk)
            start -= len(curr_chunk)
            stop -= len(curr_chunk)
            chunk_idx += 1

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


def _tokenize_styled_text(text: str) -> List[str]:
    """turns "A line. With some <red>text</>." -> ["A line. With some ", "<red>", "text", "</>", "."]
    """
    text_split_by_tags: List[str] = re.split(MATCH_CAPTURE_TAG_RE, text)
    # strip out empty strings
    return [x for x in text_split_by_tags if x]


def _is_tag(text: str) -> bool:
    """check whether a text chunk is a tag

    Args:
        text (str): chunk to check

    Returns:
        bool: whether it's a tag
    """
    return text.startswith("<") and text.endswith(">")


def _parse_arg(arg: str) -> Union[int, float, str]:
    """try to parse an arg string into a type
    Tries to parse as as int > float > string in that order

    Args:
        arg (str): Arg string

    Returns:
        Union[int, float, str]: Arg string parsed as int, float, or string
    """
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
    """individually parse tag_id and ignore args for a tag with <> stripped
    If tag_id is nonexistent it will be returned as None

    >>> _parse_tag_id('wave amplitude=5')
    'wave'
    >>> _parse_tag_id('/')
    '/'
    >>> _parse_tag_id('') # returns None

    Args:
        tag (str): Input tag with "<>" stripped

    Returns:
        Optional[NID]: Parsed tag_id
    """
    id_and_args = tag.split(" ")
    return id_and_args[0] if id_and_args[0] else None


def _parse_tag_id_and_args(tag: str) -> Tuple[Optional[NID], Optional[Dict[str:Any]]]:
    """parse tag string into tag id and args for a tag with <> stripped
    If tag_id is nonexistent it will be returned as None
    If tag_args are malformed, they will be returned as None
    If there are no arguments, tag_args will be returned as an empty dict

    >>> _parse_tag_id_and_args('wave amplitude=5')
    ('wave', {'amplitude': 5})
    >>> _parse_tag_id_and_args('/')
    ('/', {})
    >>> _parse_tag_id_and_args('')
    (None, None)
    >>> _parse_tag_id_and_args('wave amp litude=5')
    ('wave', None)
    >>> _parse_tag_id_and_args('wave amplitude=5=3')
    ('wave', None)
    >>> _parse_tag_id_and_args('wave amplitude = 5')
    ('wave', None)

    Args:
        tag (str): Input tag with "<>" stripped

    Returns:
        Tuple[Optional[NID], Optional[Dict[str:Any]]]: A tuple containing parsed (tag_id, tag_args)
    """
    id_and_args = tag.split(" ")
    if not id_and_args[0]:
        # malformed tag
        return (None, None)
    # expect args in the exact form "arg=val"
    tag_id = id_and_args[0]
    args = [x.split("=") for x in id_and_args[1:]]
    for arg in args:
        if len(arg) != 2:
            # malformed arg
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
    tokenized_text: List[str] = []
    text_split_by_tags: List[str] = _tokenize_styled_text(text)
    # decompose the non-command/tag elements into individual chars.
    for block in text_split_by_tags:
        if block.startswith("<") and block.endswith(">"):
            tokenized_text.append(block)
        else:  # normal char str (e.g. "hello")
            tokenized_text += list(block)

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
                except TypeError:
                    # broken arguments
                    pass

        def get_tags(self) -> Tuple[str, str]:
            assert self.char_level
            return self._effect.next().as_tags()

    # reconstructs individual characters into strings with CoordinatedTextEffects
    # decayed to TextEffects applied to individual characters
    preprocessed_text: str = ""
    tag_stack: List[Tag] = []
    for token in tokenized_text:
        if _is_tag(token):
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


def _parse_as_closing_tag(tag_stack: List[Tuple[NID, List[TextEffect]]]) -> bool:
    """parse a closing tag and return whether it was parsed successfully"""
    malformed_tag = False
    if tag_stack:
        tag_stack.pop()
    else:
        # orphaned closing tag with no opening tag
        logging.warning("Ignoring orphaned closing tag")
        malformed_tag = True

    return not malformed_tag


def _parse_as_starting_tag(
    tag_stack: List[Tuple[NID, List[TextEffect]]],
    tag: Tuple[NID, List[TextEffect]],
    curr_font: NID,
    curr_effects: List[TextEffect],
) -> bool:
    """parse a starting tag and return whether it was parsed successfully"""
    tag_font = curr_font
    tag_effects = list.copy(curr_effects)
    malformed_tag = False
    # parse tag arguments
    tag_id, tag_args = _parse_tag_id_and_args(tag)
    if RESOURCES.fonts.get(tag_id) or tag_id == "icon":
        # special handling for fonts and icons
        # expect no args
        if tag_args == {}:
            tag_font = tag_id
        else:
            logging.warning("Ignoring font tag with args: %s", tag)
            malformed_tag = True
    elif tag_id in RESOURCES.fonts.get(curr_font).palettes:
        # last ColorEffect pushed to list overrides
        # expect no args
        if tag_args == {}:
            tag_effects.append(ColorEffect(tag_id))
        else:
            logging.warning("Ignoring color tag with args: %s", tag)
            malformed_tag = True
    elif tag_id in TEXT_EFFECTS:
        try:
            tag_effects.append(TEXT_EFFECTS[tag_id](**tag_args))
        except TypeError:
            logging.warning("Ignoring tag with malformed or nonexistent args: %s", tag)
            malformed_tag = True
    else:
        logging.warning("Ignoring unknown tag: %s", tag)
        malformed_tag = True
    if not malformed_tag:
        tag_stack.append((tag_font, tag_effects))

    return not malformed_tag


def _parse_as_tag(
    chunk: str,
    tagged_text: TaggedText,
    tag_stack: List[Tuple[NID, List[TextEffect]]],
    default_tag: Tuple[NID, List[TextEffect]],
):
    """parse a tag and add it to stack or append it to tagged_text if malformed"""
    tag = chunk.strip("<>")
    parsed_successfully = False  # used to add malformed tag as text chunk
    curr_font, curr_effects = tag_stack[-1] if tag_stack else default_tag
    if tag.startswith("/"):  # ending tag
        parsed_successfully = _parse_as_closing_tag(tag_stack)
    else:  # starting tag
        parsed_successfully = _parse_as_starting_tag(
            tag_stack, tag, curr_font, curr_effects
        )
    if not parsed_successfully:  # display malformed tag as text if it exists
        tagged_text.append(chunk, curr_font, curr_effects)


def _parse_as_plain_text(
    chunk: str,
    tagged_text: TaggedText,
    tag_stack: List[Tuple[NID, List[TextEffect]]],
    default_tag: Tuple[NID, List[TextEffect]],
):
    """parse a plaintext chunk and append it to tagged_text"""
    curr_font, curr_effects = tag_stack[-1] if tag_stack else default_tag
    tagged_text.append(chunk, curr_font, curr_effects)


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
    text_split_by_tags: List[str] = _tokenize_styled_text(text)

    class Tag(NamedTuple):
        font: NID = default_font
        effects: List[TextEffect] = [ColorEffect(default_color)]

    tagged_text = TaggedText()
    tag_stack: List[Tag] = []
    default_tag = Tag()
    for chunk in text_split_by_tags:
        if _is_tag(chunk):
            _parse_as_tag(chunk, tagged_text, tag_stack, default_tag)
        else:  # plain text
            _parse_as_plain_text(chunk, tagged_text, tag_stack, default_tag)

    return tagged_text
