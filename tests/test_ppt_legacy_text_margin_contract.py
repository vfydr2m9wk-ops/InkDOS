from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "apps" / "presentations" / "io" / "ppt-legacy-reader.js"


class LegacyPptTextMarginContractTests(unittest.TestCase):
    def test_legacy_reader_preserves_explicit_escher_text_margins(self):
        source = READER.read_text(encoding="utf-8")
        self.assertIn("function legacyTextMargins", source)
        helper = source[source.index("function legacyTextMargins") : source.index("function parseArtObjects")]
        for prop_id in ("0x0081", "0x0082", "0x0083", "0x0084"):
            self.assertIn(prop_id, helper)
        parse = source[source.index("function parseArtObjects") : source.index("function backgroundColorFromContainer")]
        self.assertIn("legacyTextMargins(props)", parse)
        self.assertIn("marginLeftEmu:margins.left", parse)
        self.assertIn("marginRightEmu:margins.right", parse)
        self.assertIn("marginTopEmu:margins.top", parse)
        self.assertIn("marginBottomEmu:margins.bottom", parse)

    def test_missing_or_implausible_margin_properties_keep_safe_fallbacks(self):
        source = READER.read_text(encoding="utf-8")
        helper = source[source.index("function legacyTextMargins") : source.index("function parseArtObjects")]
        self.assertIn("toEmu(36)", helper)
        self.assertIn("toEmu(18)", helper)
        self.assertIn("914400*4", helper)


if __name__ == "__main__":
    unittest.main()
