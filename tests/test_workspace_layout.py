from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceLayoutTests(unittest.TestCase):
    def test_layout_files_exist(self):
        for relative in (
            "shared/ui/workspace-layout.css",
            "shared/ui/workspace-layout.js",
            "docs/VISUAL_SYSTEM.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_bootstrap_loads_layout_assets(self):
        bootstrap = (ROOT / "shared" / "office-shell.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("workspace-layout.css", bootstrap)
        self.assertIn("workspace-layout.js", bootstrap)
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(encoding="utf-8")
        )
        expected = manifest["uiSystem"]["workspaceLayout"]["version"]
        self.assertEqual(expected, "0.20.0")
        self.assertIn("function loadWorkspaceLayout()", bootstrap)

    def test_default_panel_contract(self):
        runtime = (ROOT / "shared" / "ui" / "workspace-panel-controller.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("documents: Object.freeze", runtime)
        self.assertIn("sidebar: false", runtime)
        self.assertIn("thumbnails: true", runtime)
        self.assertIn("inspector: false", runtime)
        self.assertIn("notes: false", runtime)
        self.assertIn("sidebar-hidden", runtime)
        self.assertIn("hide-inspector", runtime)
        self.assertIn("hide-notes", runtime)

    def test_pdf_primary_action_is_centered(self):
        styles = (ROOT / "shared" / "ui" / "workspace-layout.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("body.office-pdf .start-actions", styles)
        self.assertIn("justify-content: center !important", styles)
        self.assertIn("body.office-pdf .start-btn", styles)
        self.assertIn("margin-inline: auto !important", styles)

    def test_spreadsheet_formula_and_status_positions_are_preserved(self):
        styles = (ROOT / "shared" / "ui" / "workspace-layout.css").read_text(
            encoding="utf-8"
        )
        self.assertIn("body.office-spreadsheets .formula-row", styles)
        self.assertIn("body.office-spreadsheets .zoom-controls", styles)
        self.assertIn("margin-left: auto", styles)

    def test_service_worker_caches_layout_assets(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("'./shared/ui/workspace-layout.css'", worker)
        self.assertIn("'./shared/ui/workspace-layout.js'", worker)
        self.assertIn("'./shared/ui/workspace-panel-controller.js'", worker)
        self.assertRegex(
            worker,
            r"const CACHE_NAME=['\"]inkdos-shell-v[^'\"]+['\"];",
        )

    def test_package_and_manifest_expose_visual_system(self):
        package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            package["scripts"]["test:layout"],
            "python3 -m unittest tests.test_workspace_layout",
        )

        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(encoding="utf-8")
        )
        visual = manifest["uiSystem"]["workspaceLayout"]
        self.assertEqual(visual["version"], "0.20.0")
        self.assertEqual(
            visual["stylesheet"],
            "shared/ui/workspace-layout.css",
        )
        self.assertEqual(
            visual["runtime"],
            "shared/ui/workspace-layout.js",
        )

    def test_javascript_runtime_exports_defaults(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = """
require('./shared/ui/workspace-layout.js');
const api = globalThis.InkDOSWorkspaceLayout;
if (!api) process.exit(10);
if (api.version !== '0.20.0') process.exit(11);
if (api.defaults.documents.sidebar !== false) process.exit(12);
if (api.defaults.presentations.thumbnails !== true) process.exit(13);
if (api.defaults.presentations.inspector !== false) process.exit(14);
if (api.defaults.presentations.notes !== false) process.exit(15);
if (api.defaults.pdf.sidebar !== false) process.exit(16);
"""

        result = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )


if __name__ == "__main__":
    unittest.main()
