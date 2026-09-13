#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_app_isolation.py"


def load_validator():
    spec = spec_from_file_location("inkdos_validate_app_isolation", VALIDATOR_PATH)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_fixture(root: Path, shared_ref: str):
    app = root / "apps" / "documents"
    app.mkdir(parents=True)
    shared = root / "shared"
    shared.mkdir(parents=True)
    (shared / "ui-density.css").write_text(":root{}\n", encoding="utf-8")
    (shared / "ui-density.js").write_text("void 0;\n", encoding="utf-8")
    (shared / "rogue.js").write_text("void 0;\n", encoding="utf-8")
    if shared_ref.endswith(".css"):
        html = f'<link rel="stylesheet" href="{shared_ref}">\n'
    else:
        html = f'<script src="{shared_ref}"></script>\n'
    (app / "index.html").write_text(html, encoding="utf-8")


def validate_fixture(shared_ref: str):
    validator = load_validator()
    with tempfile.TemporaryDirectory(prefix="inkdos-shared-density-contract-") as td:
        root = Path(td)
        write_fixture(root, shared_ref)
        validator.ROOT = root
        errors = []
        validator.validate_isolated_copy("documents", errors)
        validator.validate_cross_app_references("documents", errors)
        return errors


def test_approved_density_assets_are_the_only_shared_runtime_exception():
    for ref in ("../../shared/ui-density.css", "../../shared/ui-density.js"):
        errors = validate_fixture(ref)
        assert not errors, f"approved density asset rejected: {ref}: {errors}"


def test_unapproved_shared_runtime_reference_remains_rejected():
    errors = validate_fixture("../../shared/rogue.js")
    assert errors, "unapproved shared runtime reference must remain rejected"
    assert any("shared" in error or "escapes app root" in error for error in errors)


if __name__ == "__main__":
    test_approved_density_assets_are_the_only_shared_runtime_exception()
    test_unapproved_shared_runtime_reference_remains_rejected()
    print("App isolation approved shared-density exception contract: PASS")
