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
            self.assertIn("../../shared/local-recovery.js?v=0.20.3.0", html)
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
                save_block = text[text.index("function offerSaveCopy(result)"):text.index("function selectionBlock()")]
                self.assertNotIn("recovery.markClean()", save_block)
                self.assertIn("await recovery.flush()", save_block)
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
        self.assertIn("inkdesk-shell-v0.20.3.1", text)

    def test_service_worker_canonicalizes_versioned_shell_assets(self):
        text = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("canonical.search=''", text)
        self.assertIn("canonical.hash=''", text)
        self.assertIn("APP_SHELL_URLS.has(canonical.href)", text)
        hub = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("module-registry.js?v=0.20.3.1", hub)

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
        self.assertIn("await deleteSnapshotsOnly(moduleName,key,sessionId)", block)
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


    def test_fresh_source_only_records_have_an_orphan_grace_period(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        self.assertIn("SOURCE_ORPHAN_GRACE_MS=MAX_AGE_MS", text)
        self.assertIn("now-Number(item.updatedAt||0)>SOURCE_ORPHAN_GRACE_MS", text)
        self.assertIn("SOURCE_ORPHAN_GRACE_MS", text[text.index("constants:Object.freeze"):])

    def test_active_session_can_rehydrate_a_missing_source_before_snapshot(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        for marker in (
            "let sourceData=null,sourceMeta={}",
            "capturedSourceData=sourceData",
            "if(capturedSourceData!=null)",
            "if(!existing)await putSource",
            "could not rehydrate the recovery source package",
            "sourceData=source&&Object.prototype.hasOwnProperty.call(source,'data')?source.data:null",
        ):
            self.assertIn(marker, text)

    def test_snapshot_cleanup_is_race_aware(self):
        text = (ROOT / "shared/local-recovery.js").read_text(encoding="utf-8")
        start = text.index("async function clearSnapshots()")
        end = text.index("async function markClean()", start)
        block = text[start:end]
        self.assertIn("Recovery cleanup deferred because new edits arrived", block)
        self.assertIn("if(documentKey===key&&(dirty||revision>0))await flush()", block)
        clean_start = text.index("async function markClean()")
        clean_end = text.index("async function discardCurrent()", clean_start)
        clean = text[clean_start:clean_end]
        self.assertIn("if(documentKey===key&&(dirty||revision>0))await flush()", clean)

    def test_browser_recovery_covers_source_grace_and_rehydration(self):
        text = (ROOT / "tests/browser/revalidate_v0202_local_recovery.py").read_text(encoding="utf-8")
        for marker in (
            "recovery_source_rehydration_case",
            "recovery-source-rehydrate",
            "freshSourcePreserved",
            "rehydratedSource",
        ):
            self.assertIn(marker, text)

    def test_release_identity_is_v0202(self):
        version = json.loads((ROOT / "VERSION.json").read_text(encoding="utf-8"))
        state = json.loads((ROOT / "DEVELOPMENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(version["version"], "0.20.3.1")
        self.assertEqual(version["releaseName"], "Content Workspaces Visual Pass")
        self.assertEqual(state["appliedSequence"], 35)
        self.assertEqual(state["currentPackage"], "0.20.3.1")


if __name__ == "__main__":
    unittest.main()
