from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ApplicationShellTests(unittest.TestCase):
    def test_shared_shell_files_exist(self):
        required = [
            "shared/office-shell.js",
            "shared/ui/design-tokens.css",
            "shared/ui/components.css",
            "shared/ui/application-shell.js",
            "shared/ui/shell-contract.json",
            "docs/APPLICATION_SHELL.md",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_contract_is_valid_and_versioned(self):
        contract = json.loads(
            (ROOT / "shared" / "ui" / "shell-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["schemaVersion"], 1)
        self.assertEqual(contract["version"], "0.19.4.3")
        self.assertEqual(
            set(contract["regions"]),
            {
                "titlebar",
                "command-tabs",
                "commandbar",
                "workspace",
                "statusbar",
            },
        )
        self.assertIn("inkdesk:shell-ready", contract["events"])
        self.assertIn("inkdesk:panel-change", contract["events"])

    def test_existing_workspaces_load_the_compatibility_bootstrap(self):
        workspaces = [
            "apps/documents/index.html",
            "apps/spreadsheets/index.html",
            "apps/presentations/index.html",
            "apps/pdf/index.html",
        ]
        for relative in workspaces:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("../../shared/office-shell.css", text, relative)
            self.assertIn("../../shared/office-shell.js", text, relative)
            self.assertIn("office-product", text, relative)
            self.assertLess(
                text.index("../../shared/office-shell.js"),
                text.index("app.js"),
                relative,
            )

    def test_service_worker_caches_shared_shell_assets(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        for asset in (
            "./shared/ui/design-tokens.css",
            "./shared/ui/components.css",
            "./shared/ui/application-shell.js",
            "./shared/ui/shell-contract.json",
        ):
            self.assertIn(repr(asset), worker)
        self.assertIn("0.19.3-beta.7", worker)
        self.assertRegex(
            worker,
            r"const CACHE_NAME=[\'\"]inkdesk-shell-v[^\'\"]+[\'\"];",
        )

    def test_package_and_application_manifest_expose_shell(self):
        package = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            package["scripts"]["test:shell"],
            "python3 -m unittest tests.test_application_shell",
        )
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(encoding="utf-8")
        )
        ui = manifest["uiSystem"]
        self.assertEqual(ui["version"], "0.19.4.3")
        self.assertEqual(ui["bootstrap"], "shared/office-shell.js")
        self.assertEqual(
            ui["runtime"],
            "shared/ui/application-shell.js",
        )

    def test_javascript_runtime_smoke(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = """
require('./shared/ui/application-shell.js');
if (!globalThis.InkDeskUI) process.exit(10);
if (globalThis.InkDeskUI.version !== '0.19.4.3') process.exit(11);

let value = 0;
const commands = globalThis.InkDeskUI.createCommandRegistry(null);
const unregister = commands.register(
  'test.increment',
  () => { value += 1; return value; }
);
if (!commands.has('test.increment')) process.exit(12);
if (commands.execute('test.increment') !== 1) process.exit(13);
unregister();
if (commands.has('test.increment')) process.exit(14);

function classes(initial) {
  const values = new Set(initial || []);
  return {
    add(value) { values.add(value); },
    remove(value) { values.delete(value); },
    contains(value) { return values.has(value); },
    toggle(value, force) {
      if (force === true) values.add(value);
      else if (force === false) values.delete(value);
      else if (values.has(value)) values.delete(value);
      else values.add(value);
      return values.has(value);
    }
  };
}

const panelElement = {
  id: 'panel',
  hidden: false,
  classList: classes(),
  dataset: {},
  attrs: {},
  setAttribute(name, value) { this.attrs[name] = String(value); },
  hasAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attrs, name);
  },
  querySelector() { return null; }
};

const panelTarget = {
  dispatchEvent() {},
  querySelectorAll() { return []; }
};

const panels = globalThis.InkDeskUI.createPanelController(panelTarget);
panels.register('sample-panel', panelElement, { side: 'left' });
if (!panels.isOpen('sample-panel')) process.exit(15);
panels.setOpen('sample-panel', false);
if (panels.isOpen('sample-panel')) process.exit(16);
panels.toggle('sample-panel');
if (!panels.isOpen('sample-panel')) process.exit(17);
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
