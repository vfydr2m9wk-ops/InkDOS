from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HubLayoutTests(unittest.TestCase):
    def test_information_panel_uses_three_equal_columns_without_empty_cell(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "shared" / "hub.css").read_text(encoding="utf-8")

        self.assertEqual(html.count('class="quick-panel"'), 1)
        self.assertEqual(html.count("<div><strong>Local by default"), 1)
        self.assertEqual(html.count("<div><strong>Export verification"), 1)
        self.assertEqual(html.count("<div><strong>Contributions welcome"), 1)
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", css)
        self.assertIn("@media(max-width:860px){.quick-panel{grid-template-columns:1fr}}", css)


if __name__ == "__main__":
    unittest.main()
