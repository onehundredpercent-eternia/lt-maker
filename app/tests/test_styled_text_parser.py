import unittest

from app.engine.graphics.text.styled_text_parser import parse_styled_text, TaggedText

class DisplayTextParsingTest(unittest.TestCase):
    """
    Tests parsing of display text into tagged text
    """

    def _tagged_text_color(self, tagged_text: TaggedText):
        color = 'default_color'
        for effect in tagged_text.effects:
            color, _ = effect.apply(color, (0, 0))
        return color
    
    def _tagged_offsets(self, tagged_text: TaggedText):
        offsets = []
        for effect in tagged_text.effects:
            effect_name = str(effect).split("(")[0]
            if effect_name != "color":
                offsets.append(effect_name)
        return offsets

    def test_parsing(self):
        default_font = 'default_font'
        default_color = 'default_color'
        test_display_text = "<blue>this is some <red>red</> text<blue>"
        tagged_texts = parse_styled_text(test_display_text, default_font, default_color)

        # test that the text is parsed correctly based on tags
        actual_texts = [x.text for x in tagged_texts]
        expected_texts = ["this is some ", "red", " text"]
        self.assertEqual(actual_texts, expected_texts)

        # test that the font is correct
        actual_fonts = [x.font for x in tagged_texts]
        expected_fonts = [default_font, default_font, default_font]
        self.assertEqual(actual_fonts, expected_fonts)

        # test that the colors are correct
        actual_colors = [self._tagged_text_color(x) for x in tagged_texts]
        expected_colors = ["blue", "red", "blue"]
        self.assertEqual(actual_colors, expected_colors)

        # test that offsets are correct
        actual_offsets = [self._tagged_offsets(x) for x in tagged_texts]
        expected_offsets = [[], [], []]
        self.assertEqual(actual_offsets, expected_offsets)

if __name__ == '__main__':
    unittest.main()
