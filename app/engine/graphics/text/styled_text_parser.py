from __future__ import annotations
from typing import List, Optional

import re

from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import TextEffect, ColorEffect, JitterEffect
from app.utilities.typing import NID

MATCH_TAG_RE = re.compile('<(.*?)>')
MATCH_CAPTURE_TAG_RE = re.compile('(<[^<]*?>)')

class TaggedTextChunk():
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def width(self):
        return FONT[self.font].width(self.text) if self.font != 'icon' else 16

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item):
        return TaggedTextChunk(self.text[item], self.font, self.effects)

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"

class TaggedText():
    def __init__(self):
        self.size = 0
        self.chunks = []

    def append(self, text: str, font: NID, effects: List[TextEffect]):
        chunk = TaggedTextChunk(text, font, effects)
        self.size += len(chunk)
        self.chunks.append(chunk)

    def append_chunk(self, chunk: TaggedTextChunk):
        self.size += len(chunk)
        self.chunks.append(chunk)

    def width(self) -> int:
        return sum([t.width() for t in self.chunks])

    def __iter__(self):
        for chunk in self.chunks:
            yield chunk
        
    def __getitem__(self, item) -> TaggedTextChunk:
        if isinstance(item, slice):
            if item.step is not None:
                raise ValueError(f"TaggedText does not support indexing with custom step {item.step}")
            return self._get_slice(item.start, item.stop)
        else:
            if not isinstance(int):
                raise KeyError
            return self._get_slice(item, item)

    def _get_slice(self, start: int, stop: int) -> TaggedText:
        if stop < start:
            raise ValueError
        if start < 0 or stop < 0:
            raise ValueError
        if start >= self.size or stop > self.size:
            raise IndexError

        tagged_text = TaggedText()

        # process using a window (curr, total)
        # which represents the start and stop of the current tagged text
        curr = 0
        for chunk in self.chunks:
            total = curr + len(chunk)
            if total < start:
                # skip this tagged text, we are not using it
                curr = total
                continue

            if curr <= start:
                if total >= stop:
                    # the entirety of the text we want to process is between the window
                    tagged_text.append_chunk(chunk[start - curr:stop - curr])
                    break
                else:
                    # grab the back portion after start
                    tagged_text.append_chunk(chunk[start - curr:])
                    curr = total
                    continue

            # here, curr > start
            if total < stop:
                tagged_text.append_chunk(chunk)
                curr = total
                continue
            else:
                # grab the first portion before stop
                tagged_text.append_chunk(chunk[:stop - curr])
                break

        return tagged_text

def parse_styled_text(text: str, default_font: NID, default_color: Optional[NID],) -> TaggedText:
    # process text for tags and push them onto stack for later processing
    tagged_text = TaggedText()
    tag_history_stack = []
    while True:
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
                elif tag == "jitter" or tag == 'j':
                    tag_effect_list.append(JitterEffect())
                else: # we have a color tag
                    tag_effect_list.append(ColorEffect(tag)) # last ColorEffect pushed to list overrides
                tag_history_stack.append((tag_font, tag_effect_list))
            if curr_text: # not empty string
                tagged_text.append(curr_text, curr_font, curr_effect_list)
        else: # no more tags to process
            if text: # not empty string
                tagged_text.append(text, default_font, [ColorEffect(default_color)])
            break

    return tagged_text
