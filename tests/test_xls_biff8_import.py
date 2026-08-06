from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "apps" / "spreadsheets" / "xls-biff8-engine.js"
PUBLIC_FIXTURE = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets" / "era1_office_97_2003_legacy.xls"
STRESS_FIXTURE = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets" / "independent_libreoffice_biff8_stress.xls"
ZERO_FIXTURE = ROOT / "tests" / "compatibility-fixtures" / "spreadsheets" / "independent_biff8_zero_formula_display.xls"


def parse_fixture(path: Path):
    script = f"""
    global.window=global;
    if(!URL.createObjectURL) URL.createObjectURL=()=> 'blob:test';
    require({json.dumps(str(IMPORTER))});
    const fs=require('fs');
    (async()=>{{
      const b=fs.readFileSync({json.dumps(str(path))});
      const ab=b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
      const book=await LocalXLS.parseWorkbook(ab,{json.dumps(path.name)});
      const first=book.sheets[0];
      console.log(JSON.stringify({{
        legacy:book.legacy,
        format:book.legacyFormat,
        active:book.active,
        sheets:book.sheets.map(s=>({{name:s.name,state:s.state,cells:s.cells.size,merges:s.merges.length,drawings:s.drawings.length,maxC:s.maxC}})),
        diagnostics:book.legacyDiagnostics,
        values:Object.fromEntries(['A1','A8','A11','A189','B6','B7'].map(k=>[k,first.cells.get(k)?.v ?? null])),
        titleStyle:first.cells.get('A1')?.style || {{}},
        pageSetup:first.pageSetup || {{}}
      }}));
    }})().catch(e=>{{console.error(e);process.exit(1)}});
    """
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(completed.stdout.strip())


def parse_zero_fixture():
    script = f"""
    global.window=global;
    if(!URL.createObjectURL) URL.createObjectURL=()=> 'blob:test';
    require({json.dumps(str(IMPORTER))});
    const fs=require('fs');
    (async()=>{{
      const b=fs.readFileSync({json.dumps(str(ZERO_FIXTURE))});
      const ab=b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
      const book=await LocalXLS.parseWorkbook(ab,{json.dumps(ZERO_FIXTURE.name)});
      const sheet=book.sheets[0];
      const result={{}};
      for(const ref of ['B2','B3','B4','B5','B6']){{
        const cell=sheet.cells.get(ref);
        const effective=cell?.v;
        result[ref]={{
          value:effective,
          display:cell?.display ?? '',
          hideZero:!!cell?.style?.hideZero,
          legacyFormula:!!cell?.legacyFormula,
          rendered:(cell?.style?.hideZero&&Number(effective)===0)?'':(cell?.display ?? cell?.v ?? '')
        }};
      }}
      console.log(JSON.stringify(result));
    }})().catch(e=>{{console.error(e);process.exit(1)}});
    """
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(completed.stdout.strip())


class LegacyXlsImportTests(unittest.TestCase):
    def test_importer_and_fixtures_exist(self):
        self.assertTrue(IMPORTER.is_file())
        self.assertTrue(PUBLIC_FIXTURE.is_file())
        self.assertTrue(STRESS_FIXTURE.is_file())
        self.assertTrue(ZERO_FIXTURE.is_file())

    def test_synthetic_biff8_fixture_parses_offline(self):
        data = parse_fixture(PUBLIC_FIXTURE)
        self.assertTrue(data["legacy"])
        self.assertEqual(data["format"], "BIFF8")
        self.assertGreaterEqual(len(data["sheets"]), 2)
        self.assertGreater(sum(s["cells"] for s in data["sheets"]), 20)
        self.assertGreaterEqual(data["diagnostics"]["imageCount"], 1)

    def test_sst_continuations_fonts_orientation_and_used_columns(self):
        data = parse_fixture(STRESS_FIXTURE)
        self.assertEqual(data["sheets"][0]["name"], "Résumé Ω")
        self.assertEqual(data["sheets"][1]["state"], "hidden")
        self.assertEqual(len(data["values"]["A8"]), 10520)
        self.assertTrue(data["values"]["A11"].startswith("row-001-"))
        self.assertTrue(data["values"]["A189"].startswith("row-179-"))
        self.assertEqual(data["values"]["B6"], 1244.5)
        self.assertEqual(data["values"]["B7"], "YES")
        self.assertTrue(data["titleStyle"]["font"]["bold"])
        self.assertEqual(data["titleStyle"]["font"]["size"], 14)
        self.assertEqual(data["pageSetup"]["orientation"], "landscape")
        self.assertLessEqual(data["sheets"][0]["maxC"], 20)
        self.assertGreaterEqual(data["diagnostics"]["imageCount"], 1)


    def test_formula_zero_with_visible_number_format_is_not_blank(self):
        cells = parse_zero_fixture()
        self.assertEqual(cells["B2"]["value"], 0)
        self.assertTrue(cells["B2"]["legacyFormula"])
        self.assertFalse(cells["B2"]["hideZero"])
        self.assertEqual(cells["B2"]["display"], "0.00")
        self.assertEqual(cells["B2"]["rendered"], "0.00")

    def test_formula_zero_obeys_explicit_hidden_zero_format(self):
        cells = parse_zero_fixture()
        self.assertEqual(cells["B3"]["value"], 0)
        self.assertTrue(cells["B3"]["legacyFormula"])
        self.assertTrue(cells["B3"]["hideZero"])
        self.assertEqual(cells["B3"]["rendered"], "")

    def test_literal_zero_uses_the_same_number_format_rules(self):
        cells = parse_zero_fixture()
        self.assertEqual(cells["B4"]["value"], 0)
        self.assertFalse(cells["B4"]["legacyFormula"])
        self.assertFalse(cells["B4"]["hideZero"])
        self.assertEqual(cells["B4"]["rendered"], "0.00")
        self.assertEqual(cells["B5"]["value"], 0)
        self.assertTrue(cells["B5"]["hideZero"])
        self.assertEqual(cells["B5"]["rendered"], "")

    def test_nonzero_formula_display_is_unchanged(self):
        cells = parse_zero_fixture()
        self.assertEqual(cells["B6"]["value"], 1)
        self.assertTrue(cells["B6"]["legacyFormula"])
        self.assertFalse(cells["B6"]["hideZero"])
        self.assertEqual(cells["B6"]["display"], "1.00")
        self.assertEqual(cells["B6"]["rendered"], "1.00")

    def test_imported_xls_is_exported_as_xlsx(self):
        app = (ROOT / "apps" / "spreadsheets" / "app.js").read_text(encoding="utf-8")
        engine = (ROOT / "apps" / "spreadsheets" / "xlsx-engine.js").read_text(encoding="utf-8")
        self.assertIn("Save creates XLSX", app)
        self.assertIn("legacyStylesXml", engine)
        self.assertIn("drawingXmlForSheet", engine)
        self.assertIn("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", engine)


if __name__ == "__main__":
    unittest.main()
