from pathlib import Path
from zipfile import ZipFile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests' / 'compatibility-fixtures' / 'documents'

class DocxRoundTripPreservationTests(unittest.TestCase):
    def test_three_era_fixtures_are_included(self):
        self.assertTrue((FIX / 'era1_office_97_2003_legacy.doc').is_file())
        self.assertTrue((FIX / 'era2_office_2007_2013_baseline.docx').is_file())
        self.assertTrue((FIX / 'era3_office_2016_365_modern.docx').is_file())

    def test_baseline_fixture_contains_roundtrip_features(self):
        with ZipFile(FIX / 'era2_office_2007_2013_baseline.docx') as z:
            names=set(z.namelist()); document=z.read('word/document.xml').decode('utf-8')
            self.assertIn('word/header1.xml', names)
            self.assertIn('word/footer1.xml', names)
            self.assertIn('word/numbering.xml', names)
            self.assertIn('word/media/image1.png', names)
            self.assertIn('w:type="page"', document)

    def test_modern_fixture_contains_modern_wrappers_and_sections(self):
        with ZipFile(FIX / 'era3_office_2016_365_modern.docx') as z:
            document=z.read('word/document.xml').decode('utf-8')
            self.assertIn('<w:sdt>', document)
            self.assertIn('<w:ins ', document)
            self.assertIn('w:orient="landscape"', document)

    def test_writer_uses_original_package(self):
        writer=(ROOT/'apps/documents/docx-writer.js').read_text(encoding='utf-8')
        parser=(ROOT/'apps/documents/docx-parser.js').read_text(encoding='utf-8')
        self.assertIn('JSZip.loadAsync(sourceBuffer)', writer)
        self.assertIn('renderedSourceIndexes', parser)
        self.assertIn('content-control-block', parser)
        self.assertIn('tracked-insert', parser)

if __name__ == '__main__':
    unittest.main()
