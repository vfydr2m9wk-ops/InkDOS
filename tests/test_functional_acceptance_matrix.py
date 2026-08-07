from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "FUNCTIONAL_ACCEPTANCE_MATRIX.json"
SOURCES = [("home", "index.html")] + [
    (name, f"apps/{name}/index.html")
    for name in ("documents", "spreadsheets", "presentations", "pdf", "txt", "epub")
]


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "control"


def label_for(element) -> str:
    for attr in ("aria-label", "title"):
        if element.get(attr):
            return " ".join(str(element.get(attr)).split())
    text = " ".join(element.stripped_strings)
    if text:
        return text
    if element.get("id"):
        return element["id"]
    if element.get("for"):
        return "Open/select " + element["for"]
    return element.name


def signature_for(element, index: int) -> str:
    if element.get("id"):
        return "#" + element["id"]
    for attr in ("data-cmd", "data-panel", "data-tab", "data-tool", "data-theme"):
        if element.get(attr):
            return f'[{attr}="{element[attr]}"]'
    if element.name == "label" and element.get("for"):
        return f'label[for="{element["for"]}"]'
    if element.name == "a" and element.get("href"):
        return f'a[href="{element["href"]}"]#{index}'
    return f"{element.name}:{norm(label_for(element))}#{index}"


def current_controls() -> list[dict]:
    result = []
    for module, relative in SOURCES:
        soup = BeautifulSoup((ROOT / relative).read_text(encoding="utf-8"), "html.parser")
        candidates = []
        for element in soup.find_all(["button", "a", "input", "select", "textarea", "label"]):
            if element.name == "label" and not element.get("for"):
                continue
            if element.name == "input" and element.get("type") in {"hidden", "file"}:
                continue
            if element.get("hidden") is not None:
                continue
            candidates.append(element)
        seen: dict[str, int] = {}
        for element in candidates:
            base = signature_for(element, 0)
            seen[base] = seen.get(base, 0) + 1
            if base.startswith('a[href=') or ("#" in base and not base.startswith("#")):
                selector = signature_for(element, seen[base])
            else:
                selector = base
            result.append({
                "module": module,
                "source": relative,
                "selector": selector,
                "label": label_for(element),
                "element": element.name,
            })
    return result


class FunctionalAcceptanceMatrixTests(unittest.TestCase):
    def setUp(self):
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_every_visible_control_is_inventoried(self):
        expected = [
            {key: item[key] for key in ("module", "source", "selector", "label", "element")}
            for item in self.matrix["controls"]
        ]
        self.assertEqual(current_controls(), expected)

    def test_control_keys_are_unique(self):
        keys = [item["key"] for item in self.matrix["controls"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_coverage_state_is_explicit(self):
        allowed = {"automated", "manual", "scheduled"}
        for item in self.matrix["controls"] + self.matrix["capabilities"]:
            self.assertIn(item["coverage"], allowed, item.get("key"))
            if item["coverage"] in {"automated", "manual"}:
                self.assertTrue(item.get("evidence"), item.get("key"))

    def test_required_modules_are_present(self):
        present = {item["module"] for item in self.matrix["controls"]}
        self.assertEqual(present, {module for module, _ in SOURCES})

    def test_presentations_format_panel_has_behavioral_evidence(self):
        capability = next(item for item in self.matrix["capabilities"] if item["key"] == "presentations.format-panel-responsive")
        self.assertEqual(capability["coverage"], "automated")
        self.assertIn("tests/browser/revalidate_presentations_controls.py", capability["evidence"])


if __name__ == "__main__":
    unittest.main()
