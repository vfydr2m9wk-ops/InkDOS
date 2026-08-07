from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PresentationsResponsiveControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / "apps/presentations/styles.css").read_text(encoding="utf-8")
        cls.app = (ROOT / "apps/presentations/app.js").read_text(encoding="utf-8")
        cls.inspector = (
            ROOT / "apps/presentations/ui/inspector-controller.js"
        ).read_text(encoding="utf-8")
        cls.html = (ROOT / "apps/presentations/index.html").read_text(encoding="utf-8")
        cls.recovery_test = (
            ROOT / "tests/browser/revalidate_v0202_local_recovery.py"
        ).read_text(encoding="utf-8")
        cls.shell_css = (ROOT / "shared/office-shell.css").read_text(encoding="utf-8")

    def test_compact_layout_overrides_legacy_hidden_inspector(self):
        marker = "/* 0.20.2 responsive format-panel drawer */"
        self.assertIn(marker, self.css)
        tail = self.css.split(marker, 1)[1]
        self.assertIn("display:block!important", tail)
        self.assertIn(".workspace.inspector-open .inspector", tail)
        self.assertIn("visibility:visible!important", tail)

    def test_legacy_compact_display_none_rule_is_removed(self):
        self.assertNotIn(".inspector{display:none}", self.css)

    def test_shared_shell_finishes_the_presentations_drawer_cascade(self):
        marker = "/* 0.20.2 presentations format-panel cascade guard"
        self.assertIn(marker, self.shell_css)
        tail = self.shell_css.split(marker, 1)[1]
        self.assertIn("@media (min-width:1001px)", tail)
        self.assertIn("position:relative!important", tail)
        self.assertIn("@media (max-width:1000px)", tail)
        self.assertIn("position:fixed!important", tail)
        self.assertIn(".workspace.inspector-open .inspector", tail)
        self.assertIn("visibility:visible!important", tail)

    def test_shell_is_loaded_after_product_styles_and_owns_final_cascade(self):
        product_pos = self.html.index('href="styles.css"')
        shell_pos = self.html.index('href="../../shared/office-shell.css"')
        self.assertLess(product_pos, shell_pos)
        self.assertIn("presentations format-panel cascade guard", self.shell_css)

    def test_format_panel_uses_one_boolean_source_of_truth_at_all_widths(self):
        self.assertIn("matchMedia('(max-width:1000px)')", self.inspector)
        self.assertIn("this.open = false", self.inspector)
        self.assertIn("applyOpenState()", self.inspector)
        self.assertIn("setOpen(open, options = {})", self.inspector)
        self.assertIn("classList.toggle('inspector-open', this.open)", self.inspector)
        self.assertIn("classList.toggle('hide-inspector', !this.open)", self.inspector)
        self.assertIn("dataset.inspectorOpen = String(this.open)", self.inspector)
        self.assertNotIn("lastInspectorCompactMode", self.inspector)
        self.assertNotIn("inspectorResizeFrame", self.inspector)
        self.assertIn("InkDeskPresentationsInspector.create", self.app)

    def test_format_toggle_exposes_accessibility_state_from_same_source(self):
        self.assertIn('aria-controls="inspector"', self.html)
        self.assertIn("setAttribute('aria-expanded', String(this.open))", self.inspector)
        self.assertIn("'Hide format panel'", self.inspector)
        self.assertIn("'Show format panel'", self.inspector)

    def test_escape_closes_compact_format_panel_through_state_api(self):
        self.assertIn("event.key === 'Escape'", self.inspector)
        self.assertIn("this.isCompact() && this.open", self.inspector)
        self.assertIn("this.setOpen(false)", self.inspector)

    def test_recovery_test_does_not_depend_on_notes_visibility(self):
        self.assertIn("node.value=value", self.recovery_test)
        self.assertNotIn('page.fill("#presenterNotes", token)', self.recovery_test)

    def test_behavioral_control_regression_is_registered(self):
        runner = (ROOT / "scripts/run_browser_regressions.py").read_text(encoding="utf-8")
        self.assertIn('"revalidate_presentations_controls.py"', runner)

    def test_optional_presentation_panels_start_closed_and_reset_on_open(self):
        self.assertIn('class="app hidden hide-notes"', self.html)
        self.assertIn('class="workspace hide-inspector"', self.html)
        self.assertIn('aria-expanded="false">Show format panel', self.html)
        self.assertIn('>Show presenter notes</button>', self.html)
        self.assertIn("function resetOptionalPanelsForOpen()", self.app)
        self.assertIn("setInspectorOpen(false,{relayout:false})", self.app)
        self.assertIn("ui.app.classList.add('hide-notes')", self.app)
        self.assertIn("resetOptionalPanelsForOpen()", self.app)

    def test_compact_cold_start_starts_closed_then_uses_canonical_open_class(self):
        browser = (
            ROOT / "tests/browser/revalidate_presentations_controls.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Real iPad/mobile cold start", browser)
        self.assertIn("Compact cold start retained the desktop hide class", browser)
        self.assertIn("classList.toggle('hide-inspector', !this.open)", self.inspector)

    def test_breakpoint_change_is_css_only_and_cannot_race_js_state(self):
        combined = self.app + self.inspector
        self.assertNotIn("reconcileInspectorViewport", combined)
        self.assertNotIn("scheduleInspectorViewportSync", combined)
        self.assertNotIn("lastInspectorCompactMode", combined)
        self.assertNotIn("inspectorResizeFrame", combined)
        browser = (
            ROOT / "tests/browser/revalidate_presentations_controls.py"
        ).read_text(encoding="utf-8")
        self.assertIn("did not remain open as a compact drawer", browser)
        self.assertIn("did not close the drawer", browser)
        self.assertIn("did not reopen the drawer", browser)

    def test_behavioral_format_test_starts_from_collapsed_product_state(self):
        browser = (
            ROOT / "tests/browser/revalidate_presentations_controls.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Format panel should start collapsed in the desktop layout", browser)
        self.assertIn("Show format panel did not open the desktop inspector", browser)
        self.assertIn('wait_toggle_state(page, False', browser)
        self.assertIn('wait_toggle_state(page, True', browser)


if __name__ == "__main__":
    unittest.main()
