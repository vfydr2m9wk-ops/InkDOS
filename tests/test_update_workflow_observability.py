from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/publish-inkdesk-v0.20.0.yml"


class UpdateWorkflowObservabilityTests(unittest.TestCase):
    def test_publication_workflow_has_safe_staging_and_dry_run(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "Locate complete package",
            "Inspect and extract package safely",
            "Verify release identity",
            "Vendor pinned PDF.js runtime",
            "Validate staged source",
            "Dry-run summary",
            "dry_run",
        ):
            self.assertIn(marker, workflow)

    def test_publication_workflow_preserves_recovery_path(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "Create backup branch",
            "backup/pre-v0.20.0-${GITHUB_RUN_ID}",
            "Replace repository with v0.20.0",
            "rsync -a --delete",
            "Validate replaced repository",
        ):
            self.assertIn(marker, workflow)

    def test_publication_workflow_pins_vendor_and_checksums(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("npm pack pdfjs-dist@3.11.174", workflow)
        self.assertIn("install -m 0644 package/build/pdf.min.js", workflow)
        self.assertIn("install -m 0644 package/build/pdf.worker.min.js", workflow)
        self.assertIn("python3 scripts/generate_checksums.py", workflow)
        self.assertIn("python3 scripts/verify_checksums.py", workflow)

    def test_publication_workflow_commits_and_tags_release(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "Release InkDesk v0.20.0",
            "git push origin HEAD:${GITHUB_REF_NAME}",
            "Create release tag",
            "git tag -a v0.20.0",
        ):
            self.assertIn(marker, workflow)

    def test_legacy_updater_retains_failure_reporting_for_archives(self):
        script = (
            ROOT / "scripts/apply_update_package.py"
        ).read_text(encoding="utf-8")
        for marker in (
            "def write_failure_report",
            '"status": "failed"',
            '"rollback": True',
            '"repositorySequenceAfterRollback"',
        ):
            self.assertIn(marker, script)

    def test_observability_history_document_is_retained(self):
        document = (
            ROOT / "docs/UPDATE_WORKFLOW_OBSERVABILITY.md"
        ).read_text(encoding="utf-8")
        self.assertIn("rolled-back attempts", document)
        self.assertIn("transaction error", document.lower())


if __name__ == "__main__":
    unittest.main()
