from __future__ import annotations
from typing import List, Optional

import re

from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import TextEffect, ColorEffect, JitterEffect
from app.utilities.typing import NID

MATCH_TAG_RE = re.compile('<(.*?)>')
MATCH_CAPTURE_TAG_RE = re.compile('(<[^<]*?>)')

class TaggedText():
    def __init__(self, text: str, font: NID, effects: List[TextEffect]):
        self.text = text
        self.font = font
        self.effects = effects

    def get_start(self, end: int) -> TaggedText:
        if end > len(self.text):
            raise Exception(f"{__name__}: not enough text")
        return TaggedText(self.text[:end], self.font, self.effects)
    
    def get_end(self, start: int) -> TaggedText:
        if start >= len(self.text):
            raise Exception(f"{__name__}: not enough text")
        return TaggedText(self.text[start:], self.font, self.effects)

    def get_between(self, start: int, end: int) -> TaggedText:
        if start >= len(self.text) or end > len(self.text):
            raise Exception(f"{__name__}: not enough text")
        return TaggedText(self.text[start:end], self.font, self.effects)

    def __repr__(self):
        return f"({self.text}, {self.font}, {self.effects})"

def parse_styled_text(text: str, default_font: NID, default_color: Optional[NID],) -> List[TaggedText]:
    # process text for tags and push them onto stack for later processing
    tagged_texts = []
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
                tagged_texts.append(TaggedText(curr_text, curr_font, curr_effect_list))
        else: # no more tags to process
            if text: # not empty string
                tagged_texts.append(TaggedText(text, default_font, [ColorEffect(default_color)]))
            break

    return tagged_texts
