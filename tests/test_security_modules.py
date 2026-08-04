from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SecurityModuleTests(unittest.TestCase):
    def test_security_modules_execute(self):
        completed = subprocess.run(
            ["node", "tests/js/security-modules.test.js"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        result = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertGreaterEqual(result["assertions"], 40)

    def test_runtime_has_no_dynamic_compilation(self):
        for path in [ROOT / "apps" / "spreadsheets" / "app.js", ROOT / "shared" / "formula-engine.js"]:
            source = path.read_text(encoding="utf-8")
            self.assertNotRegex(source, r"\b(?:eval|Function)\s*\(")

    def test_all_workspaces_use_shared_lifecycle(self):
        for rel in (
            "apps/documents/app.js",
            "apps/spreadsheets/app.js",
            "apps/presentations/app.js",
        ):
            source=(ROOT/rel).read_text(encoding="utf-8")
            self.assertIn("InkDeskFileLifecycle.create", source)
            self.assertIn("shouldWarnBeforeUnload", source)
            self.assertIn("downloadRequested", source)

if __name__ == "__main__":
    unittest.main()
