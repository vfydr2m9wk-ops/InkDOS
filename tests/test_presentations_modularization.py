from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/presentations/app.js"
INSPECTOR = ROOT / "apps/presentations/ui/inspector-controller.js"
HTML = ROOT / "apps/presentations/index.html"
WORKER = ROOT / "service-worker.js"


class PresentationsModularizationTests(unittest.TestCase):
    def test_inspector_is_a_real_feature_component_loaded_before_app(self):
        self.assertTrue(INSPECTOR.is_file())
        html = HTML.read_text(encoding="utf-8")
        component = 'ui/inspector-controller.js?v=0.20.2.3'
        app = 'app.js?v=0.20.2.3'
        self.assertIn(component, html)
        self.assertLess(html.index(component), html.index(app))

    def test_inspector_component_is_readable_and_within_new_source_limits(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        source = INSPECTOR.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(source), policy["extensions"][".js"]["newFileMaxLines"])
        long_lines = [
            line for line in source
            if len(line) > policy["extensions"][".js"]["maxPhysicalLineLength"]
        ]
        self.assertEqual(long_lines, [])
        self.assertNotIn(
            "apps/presentations/ui/inspector-controller.js",
            policy["grandfatheredDebt"],
        )

    def test_app_delegates_inspector_behavior_instead_of_reimplementing_it(self):
        app = APP.read_text(encoding="utf-8")
        component = INSPECTOR.read_text(encoding="utf-8")
        self.assertIn("InkDeskPresentationsInspector.create", app)
        self.assertIn("class PresentationInspectorController", component)
        self.assertIn("bindPropertyControls()", component)
        self.assertIn("bindPalette(options.colors || DEFAULT_COLORS)", component)
        self.assertNotIn("const COLORS=[", app)
        self.assertNotIn("let inspectorOpen=false", app)
        self.assertNotIn("compactInspectorQuery", app)

    def test_presentations_app_ratchet_moves_down_after_extraction(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        debt = policy["grandfatheredDebt"]["apps/presentations/app.js"]
        lines = APP.read_text(encoding="utf-8").splitlines()
        self.assertEqual(debt["maxLines"], len(lines))
        self.assertLess(debt["maxLines"], 886)
        self.assertLess(debt["maxLongLines"], 97)

    def test_offline_shell_precaches_extracted_inspector_component(self):
        worker = WORKER.read_text(encoding="utf-8")
        self.assertIn("'./apps/presentations/ui/inspector-controller.js'", worker)

    def test_manual_browser_harnesses_load_component_before_presentations_app(self):
        paths = (
            "tests/browser/revalidate_v0201_consistency.py",
            "tests/browser/revalidate_pptx_three_eras.py",
            "tests/browser/revalidate_cross_workspace_isolation.py",
            "tests/browser/revalidate_transactional_open_failures.py",
            "tests/browser/revalidate_launch_and_offline_modes.py",
        )
        component = "apps/presentations/ui/inspector-controller.js"
        app = "apps/presentations/app.js"
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(component, text, relative)
            self.assertLess(text.index(component), text.index(app), relative)


if __name__ == "__main__":
    unittest.main()
