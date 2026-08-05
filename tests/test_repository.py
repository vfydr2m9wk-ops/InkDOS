from pathlib import Path
import json
import re
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


class RepositoryTests(unittest.TestCase):
    def test_retired_runtime_gate(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/check_no_legacy_runtime.py')],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_version_consistency(self):
        version = json.loads((ROOT / 'VERSION.json').read_text())['version']
        self.assertEqual(version, json.loads((ROOT / 'package.json').read_text())['version'])
        self.assertEqual(version, json.loads((ROOT / 'app-manifest.json').read_text())['version'])
        self.assertIn(version, (ROOT / 'service-worker.js').read_text())

    def test_all_workspace_routes(self):
        router = (ROOT / 'shared/file-router.js').read_text()
        for extension, route in {
            'docx': './apps/documents/index.html',
            'xls': './apps/spreadsheets/index.html',
            'xlsx': './apps/spreadsheets/index.html',
            'pptx': './apps/presentations/index.html',
            'pdf': './apps/pdf/index.html',
        }.items():
            self.assertRegex(router, rf"{extension}:\s*'{re.escape(route)}'")
            self.assertTrue((ROOT / route.removeprefix('./')).is_file())

    def test_pdf_is_in_service_worker_shell(self):
        service_worker = (ROOT / 'service-worker.js').read_text()
        for path in ('./PDF.html', './assets/icons/pdf.png', './apps/pdf/index.html', './apps/pdf/styles.css', './apps/pdf/app.js', './shared/vendor/pdfjs/pdf.min.js', './shared/vendor/pdfjs/pdf.worker.min.js'):
            self.assertIn(repr(path), service_worker)

    def test_only_synthetic_fixtures_are_bundled(self):
        expected = {
            'inkdesk-letterhead-a4.docx',
            'inkdesk-letterhead-a4-bom.docx',
            'inkdesk-prescription-a4.xls',
            'inkdesk-prescription-a4.xlsx',
            'inkdesk-presentation-layout.pptx',
            'inkdesk-pdf-sample.pdf',
            'inkdesk-pdf-long-4000-pages.pdf',
        }
        self.assertEqual({p.name.lower() for p in FIXTURES.iterdir() if p.is_file()}, expected)

    def test_fixture_packages_have_required_parts(self):
        required = {
            'inkdesk-letterhead-a4.docx': ('word/document.xml', 'docProps/core.xml'),
            'inkdesk-letterhead-a4-bom.docx': ('word/document.xml', 'docProps/core.xml'),
            'inkdesk-prescription-a4.xlsx': ('xl/workbook.xml',),
            'inkdesk-presentation-layout.pptx': ('ppt/presentation.xml', 'docProps/core.xml'),
        }
        for name, parts in required.items():
            with self.subTest(name=name), zipfile.ZipFile(FIXTURES / name) as archive:
                for part in parts:
                    self.assertIn(part, archive.namelist())

    def test_ooxml_fixture_metadata_is_generic(self):
        for path in (FIXTURES / 'inkdesk-letterhead-a4.docx', FIXTURES / 'inkdesk-letterhead-a4-bom.docx', FIXTURES / 'inkdesk-prescription-a4.xlsx', FIXTURES / 'inkdesk-presentation-layout.pptx'):
            with self.subTest(path=path.name), zipfile.ZipFile(path) as archive:
                if 'docProps/core.xml' not in archive.namelist():
                    continue
                core = archive.read('docProps/core.xml').decode('utf-8', 'replace')
                creators = re.findall(r'<dc:creator>(.*?)</dc:creator>|<cp:lastModifiedBy>(.*?)</cp:lastModifiedBy>', core, re.S)
                values = [value.strip() for pair in creators for value in pair if value.strip()]
                self.assertTrue(values)
                self.assertTrue(all(value == 'InkDesk QA' for value in values), values)
                self.assertNotRegex(core, r'(?i)(/(?:home|mnt)/[^<]+|[A-Z]:\\[^\\]+\\)')

    def test_direct_slide_background_fixture(self):
        with zipfile.ZipFile(FIXTURES / 'inkdesk-presentation-layout.pptx') as archive:
            xml = archive.read('ppt/slides/slide1.xml').decode()
            self.assertIn('<p:bg>', xml)
            self.assertIn('<a:blipFill', xml)

    def test_biff8_hidden_zero_option_is_supported(self):
        source = (ROOT / 'apps/spreadsheets/xls-biff8-engine.js').read_text()
        app = (ROOT / 'apps/spreadsheets/app.js').read_text()
        self.assertIn('r.type===0x023E', source)
        self.assertIn('showZeros=!!(options&0x0010)', source)
        self.assertIn('targetSheet?.showZeros===false', app)

    def test_pdf_workspace_controls_and_selector(self):
        root_html = (ROOT / 'index.html').read_text()
        pdf_html = (ROOT / 'apps' / 'pdf' / 'index.html').read_text()
        pdf_js = (ROOT / 'apps' / 'pdf' / 'app.js').read_text()
        self.assertRegex(root_html, r'id="openAnyInput"[^>]+(?:\.pdf|application/pdf)')
        for element_id in ('pdfPages', 'pageList', 'outlineList', 'bookmarkBtn', 'fullscreenBtn', 'immersiveExit', 'pageNumber', 'verticalScroll', 'horizontalScroll', 'saveModifiedPdfBtn'):
            self.assertIn(f'id="{element_id}"', pdf_html)
        for feature in ('highlight', 'underline', 'marker', 'comment', 'text'):
            self.assertIn(f'data-tool="{feature}"', pdf_html)
        for zoom in ('50', '100', '200', '300', '400'):
            self.assertIn(f'<option value="{zoom}">{zoom}%</option>', pdf_html)
        self.assertNotIn('id="pdfEmbed"', pdf_html)
        self.assertNotIn('page-thumb-object', pdf_html + pdf_js)
        self.assertIn("inkdesk.pdf.review.", pdf_js)
        self.assertIn("schema:'inkdesk-pdf-review/2'", pdf_js)
        self.assertIn('CACHE_RADIUS=2', pdf_js)
        self.assertIn('pdfjsLib.renderTextLayer', pdf_js)
        self.assertIn('new pdfjsLib.AnnotationLayer', pdf_js)
        self.assertIn('state.doc.saveDocument()', pdf_js)
        self.assertIn('record.page?.cleanup?.()', pdf_js)
        self.assertIn('canvas.width=0', pdf_js)
        self.assertNotIn("document.createElement('object')", pdf_js)
        self.assertNotIn("document.createElement('embed')", pdf_js)
        self.assertNotIn("document.createElement('iframe')", pdf_js)
        self.assertTrue((ROOT / 'shared/vendor/pdfjs/pdf.min.js').is_file())
        self.assertTrue((ROOT / 'shared/vendor/pdfjs/pdf.worker.min.js').is_file())
        self.assertNotIn('type="module"', pdf_html)

    def test_spreadsheet_drag_formula_suggestions_and_excel_shortcuts(self):
        html = (ROOT / 'apps/spreadsheets/index.html').read_text()
        app = (ROOT / 'apps/spreadsheets/app.js').read_text()
        self.assertIn('id="formulaSuggestions"', html)
        for fn in ('SUM', 'XLOOKUP', 'IFERROR', 'MEDIAN', 'TODAY'):
            self.assertIn("['" + fn + "'", app)
        self.assertIn("window.addEventListener('pointermove'", app)
        self.assertIn("e.key==='F2'", app)
        self.assertIn("key==='z'", app)
        self.assertIn("if(ch==='=')", app)

    def test_presentations_show_determinate_opening_progress(self):
        html = (ROOT / 'apps/presentations/index.html').read_text()
        app = (ROOT / 'apps/presentations/app.js').read_text()
        self.assertIn('id="presentationLoading"', html)
        self.assertIn('role="progressbar"', html)
        self.assertIn('readPresentationFile(file)', app)
        self.assertIn('Opening slide ${i+1} of ${ids.length}', app)
        self.assertIn('setPresentationProgress(97', app)

    def test_pdf_fixture_has_forms_outline_and_generic_metadata(self):
        from pypdf import PdfReader
        reader = PdfReader(FIXTURES / 'inkdesk-pdf-sample.pdf')
        self.assertEqual(len(reader.pages), 3)
        self.assertGreaterEqual(len(reader.get_fields() or {}), 4)
        self.assertGreaterEqual(len(reader.outline or []), 3)
        metadata = reader.metadata or {}
        for key in ('/Author', '/Creator', '/Producer'):
            self.assertEqual(metadata.get(key), 'InkDesk QA')
        metadata_text = ' '.join(str(v) for v in metadata.values())
        self.assertNotRegex(metadata_text, r'(?i)(/(?:home|mnt)/|[A-Z]:\\|@|patient|clinic)')

    def test_long_pdf_fixture_is_synthetic_and_has_4000_pages(self):
        from pypdf import PdfReader
        reader = PdfReader(FIXTURES / 'inkdesk-pdf-long-4000-pages.pdf')
        self.assertEqual(len(reader.pages), 4000)
        metadata = reader.metadata or {}
        for key in ('/Author', '/Creator', '/Producer'):
            self.assertEqual(metadata.get(key), 'InkDesk QA')
        metadata_text = ' '.join(str(v) for v in metadata.values())
        self.assertNotRegex(metadata_text, r'(?i)(/(?:home|mnt)/|[A-Z]:\\|@|patient|clinic)')

    def test_docx_bom_fixture_is_bom_encoded(self):
        with zipfile.ZipFile(FIXTURES / 'inkdesk-letterhead-a4-bom.docx') as archive:
            for name in ('word/document.xml', 'word/styles.xml', 'word/_rels/document.xml.rels'):
                self.assertTrue(archive.read(name).startswith(b'\xef\xbb\xbf'), name)
        runtime = (ROOT / 'shared' / 'office-runtime.js').read_text()
        parser = (ROOT / 'apps' / 'documents' / 'docx-parser.js').read_text()
        self.assertIn("replace(/^\\uFEFF/", runtime)
        self.assertIn("normalize('NFC')", parser)

    def test_repository_images_have_no_text_metadata(self):
        from PIL import Image
        for path in (ROOT / 'docs' / 'images').glob('*.png'):
            with self.subTest(path=path.name), Image.open(path) as image:
                self.assertFalse(set(image.info) - {'dpi', 'transparency', 'srgb', 'gamma'})

    def test_no_stale_release_images(self):
        names = {p.name for p in (ROOT / 'docs' / 'images').iterdir() if p.is_file()}
        self.assertFalse(any('0.18.5' in name or 'validation-contact-sheet' in name for name in names))


if __name__ == '__main__':
    unittest.main()
