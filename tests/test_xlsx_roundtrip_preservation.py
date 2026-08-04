from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "apps" / "spreadsheets" / "xlsx-engine.js"
APP = ROOT / "apps" / "spreadsheets" / "app.js"
FIX = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets"


class XlsxRoundTripTests(unittest.TestCase):
    def test_three_era_fixtures_exist(self):
        for name in (
            "era1_office_97_2003_legacy.xls",
            "era2_office_2007_2013_baseline.xlsx",
            "era3_office_2016_365_modern.xlsx",
        ):
            self.assertTrue((FIX / name).is_file(), name)

    def test_package_preserving_writer_is_used(self):
        source = ENGINE.read_text(encoding="utf-8")
        self.assertIn("patchSheetXml", source)
        self.assertIn("book.zip.generateAsync({type:'uint8array'})", source)
        self.assertIn("zip.file(s.path,patchSheetXml(raw,s)", source)
        self.assertNotIn("for(const s of book.sheets)book.zip.file(s.path,serializeSheet(s))", source)

    def test_modern_preview_paths_are_present(self):
        source = APP.read_text(encoding="utf-8")
        for token in ("XLOOKUP", "FILTER", "LET", "sheet-chart", "state!=='hidden'", "dynamic-array-preview"):
            self.assertIn(token, source)

    def test_baseline_fixture_contains_preserved_structures(self):
        with zipfile.ZipFile(FIX / "era2_office_2007_2013_baseline.xlsx") as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
            self.assertIn("<pane", sheet)
            self.assertIn("<pageSetup", sheet)
            self.assertIn("<cols>", sheet)
            self.assertIn("<drawing", sheet)

    def test_modern_fixture_contains_advanced_structures(self):
        with zipfile.ZipFile(FIX / "era3_office_2016_365_modern.xlsx") as archive:
            names = set(archive.namelist())
            sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
            workbook = archive.read("xl/workbook.xml").decode("utf-8")
            self.assertIn("<tableParts", sheet)
            self.assertIn("<conditionalFormatting", sheet)
            self.assertIn("<dataValidations", sheet)
            self.assertIn("<autoFilter", sheet)
            self.assertIn('state="hidden"', workbook)
            self.assertTrue(any(n.startswith("xl/charts/") for n in names))
            self.assertTrue(any(n.startswith("xl/tables/") for n in names))

    def test_legacy_extension_uses_local_biff8_importer(self):
        source = APP.read_text(encoding="utf-8")
        html = (ROOT / "apps" / "spreadsheets" / "index.html").read_text(encoding="utf-8")
        importer = (ROOT / "apps" / "spreadsheets" / "xls-biff8-engine.js").read_text(encoding="utf-8")
        self.assertIn("LocalXLS.parseWorkbook", source)
        self.assertIn(".xls,.xlsx", html)
        self.assertIn("class CFBReader", importer)
        self.assertIn("BIFF8", importer)
        self.assertIn("Saving creates an XLSX copy", importer)



if __name__ == "__main__":
    unittest.main()
