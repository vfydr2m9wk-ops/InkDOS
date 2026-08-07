from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TxtModuleTests(unittest.TestCase):
    def test_txt_module_assets_exist(self):
        for relative in (
            "apps/txt/module.json",
            "apps/txt/index.html",
            "apps/txt/styles.css",
            "apps/txt/app.js",
            "assets/icons/txt.svg",
            "assets/icons/txt.png",
            "docs/TXT_EDITOR.md",
            "TXT.html",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_manifest_is_enabled_optional_and_local(self):
        manifest = json.loads(
            (ROOT / "apps/txt/module.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["id"], "txt")
        self.assertTrue(manifest["enabled"])
        self.assertTrue(manifest["optional"])
        self.assertEqual(manifest["extensions"], ["txt"])
        self.assertIn("local-processing", manifest["capabilities"])
        self.assertIn(
            "unsaved-change-navigation-warning",
            manifest["capabilities"],
        )

    def test_workspace_has_simple_editor_actions(self):
        html = (ROOT / "apps/txt/index.html").read_text(
            encoding="utf-8"
        )
        for marker in (
            'id="newBtn"',
            'id="openBtn"',
            'id="saveBtn"',
            'id="docTitle"',
            'id="editor"',
            'id="findBar"',
            'id="wrapBtn"',
            'id="fontSize"',
            'id="lineCount"',
            'id="wordCount"',
            'id="characterCount"',
        ):
            self.assertIn(marker, html)

        self.assertIn(
            "../../shared/file-lifecycle.js?v=0.20.2.6",
            html,
        )
        self.assertIn(
            "../../shared/file-router.js?v=0.20.2.6",
            html,
        )

    def test_runtime_opens_saves_and_warns(self):
        script = (ROOT / "apps/txt/app.js").read_text(
            encoding="utf-8"
        )
        for marker in (
            "MAX_FILE_BYTES = 20 * 1024 * 1024",
            "new TextDecoder('utf-8')",
            "new TextDecoder('utf-16le')",
            "state.lineEnding",
            "global.InkDeskRuntime.requestDownload",
            "global.InkDeskFileLifecycle.create",
            "lifecycle.confirmDiscard",
            "global.InkDeskWorkspaceOpenFile = openFile",
            "extensions: ['txt']",
            "global.InkDeskTxtDebug",
        ):
            self.assertIn(marker, script)

    def test_router_and_registry_include_txt(self):
        router = (ROOT / "shared/file-router.js").read_text(
            encoding="utf-8"
        )
        registry = (ROOT / "modules/module-registry.js").read_text(
            encoding="utf-8"
        )
        config = json.loads(
            (ROOT / "modules/module-config.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertIn(
            "txt:'./apps/txt/index.html'",
            router,
        )
        self.assertIn('"id": "txt"', registry)
        txt_entry = next(
            item for item in config["modulePaths"]
            if item["id"] == "txt"
        )
        self.assertFalse(txt_entry["required"])

    def test_home_and_offline_shell_include_txt(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        worker = (ROOT / "service-worker.js").read_text(
            encoding="utf-8"
        )

        self.assertIn("./apps/txt/index.html", home)
        self.assertIn(".txt", home)
        for asset in (
            "./TXT.html",
            "./apps/txt/module.json",
            "./apps/txt/index.html",
            "./apps/txt/styles.css",
            "./apps/txt/app.js",
        ):
            self.assertIn(repr(asset), worker)
        self.assertRegex(worker, r"const CACHE_NAME=['\"]inkdesk-shell-v[^'\"]+['\"];")

    def test_application_manifest_records_txt_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        contract = manifest["txtEditorSystem"]

        self.assertEqual(contract["version"], "0.20.0")
        self.assertTrue(contract["localProcessing"])
        self.assertTrue(contract["preservesDetectedLineEnding"])
        self.assertIn("txt", manifest["capabilities"])
        self.assertEqual(
            manifest["documentSessionSystem"][
                "editableTitles"
            ]["txt"],
            ".txt",
        )
        self.assertNotIn(
            "txt",
            manifest["iconSystem"]["plannedModuleIcons"],
        )

    def test_javascript_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        for relative in (
            "apps/txt/app.js",
            "shared/file-router.js",
            "modules/module-registry.js",
        ):
            result = subprocess.run(
                [node, "--check", str(ROOT / relative)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                result.stdout + result.stderr,
            )

    def test_package_script_is_registered(self):
        package = json.loads(
            (ROOT / "package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            package["scripts"]["test:txt"],
            "python3 -m unittest tests.test_txt_module",
        )


if __name__ == "__main__":
    unittest.main()
