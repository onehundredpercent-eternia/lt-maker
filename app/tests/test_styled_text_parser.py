from __future__ import annotations

import unittest

from typing import Tuple

from app.engine.fonts import FONT
from app.engine.graphics.text.text_effects import TextSettings
from app.engine.graphics.text.styled_text_parser import (TaggedTextChunk,
                                                         parse_styled_text)
from app.utilities.typing import NID

class DisplayTextParsingTest(unittest.TestCase):
    """
    Tests parsing of display text into tagged text
    """

    def _tagged_text_color(self, chunk: TaggedTextChunk) -> NID:
        settings = TextSettings("default_color", (0, 0))
        settings.apply(chunk.effects)
        return settings.color
    
    def _tagged_offsets(self, chunk: TaggedTextChunk) -> Tuple[float, float]:
        offsets = []
        for effect in chunk.effects:
            effect_name = str(effect).split("(")[0]
            if effect_name != "color":
                offsets.append(effect_name)
        return offsets

    def test_parsing(self):
        default_font = "default_font"
        default_color = "default_color"
        test_display_text = "<blue>this is some <red>red</> and some <j>jittering <green>green</></> text</>"
        tagged_text = parse_styled_text(test_display_text, default_font, default_color)

        # test that the text is parsed correctly based on tags
        actual_texts = [x.text for x in tagged_text]
        expected_texts = ["this is some ", "red", " and some ", "jittering ", "green", " text"]
        self.assertEqual(actual_texts, expected_texts)

        # test that the font is correct
        actual_fonts = [x.font for x in tagged_text]
        expected_fonts = [default_font, default_font, default_font, default_font, default_font, default_font]
        self.assertEqual(actual_fonts, expected_fonts)

        # test that the colors are correct
        actual_colors = [self._tagged_text_color(x) for x in tagged_text]
        expected_colors = ["blue", "red", "blue", "blue", "green", "blue"]
        self.assertEqual(actual_colors, expected_colors)

        # test that offsets are correct
        actual_offsets = [self._tagged_offsets(x) for x in tagged_text]
        expected_offsets = [[], [], [], ["jitter"], ["jitter"], []]
        self.assertEqual(actual_offsets, expected_offsets)

    def test_parsing_malformed(self):
        default_font = "default_font"
        default_color = "default_color"
        test_display_text = "<blue>blue text? <red>red text?</> but did not close blue"
        tagged_text = parse_styled_text(test_display_text, default_font, default_color)

        # test that the text is parsed correctly based on tags
        actual_texts = [x.text for x in tagged_text]
        expected_texts = ["blue text? ", "red text?", " but did not close blue"]
        self.assertEqual(actual_texts, expected_texts)

        # test that the font is correct
        actual_fonts = [x.font for x in tagged_text]
        expected_fonts = [default_font, default_font, default_font]
        self.assertEqual(actual_fonts, expected_fonts)

        # test that the colors are correct
        actual_colors = [self._tagged_text_color(x) for x in tagged_text]
        expected_colors = ["blue", "red", "blue"]
        self.assertEqual(actual_colors, expected_colors)

        # test that offsets are correct
        actual_offsets = [self._tagged_offsets(x) for x in tagged_text]
        expected_offsets = [[], [], []]
        self.assertEqual(actual_offsets, expected_offsets)

    def test_indexing(self):
        default_font = "default_font"
        default_color = "default_color"
        test_display_text = "<blue>this is some <red>red</> text</>"
        tagged_text = parse_styled_text(test_display_text, default_font, default_color)

        # test that single indices work as expected
        indexed_text = tagged_text[0]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "t")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[12]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, " ")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[13]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "r")
        self.assertEqual(self._tagged_text_color(chunk), "red")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[15]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "d")
        self.assertEqual(self._tagged_text_color(chunk), "red")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[16]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, " ")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[20]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "t")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        # test that indexing out of bounds asserts
        with self.assertRaises(IndexError):
            tagged_text[-1]
        with self.assertRaises(IndexError):
            tagged_text[len(tagged_text)]

    def test_slicing(self):
        default_font = "default_font"
        default_color = "default_color"
        test_display_text = "<blue>this is some <red>red</> text</>"
        tagged_text = parse_styled_text(test_display_text, default_font, default_color)

        # test that single slices work as expected
        indexed_text = tagged_text[:]
        self.assertEqual(indexed_text, tagged_text)

        indexed_text = tagged_text[:len(tagged_text)]
        self.assertEqual(indexed_text, tagged_text)

        indexed_text = tagged_text[0:]
        self.assertEqual(indexed_text, tagged_text)

        indexed_text = tagged_text[0:0]
        self.assertEqual(len(indexed_text.chunks), 0)

        indexed_text = tagged_text[3:13]
        self.assertEqual(len(indexed_text.chunks), 1)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "s is some ")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[3:14]
        self.assertEqual(len(indexed_text.chunks), 2)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "s is some ")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])
        chunk = indexed_text.chunks[1]
        self.assertEqual(chunk.text, "r")
        self.assertEqual(self._tagged_text_color(chunk), "red")
        self.assertEqual(self._tagged_offsets(chunk), [])

        indexed_text = tagged_text[3:20]
        self.assertEqual(len(indexed_text.chunks), 3)
        chunk = indexed_text.chunks[0]
        self.assertEqual(chunk.text, "s is some ")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])
        chunk = indexed_text.chunks[1]
        self.assertEqual(chunk.text, "red")
        self.assertEqual(self._tagged_text_color(chunk), "red")
        self.assertEqual(self._tagged_offsets(chunk), [])
        chunk = indexed_text.chunks[2]
        self.assertEqual(chunk.text, " tex")
        self.assertEqual(self._tagged_text_color(chunk), "blue")
        self.assertEqual(self._tagged_offsets(chunk), [])

        # test that slicing with out of bounds and invalid slices
        with self.assertRaises(IndexError):
            tagged_text[-1:]
        with self.assertRaises(IndexError):
            tagged_text[:-1]
        with self.assertRaises(IndexError):
            tagged_text[:len(tagged_text) + 1]
        with self.assertRaises(IndexError):
            tagged_text[len(tagged_text):]
        with self.assertRaises(ValueError):
            tagged_text[5:0]
        with self.assertRaises(ValueError):
            tagged_text[0:5:1]

if __name__ == "__main__":
    unittest.main()
