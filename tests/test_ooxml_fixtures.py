from pathlib import Path
from zipfile import ZipFile
import unittest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class OOXMLFixtureTests(unittest.TestCase):
    def assert_parts(self, name, required):
        with ZipFile(FIXTURES / name) as archive:
            names = set(archive.namelist())
            for part in required:
                self.assertIn(part, names, f"{name}: {part}")
            self.assertIn("[Content_Types].xml", names)
            self.assertIn("_rels/.rels", names)

    def test_docx(self):
        self.assert_parts("minimal.docx", {"word/document.xml"})

    def test_numbered_docx(self):
        self.assert_parts("numbered-list.docx", {"word/document.xml", "word/numbering.xml", "word/_rels/document.xml.rels"})

    def test_xlsx(self):
        self.assert_parts("minimal.xlsx", {"xl/workbook.xml", "xl/worksheets/sheet1.xml"})

    def test_pptx(self):
        self.assert_parts("minimal.pptx", {"ppt/presentation.xml", "ppt/slides/slide1.xml"})


if __name__ == "__main__":
    unittest.main()
