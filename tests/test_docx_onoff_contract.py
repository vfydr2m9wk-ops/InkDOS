import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class DocxOnOffContractTests(unittest.TestCase):
    def test_docx_onoff_properties_respect_explicit_false_values(self):
        app = read("apps/documents/app.js")
        self.assertIn("function installDocxOnOffFix()", app)
        self.assertIn("['0','false','off','no'].includes", app)
        self.assertIn("block.hardPageBreakBefore=onOff(pageBreak)", app)
        self.assertIn("block.keepNext=onOff(keepNext)", app)
        self.assertIn("installDocxOnOffFix();", app)


if __name__ == "__main__":
    unittest.main()
