from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArchitectureGuardrailsTests(unittest.TestCase):
    def test_policy_has_refactoring_ratchet(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["release"], "0.20.2.4")
        self.assertTrue(policy["rules"]["grandfatheredFilesMayShrinkButNotGrow"])
        self.assertIn("apps/presentations/app.js", policy["grandfatheredDebt"])
        self.assertIn("apps/pdf/app.js", policy["grandfatheredDebt"])
        self.assertIn("shared/ui/workspace-layout.js", policy["grandfatheredDebt"])

    def test_agent_rules_preserve_behavior_and_visual_contract(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("smallest change", text)
        self.assertIn("moving code does **not** authorize", text)
        self.assertIn("44 px", text)
        self.assertIn("React", text)
        self.assertIn(".github/workflows", text)

    def test_guardrail_command_passes_current_tree(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_architecture_guardrails.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Architecture guardrails passed", result.stdout)

    def test_release_gate_runs_architecture_guardrails(self):
        runner = (ROOT / "scripts/run_release_validation.py").read_text(encoding="utf-8")
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn('("Architecture guardrails", [sys.executable, "scripts/check_architecture_guardrails.py"])', runner)
        self.assertEqual(package["scripts"]["test:guardrails"], "python3 scripts/check_architecture_guardrails.py")
        updater = (ROOT / "scripts/apply_update_package.py").read_text(encoding="utf-8")
        self.assertIn("scripts/check_architecture_guardrails.py", updater)

    def test_guard_script_contains_dependency_and_cycle_checks(self):
        text = (ROOT / "scripts/check_architecture_guardrails.py").read_text(encoding="utf-8")
        self.assertIn("Cross-workspace runtime dependency", text)
        self.assertIn("Shared runtime imports workspace code", text)
        self.assertIn("Relative runtime import cycle", text)

    def test_native_runtime_decision_is_explicit(self):
        text = (ROOT / "docs/adr/0001-native-modular-runtime.md").read_text(encoding="utf-8")
        self.assertIn("React", text)
        self.assertIn("native", text.lower())
        self.assertIn("compilation", text.lower())

    def make_fixture_repo(self, files: dict[str, str], *, max_lines: int = 5, max_length: int = 40) -> Path:
        temp = Path(tempfile.mkdtemp(prefix="inkdesk-guard-test-"))
        self.addCleanup(shutil.rmtree, temp, True)
        (temp / "scripts").mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/check_architecture_guardrails.py", temp / "scripts/check_architecture_guardrails.py")
        for relative, content in files.items():
            path = temp / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        policy = {
            "schemaVersion": 1,
            "release": "test",
            "runtimeRoots": ["apps", "shared", "modules"],
            "extensions": {
                ".js": {"newFileMaxLines": max_lines, "maxPhysicalLineLength": max_length},
                ".css": {"newFileMaxLines": max_lines, "maxPhysicalLineLength": max_length},
            },
            "grandfatheredDebt": {},
            "rules": {
                "noCrossWorkspaceRuntimeDependencies": True,
                "noSharedImportsFromApps": True,
                "noRelativeImportCycles": True,
                "grandfatheredFilesMayShrinkButNotGrow": True,
            },
        }
        (temp / "architecture-policy.json").write_text(json.dumps(policy), encoding="utf-8")
        return temp

    def run_fixture(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/check_architecture_guardrails.py"],
            cwd=root,
            capture_output=True,
            text=True,
        )

    def test_guardrail_rejects_new_oversized_or_compressed_runtime_source(self):
        repo = self.make_fixture_repo({"apps/documents/new.js": "const x = '" + "x" * 80 + "';\n"})
        result = self.run_fixture(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("physical line", result.stdout)

    def test_guardrail_rejects_cross_workspace_dependency(self):
        repo = self.make_fixture_repo(
            {
                "apps/documents/a.js": "import '../presentations/b.js';\n",
                "apps/presentations/b.js": "export const b = 1;\n",
            },
            max_length=120,
        )
        result = self.run_fixture(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cross-workspace runtime dependency", result.stdout)

    def test_guardrail_rejects_relative_import_cycle(self):
        repo = self.make_fixture_repo(
            {
                "shared/a.js": "import './b.js';\n",
                "shared/b.js": "import './a.js';\n",
            },
            max_length=120,
        )
        result = self.run_fixture(repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Relative runtime import cycle", result.stdout)


if __name__ == "__main__":
    unittest.main()
