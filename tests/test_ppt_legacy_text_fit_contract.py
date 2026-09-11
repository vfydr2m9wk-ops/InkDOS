from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "apps" / "presentations" / "ui" / "ppt-p1-tools.js"


class LegacyPptTextFitContractTests(unittest.TestCase):
    def test_fit_is_scoped_to_read_only_legacy_ppt_text(self):
        source = TOOLS.read_text(encoding="utf-8")
        self.assertIn("session.sourceKind!=='ppt'", source)
        self.assertIn("startsWith('ppt-legacy')", source)
        self.assertIn("fitLegacyText", source)
        self.assertIn("scheduleLegacyTextFit", source)

    def test_fit_uses_measured_overflow_and_bounded_scaling(self):
        source = TOOLS.read_text(encoding="utf-8")
        self.assertIn("content.scrollHeight<=innerH+1", source)
        self.assertIn("content.scrollWidth<=innerW+1", source)
        self.assertIn("Math.max(.55", source)
        self.assertIn("content.style.transform=`scale(${scale})`", source)
        self.assertIn("content.style.width=(100/scale)+'%'", source)

    def test_fit_is_render_only_and_preserves_legacy_model(self):
        source = TOOLS.read_text(encoding="utf-8")
        fit = source[source.index("function fitLegacyText") : source.index("function colorControl")]
        self.assertNotIn("object.fontSizePt=", fit)
        self.assertNotIn("object.w=", fit)
        self.assertNotIn("object.h=", fit)
        self.assertNotIn("session.markDirty", fit)
        self.assertIn("dataset.legacyTextFit", fit)

    def test_fit_reacts_to_viewport_resize_without_mutating_model(self):
        source = TOOLS.read_text(encoding="utf-8")
        install = source[source.index("function install") : source.index("return Object.freeze")]
        self.assertIn("addEventListener('resize',scheduleLegacyTextFit", install)
        self.assertNotIn("session.markDirty", install)


if __name__ == "__main__":
    unittest.main()
