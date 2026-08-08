from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TxtInteractionModularizationTests(unittest.TestCase):
    def test_history_controller_owns_snapshot_history(self):
        controller = (ROOT / "apps/txt/history-controller.js").read_text(encoding="utf-8")
        app = (ROOT / "apps/txt/app.js").read_text(encoding="utf-8")
        for marker in (
            "history.length > 80",
            "setTimeout(push, 180)",
            "editor.setSelectionRange(item.start, item.end)",
            "global.InkDeskTxtHistoryController",
        ):
            self.assertIn(marker, controller)
        for marker in ("history.length > 80", "setTimeout(push, 180)"):
            self.assertNotIn(marker, app)
        self.assertIn("historyController.schedule()", app)
        self.assertIn("historyController.undo", app)
        self.assertIn("historyController.redo", app)

    def test_find_controller_owns_find_bar_interaction(self):
        controller = (ROOT / "apps/txt/find-controller.js").read_text(encoding="utf-8")
        app = (ROOT / "apps/txt/app.js").read_text(encoding="utf-8")
        for marker in (
            "source.lastIndexOf(needle",
            "source.indexOf(needle",
            "editor.setSelectionRange(index, index + query.length)",
            "global.InkDeskTxtFindController",
        ):
            self.assertIn(marker, controller)
        self.assertNotIn("source.lastIndexOf(needle", app)
        self.assertNotIn("source.indexOf(needle", app)
        self.assertIn("findController.show()", app)

    def test_txt_app_leaves_grandfathered_line_debt(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        self.assertNotIn("apps/txt/app.js", policy["grandfatheredDebt"])
        self.assertLessEqual(len((ROOT / "apps/txt/app.js").read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len((ROOT / "apps/txt/history-controller.js").read_text(encoding="utf-8").splitlines()), 500)
        self.assertLessEqual(len((ROOT / "apps/txt/find-controller.js").read_text(encoding="utf-8").splitlines()), 500)

    def test_txt_offline_and_load_order_include_controllers(self):
        html = (ROOT / "apps/txt/index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        history = "history-controller.js?v=0.20.2.26"
        find = "find-controller.js?v=0.20.2.26"
        app = "app.js?v=0.20.2.26"
        self.assertLess(html.index(history), html.index(app))
        self.assertLess(html.index(find), html.index(app))
        self.assertIn("'./apps/txt/history-controller.js'", worker)
        self.assertIn("'./apps/txt/find-controller.js'", worker)


if __name__ == "__main__":
    unittest.main()
