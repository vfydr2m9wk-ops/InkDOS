from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "apps" / "documents"


class LegacyDocImportContractTests(unittest.TestCase):
    def test_documents_loads_local_legacy_doc_reader(self):
        html = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn('src="io/legacy-doc-reader.js"', html)
        self.assertRegex(html, r'accept="[^"]*\.doc(?:,|\")')

    def test_open_controller_accepts_doc_as_read_only_import(self):
        source = (DOCS / "io" / "file-open-controller.js").read_text(encoding="utf-8")
        self.assertIn("isDoc=/\\.doc$/i.test(file.name)", source)
        self.assertIn("NS.LegacyDocReader", source)
        self.assertIn("kind:'doc'", source)
        self.assertIn("Save editable DOCX copy", source)

    def test_save_controller_promotes_only_after_confirmed_delivery(self):
        source = (DOCS / "io" / "save-controller.js").read_text(encoding="utf-8")
        self.assertIn("setPromoter", source)
        self.assertIn("promoteLegacy", source)
        self.assertIn("session.kind==='doc'", source)
        delivery_at = source.find("NS.FileDelivery.deliver")
        promotion_at = source.find("promoteLegacy", delivery_at)
        self.assertGreater(delivery_at, -1)
        self.assertGreater(promotion_at, delivery_at)

    def test_bootstrap_wires_doc_acceptance_and_canonical_promoter(self):
        source = (DOCS / "app.js").read_text(encoding="utf-8")
        self.assertIn(".doc,", source)
        self.assertIn("application/msword", source)
        self.assertIn("saveController.setPromoter?.(fileOpen.openFile)", source)

    def test_legacy_reader_is_present_and_sanitizes_xml_controls(self):
        reader = DOCS / "io" / "legacy-doc-reader.js"
        self.assertTrue(reader.is_file(), "legacy DOC reader must be local to Documents")
        source = reader.read_text(encoding="utf-8")
        self.assertIn("Invalid OLE compound file signature", source)
        self.assertRegex(source, r"\\x00-\\x08")
        self.assertNotIn("fetch(", source)
        self.assertNotIn("XMLHttpRequest", source)


if __name__ == "__main__":
    unittest.main()
