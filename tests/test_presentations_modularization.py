from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/presentations/app.js"
UI = ROOT / "apps/presentations/ui"
INSPECTOR = UI / "inspector-controller.js"
THUMBNAILS = UI / "thumbnails-controller.js"
NOTES = UI / "presenter-notes-controller.js"
HTML = ROOT / "apps/presentations/index.html"
WORKER = ROOT / "service-worker.js"


class PresentationsModularizationTests(unittest.TestCase):
    def test_feature_components_load_before_app(self):
        html = HTML.read_text(encoding="utf-8")
        components = (
            "ui/inspector-controller.js?v=0.20.2.4",
            "ui/thumbnails-controller.js?v=0.20.2.4",
            "ui/presenter-notes-controller.js?v=0.20.2.4",
        )
        app = "app.js?v=0.20.2.4"
        for component in components:
            self.assertIn(component, html)
            self.assertLess(html.index(component), html.index(app))

    def test_extracted_components_are_readable_and_within_new_source_limits(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        for path in (INSPECTOR, THUMBNAILS, NOTES):
            self.assertTrue(path.is_file(), path)
            source = path.read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(source), policy["extensions"][".js"]["newFileMaxLines"], path)
            long_lines = [
                line for line in source
                if len(line) > policy["extensions"][".js"]["maxPhysicalLineLength"]
            ]
            self.assertEqual(long_lines, [], path)
            self.assertNotIn(str(path.relative_to(ROOT)), policy["grandfatheredDebt"])

    def test_app_delegates_extracted_ui_behavior(self):
        app = APP.read_text(encoding="utf-8")
        inspector = INSPECTOR.read_text(encoding="utf-8")
        thumbnails = THUMBNAILS.read_text(encoding="utf-8")
        notes = NOTES.read_text(encoding="utf-8")

        self.assertIn("InkDeskPresentationsInspector.create", app)
        self.assertIn("InkDeskPresentationsThumbnails.create", app)
        self.assertIn("InkDeskPresentationsNotes.create", app)
        self.assertIn("class PresentationInspectorController", inspector)
        self.assertIn("class PresentationThumbnailsController", thumbnails)
        self.assertIn("class PresentationNotesController", notes)

        self.assertNotIn("const COLORS=[", app)
        self.assertNotIn("let inspectorOpen=false", app)
        self.assertNotIn("compactInspectorQuery", app)
        self.assertNotIn("function renderMini(", app)
        self.assertNotIn("ui.notes.addEventListener('input'", app)
        self.assertNotIn("$('togglePresentationsBtn').onclick", app)
        self.assertNotIn("$('toggleNotesBtn').onclick", app)

    def test_presentations_app_ratchet_moves_down_after_second_extraction(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        debt = policy["grandfatheredDebt"]["apps/presentations/app.js"]
        lines = APP.read_text(encoding="utf-8").splitlines()
        self.assertEqual(debt["maxLines"], len(lines))
        self.assertLess(debt["maxLines"], 883)
        self.assertLess(debt["maxLongLines"], 93)

    def test_offline_shell_precaches_every_extracted_component(self):
        worker = WORKER.read_text(encoding="utf-8")
        for component in (
            "./apps/presentations/ui/inspector-controller.js",
            "./apps/presentations/ui/thumbnails-controller.js",
            "./apps/presentations/ui/presenter-notes-controller.js",
        ):
            self.assertIn(component, worker)

    def test_manual_browser_harnesses_load_components_before_presentations_app(self):
        paths = (
            "tests/browser/revalidate_v0201_consistency.py",
            "tests/browser/revalidate_pptx_three_eras.py",
            "tests/browser/revalidate_cross_workspace_isolation.py",
            "tests/browser/revalidate_transactional_open_failures.py",
            "tests/browser/revalidate_launch_and_offline_modes.py",
        )
        components = (
            "apps/presentations/ui/inspector-controller.js",
            "apps/presentations/ui/thumbnails-controller.js",
            "apps/presentations/ui/presenter-notes-controller.js",
        )
        app = "apps/presentations/app.js"
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for component in components:
                self.assertIn(component, text, relative)
                self.assertLess(text.index(component), text.index(app), relative)


if __name__ == "__main__":
    unittest.main()
