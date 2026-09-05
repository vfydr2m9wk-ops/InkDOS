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
            "apps/txt/history-controller.js",
            "apps/txt/find-controller.js",
            "assets/icons/txt.svg",
            "assets/icons/txt.png",
            "docs/TXT_EDITOR.md",
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
            "../../shared/file-lifecycle.js?v=1.0.0-beta.7",
            html,
        )
        self.assertIn(
            "../../shared/file-router.js?v=1.0.0-beta.7",
            html,
        )
        self.assertIn(
            'history-controller.js?v=1.0.0-beta.7',
            html,
        )
        self.assertIn(
            'find-controller.js?v=1.0.0-beta.7',
            html,
        )
        self.assertLess(
            html.index('history-controller.js?v=1.0.0-beta.7'),
            html.index('app.js?v=1.0.0-beta.7'),
        )
        self.assertLess(
            html.index('find-controller.js?v=1.0.0-beta.7'),
            html.index('app.js?v=1.0.0-beta.7'),
        )
        self.assertLess(
            html.index('../../shared/local-recovery.js?v=1.0.0-beta.7'),
            html.index('app.js?v=1.0.0-beta.7'),
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
            "global.InkDOSRuntime.requestDownload",
            "global.InkDOSFileLifecycle.create",
            "lifecycle.confirmDiscard",
            "global.InkDOSWorkspaceOpenFile = openFile",
            "appId: 'txt'",
            "global.InkDOSTxtDebug",
            "global.InkDOSTxtRecoveryController.create",
            "await recovery.flush()",
):
            self.assertIn(marker, script)
        controller = (ROOT / "apps/txt/recovery-controller.js").read_text(encoding="utf-8")
        self.assertIn("global.InkDOSLocalRecovery.create", controller)
        self.assertIn("manager.promptLatest()", controller)

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

        self.assertIn("registry().resolveExtension", router)
        self.assertIn("module.route", router)
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
        self.assertIn("./apps/txt/index.html", home)
        self.assertNotIn("openAnyInput", home)
        for asset in (
            "./apps/txt/module.json",
            "./apps/txt/index.html",
            "./apps/txt/styles.css",
            "./apps/txt/app.js",
            "./apps/txt/history-controller.js",
            "./apps/txt/find-controller.js",
        ):
            self.assertIn(repr(asset), worker)
        self.assertRegex(worker, r"const CACHE_NAME=['\"]inkdos-shell-v[^'\"]+['\"];")

    def test_application_manifest_records_txt_contract(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        contract = manifest["txtEditorSystem"]

        self.assertEqual(contract["version"], "1.0.0-beta.7")
        self.assertTrue(contract["localProcessing"])
        self.assertTrue(contract["preservesDetectedLineEnding"])
        self.assertEqual(contract["recovery"], "shared/local-recovery.js")
        self.assertIn("private-indexeddb-recovery-snapshots", manifest["capabilities"]["txt"])
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
            "apps/txt/history-controller.js",
            "apps/txt/find-controller.js",
            "apps/txt/history-controller.js",
            "apps/txt/find-controller.js",
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
