from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfShellPolishTests(unittest.TestCase):
    def test_pdf_identity_is_red_everywhere(self):
        manifest = json.loads(
            (ROOT / "apps" / "pdf" / "module.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["accent"], "#b42318")

        registry = (
            ROOT / "modules" / "module-registry.js"
        ).read_text(encoding="utf-8")
        pdf_index = registry.index('"id": "pdf"')
        self.assertIn(
            '"accent": "#b42318"',
            registry[pdf_index:],
        )

        hub = (ROOT / "shared" / "hub.css").read_text(encoding="utf-8")
        self.assertIn(
            ".pdf{--accent:#b42318}",
            hub,
        )

        layout = (
            ROOT / "shared" / "ui" / "workspace-layout.css"
        ).read_text(encoding="utf-8")
        self.assertIn("--accent: #b42318 !important", layout)
        self.assertIn("--inkdesk-accent: #b42318", layout)

    def test_pdf_sidebar_defaults_closed_and_owns_toggle(self):
        runtime = (
            ROOT / "shared" / "ui" / "workspace-layout.js"
        ).read_text(encoding="utf-8")

        for expected in (
            "pdf: Object.freeze",
            "sidebar: false",
            "'pdf.sidebar'",
            "sidebar-collapsed",
            "stopImmediatePropagation",
            "inkdeskPdfSidebarController",
            "setSidebarOpen(initialOpen, false)",
        ):
            self.assertIn(expected, runtime)

    def test_closed_sidebar_reserves_no_desktop_width(self):
        styles = (
            ROOT / "shared" / "ui" / "workspace-layout.css"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "body.office-pdf .workspace-body.sidebar-collapsed",
            styles,
        )
        self.assertIn(
            "grid-template-columns: 0 minmax(0, 1fr) !important",
            styles,
        )
        self.assertIn("max-width: 0 !important", styles)
        self.assertIn("pointer-events: none !important", styles)

    def test_metadata_records_pdf_shell_defaults(self):
        manifest = json.loads(
            (ROOT / "app-manifest.json").read_text(encoding="utf-8")
        )
        layout = manifest["uiSystem"]["workspaceLayout"]
        self.assertEqual(layout["version"], "0.20.0")
        self.assertEqual(layout["defaults"]["pdfSidebar"], "closed")
        self.assertEqual(layout["defaults"]["pdfAccent"], "#b42318")

    def test_runtime_sidebar_interaction(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
require('./shared/ui/workspace-layout.js');

function classList(initial) {
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

const body = {
  dataset: { inkdeskModule: 'pdf' },
  classList: classList(['office-product', 'office-pdf'])
};

const workspace = {
  dataset: {},
  classList: classList()
};

const sidebar = {
  attrs: {},
  inert: false,
  setAttribute(name, value) { this.attrs[name] = String(value); }
};

let capturedClick = null;
const toggle = {
  dataset: {},
  attrs: {},
  title: '',
  classList: classList(['active']),
  setAttribute(name, value) { this.attrs[name] = String(value); },
  addEventListener(name, handler, capture) {
    if (name === 'click' && capture === true) capturedClick = handler;
  }
};

const startScreen = { dataset: {} };
const openButton = { dataset: {} };

const elements = {
  startScreen,
  openBtn: openButton,
  workspaceBody: workspace,
  sidebar,
  sidebarToggle: toggle
};

const documentObject = {
  body,
  querySelector() { return null; },
  getElementById(id) { return elements[id] || null; },
  dispatchEvent() {}
};

globalThis.dispatchEvent = function () {};
globalThis.sessionStorage = {
  getItem() { return null; },
  setItem() {}
};

const api = globalThis.InkDeskWorkspaceLayout;
if (!api || api.version !== '0.20.0') process.exit(10);
if (!api.apply(documentObject)) process.exit(11);
if (!workspace.classList.contains('sidebar-collapsed')) process.exit(12);
if (toggle.classList.contains('active')) process.exit(13);
if (toggle.attrs['aria-expanded'] !== 'false') process.exit(14);
if (sidebar.attrs['aria-hidden'] !== 'true') process.exit(15);
if (typeof capturedClick !== 'function') process.exit(16);

let prevented = false;
let stopped = false;
capturedClick({
  preventDefault() { prevented = true; },
  stopImmediatePropagation() { stopped = true; }
});

if (!prevented || !stopped) process.exit(17);
if (workspace.classList.contains('sidebar-collapsed')) process.exit(18);
if (!toggle.classList.contains('active')) process.exit(19);
if (toggle.attrs['aria-expanded'] !== 'true') process.exit(20);
if (sidebar.attrs['aria-hidden'] !== 'false') process.exit(21);
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
