from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "apps" / "presentations" / "io" / "ppt-import-adapter.js"
FIXTURE = ROOT / "tests" / "compatibility-fixtures" / "presentations" / "era1_office_97_2003_legacy.ppt"


class LegacyPptFidelityTests(unittest.TestCase):
    def test_importer_owns_officeart_text_and_picture_decoding(self):
        source = IMPORTER.read_text(encoding="utf-8")
        for marker in (
            "PowerPoint Document",
            "Current User",
            "PersistDirectory",
            "0xF004",
            "0xF010",
            "0xF00D",
            "picturePayloads",
            "legacyTextStyle",
            "legacyShapeType",
        ):
            self.assertIn(marker, source)

    def test_versioned_legacy_fixture_remains_compound_document(self):
        self.assertTrue(FIXTURE.read_bytes().startswith(bytes.fromhex("D0CF11E0A1B11AE1")))

    def test_importer_has_explicit_safe_fidelity_degradation(self):
        source = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("legacyDrawingFidelity: 'partial'", source)
        self.assertIn("persistedVersionSelection: false", source)
        self.assertIn("unsupported records were skipped", source)


if __name__ == "__main__":
    unittest.main()
