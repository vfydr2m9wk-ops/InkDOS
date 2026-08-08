from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.20.3.1"
CSS = ROOT / "shared" / "ui" / "visual-foundation-v0203.css"


class VisualFoundation0203Tests(unittest.TestCase):
    def test_shared_visual_layer_exists_and_is_bounded(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 500)
        self.assertIn("--ink-titlebar-height:44px", text)
        self.assertIn("prefers-reduced-motion:reduce", text)
        self.assertIn("pointer:coarse", text)

    def test_all_entry_points_load_visual_layer(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(f"./shared/ui/visual-foundation-v0203.css?v={VERSION}", home)
        shell = (ROOT / "shared/office-shell.js").read_text(encoding="utf-8")
        legacy = shell.index("addStylesheet('visual-foundation.css')")
        overlay = shell.index("addStylesheet('visual-foundation-v0203.css')")
        self.assertLess(legacy, overlay)
        for relative in (
            "apps/documents/index.html",
            "apps/spreadsheets/index.html",
            "apps/presentations/index.html",
            "apps/pdf/index.html",
            "apps/txt/index.html",
            "apps/epub/index.html",
        ):
            html = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(f"../../shared/office-shell.js?v={VERSION}", html, relative)

    def test_product_color_identities_are_preserved(self):
        text = CSS.read_text(encoding="utf-8")
        expected = {
            "office-documents": "#2f6fed",
            "office-spreadsheets": "#267a45",
            "office-presentations": "#d64a24",
            "office-pdf": "#b42318",
            "office-txt": "#d9a514",
            "office-epub": "#7655c7",
        }
        for klass, color in expected.items():
            self.assertIn(f"body.{klass}{{--ink-accent:{color}}}", text)

    def test_home_has_desktop_tablet_and_phone_layouts(self):
        text = CSS.read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:repeat(3,minmax(0,1fr))", text)
        self.assertIn("@media(max-width:860px)", text)
        self.assertIn("@media(max-width:620px)", text)
        self.assertIn(".workspace-grid{grid-template-columns:1fr", text)

    def test_service_worker_precaches_visual_layer(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("inkdesk-shell-v" + VERSION, worker)
        self.assertIn("./shared/ui/visual-foundation-v0203.css", worker)

    def test_visual_layer_does_not_define_data_or_editor_logic(self):
        text = CSS.read_text(encoding="utf-8").lower()
        for forbidden in ("indexeddb", "localstorage", "fetch(", "formulaengine", "undostack"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
