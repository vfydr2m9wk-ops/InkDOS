from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UpdateWorkflowObservabilityTests(unittest.TestCase):
    def test_workflow_captures_transaction_log_and_exit_code(self):
        workflow = (ROOT / ".github/workflows/apply-inkdesk-update.yml").read_text(encoding="utf-8")
        for marker in (
            "tee /tmp/update-transaction.log",
            "status=${PIPESTATUS[0]}",
            "exit_code=${status}",
            "Failed — repository transaction rolled back",
            "Automatic diagnosis",
            "repository transaction rolled back",
            "workflowObservation",
        ):
            self.assertIn(marker, workflow)

    def test_workflow_mentions_the_stale_pdf_version_failure(self):
        workflow = (ROOT / ".github/workflows/apply-inkdesk-update.yml").read_text(encoding="utf-8")
        self.assertIn("app.js?v=0.19.4.6", workflow)
        self.assertIn("version-independent selector", workflow)

    def test_workflow_prefers_the_package_updater(self):
        workflow = (
            ROOT / ".github/workflows/apply-inkdesk-update.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Using updater supplied by the selected package.",
            workflow,
        )
        self.assertIn(
            "elif Path('scripts/apply_update_package.py').is_file()",
            workflow,
        )

    def test_updater_writes_failure_report(self):
        script = (ROOT / "scripts/apply_update_package.py").read_text(encoding="utf-8")
        for marker in (
            "def write_failure_report",
            '"status": "failed"',
            '"rollback": True',
            '"repositorySequenceAfterRollback"',
            'manifest.get("workflowObservation", "")',
        ):
            self.assertIn(marker, script)

    def test_observability_document_records_superseded_attempts(self):
        document = (
            ROOT / "docs" / "UPDATE_WORKFLOW_OBSERVABILITY.md"
        ).read_text(encoding="utf-8")

        self.assertIn("two rolled-back attempts", document)
        self.assertIn("app.js?v=0.19.4.6", document)
        self.assertIn(
            "patch-manifest-0.19.4.10.json",
            document,
        )

    def test_workflow_diagnoses_fixture_inventory_failure(self):
        workflow = (
            ROOT / ".github/workflows/apply-inkdesk-update.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "test_only_synthetic_fixtures_are_bundled",
            workflow,
        )
        self.assertIn(
            "tests/fixtures",
            workflow,
        )
        self.assertIn(
            "Repository sequence after rollback",
            workflow,
        )
        self.assertIn("Transaction error", workflow)


if __name__ == "__main__":
    unittest.main()
