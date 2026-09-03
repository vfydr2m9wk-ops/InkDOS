from pathlib import Path
import json
import subprocess
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
        self.assertIn("persistedVersionSelection: persisted.selected.length > 0", source)
        self.assertIn("unsupported records were skipped", source)

    def test_importer_executes_against_real_versioned_fixture(self):
        script = """
const fs = require('fs'), vm = require('vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const context = { TextDecoder, Uint8Array, DataView, ArrayBuffer, Set, Math, String, Number, Object, console, btoa: value => Buffer.from(value, 'binary').toString('base64') };
context.window = context;
vm.runInNewContext(source, context);
const bytes = fs.readFileSync(process.argv[2]);
const buffer = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
const result = context.InkDeskPresentationsPptImport.importLegacyPpt(buffer, 'fixture.ppt');
const objects = result.slides.flatMap(slide => slide.objects);
process.stdout.write(JSON.stringify({ source: result.source, slides: result.slides.length, text: objects.filter(object => object.type === 'text').length, images: objects.filter(object => object.type === 'image').length, notes: result.legacyDiagnostics.notesCount, persisted: result.compatibility.persistedVersionSelection, persistMap: Object.keys(result.legacyDiagnostics.persistMap).length }));
"""
        result = subprocess.run(
            ["node", "-e", script, str(IMPORTER), str(FIXTURE)],
            check=True, capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        self.assertEqual(data["source"], "ppt")
        self.assertEqual(data["slides"], 3)
        self.assertGreater(data["text"], 0)
        self.assertGreaterEqual(data["images"], 1)
        self.assertTrue(data["persisted"])
        self.assertGreater(data["persistMap"], 0)

    def test_malformed_input_is_rejected_without_out_of_bounds_read(self):
        script = """
const fs = require('fs'), vm = require('vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const context = { TextDecoder, Uint8Array, DataView, ArrayBuffer, Set, Math, String, Number, Object, console };
context.window = context;
vm.runInNewContext(source, context);
try { context.InkDeskPresentationsPptImport.importLegacyPpt(new Uint8Array(512).buffer, 'bad.ppt'); process.exit(1); }
catch (error) { if (!/valid legacy PowerPoint/i.test(error.message)) process.exit(2); }
"""
        subprocess.run(["node", "-e", script, str(IMPORTER)], check=True)


if __name__ == "__main__":
    unittest.main()
