from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "apps" / "presentations" / "io" / "ppt-legacy-reader.js"


class LegacyPptStyleFontSizeContractTests(unittest.TestCase):
    def test_reader_recognizes_style_text_prop_atom_and_character_font_size_mask(self):
        source = READER.read_text(encoding="utf-8")
        self.assertIn("StyleTextProp:4001", source)
        self.assertIn("function legacyCharacterFontSize", source)
        self.assertIn("1<<13", source)

    def test_explicit_legacy_character_size_precedes_geometry_estimate(self):
        source = READER.read_text(encoding="utf-8")
        parse = source[source.index("function parseArtObjects") : source.index("function backgroundColorFromContainer")]
        self.assertIn("legacyCharacterFontSize(textbox", parse)
        self.assertIn("fontSizePt:explicitFontSize||d.fontSizePt", parse)

    def test_malformed_or_mixed_style_runs_keep_existing_fallback(self):
        source = READER.read_text(encoding="utf-8")
        helper = source[source.index("function legacyCharacterFontSize") : source.index("function officeProps")]
        self.assertIn("return null", helper)
        self.assertIn("sizes.size!==1", helper)
        self.assertIn("fontSizePt>=1&&fontSizePt<=4000", source)


if __name__ == "__main__":
    unittest.main()
