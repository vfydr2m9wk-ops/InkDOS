#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_export_release_validation.py"


def main() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "TemporaryDirectory" in text, "export gate must use an isolated temporary tree"
    auth=(ROOT / "tests" / "test_243_release_authorization_contract.py").read_text(encoding="utf-8")
    assert "TemporaryDirectory(dir=R)" not in auth, "release authorization contract must not create interrupt-leakable temp trees inside the source root"
    assert "invoke_validator" in auth and "subprocess.run" not in auth, "release authorization negative matrix must run validator in-process to keep the aggregate gate bounded"
    assert "shutil.copytree(ROOT, checkout" in text, "export gate must validate a copy, not mutate Workspace source"
    assert '["git", "init", "-q"]' in text, "export gate must synthesize git metadata for git-dependent contracts"
    assert '["git", "add", "-A"]' in text, "all exported files must participate in current-tree privacy validation"
    assert "scripts/run_release_validation.py" in text, "export gate must delegate to the canonical aggregate gate"
    assert ("inkdos-export-validation" + "@" + "invalid.local") not in text, "wrapper source must not embed an email-shaped literal rejected by source audit"
    assert '"inkdos-export-validation" + "@" + "invalid.local"' in text, "synthetic git identity must be assembled without an email-shaped source literal"
    assert "GitHub history not validated" in text, "export gate must not overclaim historical validation"
    print("InkDOS 2.4.3 Library/export validation wrapper contract passed.")


if __name__ == "__main__":
    main()
