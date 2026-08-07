from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
MODULES = ("documents", "spreadsheets", "presentations", "pdf", "txt", "epub")
DYNAMIC_IDS = {
    "documents": {"loadingOverlay", "newDocumentPanel", "openErrorPanel", "saveReadyPanel"},
    # Fullscreen controls are optional: presentation mode still works when a
    # web view does not expose a dedicated Fullscreen API control.
    "presentations": {"fullscreenPresentBtn", "fullscreenPresentLabel"},
}


class InteractiveDomContractTests(unittest.TestCase):
    def test_workspace_html_has_no_duplicate_ids(self):
        for module in MODULES:
            path = ROOT / "apps" / module / "index.html"
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            ids = [node["id"] for node in soup.find_all(attrs={"id": True})]
            duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
            self.assertEqual(duplicates, [], f"{module}: duplicate DOM ids {duplicates}")

    def test_direct_app_id_references_resolve_or_are_intentionally_dynamic(self):
        pattern = re.compile(r"\$\(['\"]([^'\"]+)['\"]\)")
        for module in MODULES:
            html_path = ROOT / "apps" / module / "index.html"
            app_path = ROOT / "apps" / module / "app.js"
            soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
            html_ids = {node["id"] for node in soup.find_all(attrs={"id": True})}
            references = set(pattern.findall(app_path.read_text(encoding="utf-8")))
            unresolved = sorted(references - html_ids - DYNAMIC_IDS.get(module, set()))
            self.assertEqual(unresolved, [], f"{module}: unresolved direct DOM references {unresolved}")

    def test_presentations_inspector_state_is_not_split_between_click_paths(self):
        app = (ROOT / "apps/presentations/app.js").read_text(encoding="utf-8")
        component = (
            ROOT / "apps/presentations/ui/inspector-controller.js"
        ).read_text(encoding="utf-8")
        self.assertIn("InkDeskPresentationsInspector.create", app)
        self.assertIn("this.open = false", component)
        self.assertIn("this.setOpen(!this.open)", component)
        self.assertNotIn("classList.toggle('inspector-open');", app + component)
        self.assertNotIn("classList.toggle('hide-inspector');", app + component)

    def test_presentations_inspector_component_ids_exist_in_workspace_html(self):
        html_path = ROOT / "apps/presentations/index.html"
        component_path = ROOT / "apps/presentations/ui/inspector-controller.js"
        soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
        html_ids = {node["id"] for node in soup.find_all(attrs={"id": True})}
        component = component_path.read_text(encoding="utf-8")
        references = set(re.findall(r"byId\('([^']+)'\)", component))
        unresolved = sorted(references - html_ids)
        self.assertEqual(unresolved, [], f"presentations inspector: unresolved ids {unresolved}")


if __name__ == "__main__":
    unittest.main()
