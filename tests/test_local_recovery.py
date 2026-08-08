from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LocalRecoveryTests(unittest.TestCase):
    def test_shared_recovery_module_has_private_indexeddb_contract(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        for token in (
            "InkDeskLocalRecovery",
            "indexedDB.open",
            "snapshots",
            "sources",
            "MAX_PER_DOCUMENT=3",
            "MAX_PER_MODULE=12",
            "Restore",
            "Discard recovery",
            "Open normally",
            "markClean",
            "resetSnapshots",
            "orphanSources",
            "cleanupOrphanSources",
        ):
            self.assertIn(token, text)
        self.assertNotIn("fetch('http", text)
        self.assertNotIn('fetch("http', text)

    def test_only_editable_office_workspaces_load_recovery_module(self):
        enabled = ("documents", "spreadsheets", "presentations")
        disabled = ("pdf", "txt", "epub")
        for module in enabled:
            html = (ROOT / "apps" / module / "index.html").read_text(encoding="utf-8")
            self.assertIn("../../shared/local-recovery.js?v=0.20.2.26", html)
            self.assertLess(html.index("local-recovery.js"), html.index("app.js"))
        for module in disabled:
            html = (ROOT / "apps" / module / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("local-recovery.js", html)

    def test_workspaces_capture_restore_and_clear_after_download(self):
        cases = {
            "documents": (
                "captureDocumentRecovery",
                "restoreDocumentRecovery",
                "__InkDeskDocumentsRecovery",
            ),
            "spreadsheets": (
                "captureSpreadsheetRecovery",
                "restoreSpreadsheetRecovery",
                "__InkDeskSpreadsheetsRecovery",
            ),
        }
        for module, tokens in cases.items():
            text = (ROOT / "apps" / module / "app.js").read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text)
            self.assertIn("recovery.markDirty", text)
            if module == "documents":
                self.assertIn("recovery.markClean", text)
            else:
                self.assertNotIn("recovery.markClean()", text[text.index("async function download()"):text.index("async function newWorkbook()")])
                self.assertIn("await recovery.flush()", text)
            self.assertIn("recovery.promptLatest", text)
            self.assertIn("resetSnapshots:true", text)

        app = (ROOT / "apps/presentations/app.js").read_text(encoding="utf-8")
        recovery = (ROOT / "apps/presentations/io/recovery-controller.js").read_text(encoding="utf-8")
        self.assertIn("InkDeskPresentationsRecovery.create", app)
        self.assertIn("__InkDeskPresentationsRecovery", recovery)
        for token in (
            "async capture()",
            "async restore(context)",
            "this.manager.markDirty",
            "this.manager.markClean",
            "this.manager.promptLatest",
            "resetSnapshots: true",
        ):
            self.assertIn(token, recovery)

    def test_service_worker_caches_recovery_runtime(self):
        text = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("./shared/local-recovery.js", text)
        self.assertIn("inkdesk-shell-v0.20.2.26", text)

    def test_service_worker_canonicalizes_versioned_shell_assets(self):
        text = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("canonical.search=''", text)
        self.assertIn("canonical.hash=''", text)
        self.assertIn("APP_SHELL_URLS.has(canonical.href)", text)
        hub = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("module-registry.js?v=0.20.2.26", hub)

    def test_local_recovery_browser_waits_use_playwright_keyword_arg(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        self.assertIn("arg=token", text)
        self.assertNotIn("innerText.includes(value)\", token)", text)
        self.assertNotIn("value === value\", token)", text)

    def test_browser_matrix_entry_points_exist(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["scripts"]["test:browser:matrix"], "python3 scripts/run_browser_matrix.py")
        matrix = (ROOT / "scripts/run_browser_matrix.py").read_text(encoding="utf-8")
        for engine in ("chromium", "firefox", "webkit"):
            self.assertIn(engine, matrix)
        runner = (ROOT / "scripts/run_browser_regressions.py").read_text(encoding="utf-8")
        self.assertIn("revalidate_v0202_local_recovery.py", runner)
        self.assertIn("INKDESK_BROWSER", runner)


    def test_mark_clean_retains_source_package_for_edits_after_save(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        start = text.index("async function markClean()")
        end = text.index("async function discardCurrent()", start)
        block = text[start:end]
        self.assertIn("await deleteSnapshotsOnly(moduleName,key)", block)
        self.assertNotIn("await deleteDocument(moduleName,key)", block)
        self.assertIn("Recovery cleanup deferred because new edits arrived", block)
        self.assertIn("async function cleanupOrphanSources(moduleName)", text)
        prompt = text[text.index("async function promptLatest()"):text.index("function getState()") ]
        self.assertIn("await cleanupOrphanSources(moduleName)", prompt)

    def test_browser_recovery_covers_save_then_edit_then_restore_fidelity(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        for marker in (
            "spreadsheets_post_save_edit_recovery_case",
            "RECOVERY-SAVED-BASE-020226",
            "RECOVERY-POST-SAVE-EDIT-020226",
            "recovery_post_save_restored.xlsx",
            "originalFeatures",
            "restoredFeatures",
        ):
            self.assertIn(marker, text)

    def test_release_identity_is_v0202(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / "DEVELOPMENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(version["version"], "0.20.2.26")
        self.assertEqual(version["releaseName"], "Export Confirmation Safety and Release Notes Organization")
        self.assertEqual(state["appliedSequence"], 28)
        self.assertEqual(state["currentPackage"], "0.20.2.26")


if __name__ == "__main__":
    unittest.main()
