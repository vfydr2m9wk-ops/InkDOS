import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class DocxOnOffContractTests(unittest.TestCase):
    def test_docx_onoff_properties_respect_explicit_false_values(self):
        parser = read("apps/documents/engine/docx-parser.js")
        self.assertIn("function onOff(", parser)
        self.assertIn("['0','false','off','no'].includes", parser)
        self.assertIn("if(onOff(first(pPr,'pageBreakBefore')))out.pageBreakBefore=true;", parser)
        self.assertIn("if(onOff(first(pPr,'keepNext')))out.keepNext=true;", parser)


if __name__ == "__main__":
    unittest.main()
