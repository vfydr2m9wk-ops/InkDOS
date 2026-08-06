from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APPLY_WORKFLOW = ROOT / ".github/workflows/apply-inkdesk-update.yml"


class UpdateWorkflowObservabilityTests(unittest.TestCase):
    def test_workflow_never_self_modifies(self):
        workflow = APPLY_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("--allow-workflow-changes", workflow)
        self.assertIn(
            "Update packages cannot create or modify GitHub workflow files",
            workflow,
        )
        self.assertIn(
            "Update packages cannot delete GitHub workflow files",
            workflow,
        )
        self.assertIn(
            "Refusing to commit staged workflow changes",
            workflow,
        )

    def test_package_is_retained_until_validation_succeeds(self):
        workflow = APPLY_WORKFLOW.read_text(encoding="utf-8")
        selection = workflow.index("Select and inspect update package")
        transaction = workflow.index("Apply package transaction")
        removal = workflow.index('rm -- "${PACKAGE_NAME}"')
        self.assertLess(selection, transaction)
        self.assertLess(transaction, removal)
        self.assertIn(
            "The root ZIP is retained until validation succeeds.",
            workflow,
        )

    def test_summary_distinguishes_validation_and_push_failures(self):
        workflow = APPLY_WORKFLOW.read_text(encoding="utf-8")
        commit = workflow.index("Commit and push applied update")
        summary = workflow.index("Write final Actions summary")
        self.assertLess(commit, summary)
        self.assertIn(
            "Validation passed, but commit/push failed",
            workflow,
        )
        self.assertIn(
            "repository transaction rolled back",
            workflow,
        )

    def test_workflow_has_ci_and_manual_update_modes(self):
        workflow = APPLY_WORKFLOW.read_text(encoding="utf-8")
        for marker in (
            "workflow_dispatch:",
            "push:",
            "pull_request:",
            "Validate repository",
            "Apply update package",
            "python scripts/run_release_validation.py",
        ):
            self.assertIn(marker, workflow)

    def test_workflow_uses_current_node24_action_generations(self):
        workflow = APPLY_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)

    def test_updater_retains_failure_reporting(self):
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


if __name__ == "__main__":
    unittest.main()
