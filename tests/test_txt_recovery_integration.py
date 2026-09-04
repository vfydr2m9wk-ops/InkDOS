from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TxtRecoveryIntegrationTests(unittest.TestCase):
    def test_recovery_is_current_and_open_confirmation_is_single_stage(self):
        html = (ROOT / "apps/txt/index.html").read_text(encoding="utf-8")
        app = (ROOT / "apps/txt/app.js").read_text(encoding="utf-8")
        controller = (ROOT / "apps/txt/recovery-controller.js").read_text(encoding="utf-8")

        recovery_asset = "../../shared/local-recovery.js?v=1.0.0-beta.4"
        controller_asset = "recovery-controller.js?v=1.0.0-beta.4"
        app_asset = "app.js?v=1.0.0-beta.4"
        self.assertIn(recovery_asset, html)
        self.assertIn(controller_asset, html)
        self.assertLess(html.index(recovery_asset), html.index(controller_asset))
        self.assertLess(html.index(controller_asset), html.index(app_asset))

        self.assertIn("global.InkDOSLocalRecovery.create", controller)
        self.assertIn("serialize: capture", controller)
        self.assertIn("restore,", controller)
        self.assertIn("manager.markDirty()", controller)
        self.assertIn("manager.flush()", controller)
        self.assertIn("global.InkDOSTxtRecoveryController", controller)
        self.assertIn("recovery.markDirty()", app)
        self.assertIn("await recovery.flush()", app)

        picker = app[app.index("function openPicker()") : app.index("function setWrap(")]
        self.assertNotIn("confirmDiscard()", picker)
        open_file = app[app.index("async function openFile(file)") : app.index("function encodeForSave()")]
        self.assertEqual(open_file.count("confirmDiscard()"), 1)

    def test_recovery_controller_is_small_and_offline(self):
        controller = ROOT / "apps/txt/recovery-controller.js"
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertLessEqual(len(controller.read_text(encoding="utf-8").splitlines()), 500)
        self.assertIn("'./apps/txt/recovery-controller.js'", worker)


if __name__ == "__main__":
    unittest.main()
