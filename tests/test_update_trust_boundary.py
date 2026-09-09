from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import hashlib
import json
import zipfile


ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "scripts" / "apply_update_package.py"
WORKFLOW = ROOT / ".github" / "workflows" / "apply-inkdos-update.yml"


def load_updater():
    spec = spec_from_file_location("inkdos_update_security", UPDATER)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_package(path: Path, payload: dict[str, bytes], *, sequence: int = 2):
    manifest = {
        "product": "InkDOS",
        "packageLabel": "security-test",
        "sequence": sequence,
        "mode": "incremental",
        "validationProfile": "standard",
        "requires": {"previousSequence": sequence - 1, "appVersions": ["2.0.12"]},
        "files": {name: {"sha256": sha256(data)} for name, data in payload.items()},
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("patch-manifest.json", json.dumps(manifest))
        for name, data in payload.items():
            archive.writestr("files/" + name, data)


def test_update_zip_cannot_supply_repository_updater(tmp_path):
    updater = load_updater()
    package = tmp_path / "bad.zip"
    write_package(
        package,
        {"scripts/apply_update_package.py": b"print('package controlled')"},
    )
    try:
        updater.inspect(package)
    except updater.UpdateError as exc:
        assert "control-plane" in str(exc)
    else:
        raise AssertionError("Package-supplied updater was accepted")


def test_control_plane_is_case_insensitively_protected():
    updater = load_updater()
    protected = [
        ".github/workflows/evil.yml",
        "SCRIPTS/run_release_validation.py",
        "Tests/test_fake.py",
        "requirements-ci.txt",
        "PYTEST.INI",
    ]
    for path in protected:
        try:
            updater.safe_payload(path)
        except updater.UpdateError:
            continue
        raise AssertionError(f"Protected path was accepted: {path}")


def test_normal_app_payload_remains_allowed():
    updater = load_updater()
    for path in [
        "apps/documents/app.js",
        "apps/pdf/vendor/pdfjs/pdf.min.js",
        "assets/home.css",
        "service-worker.js",
    ]:
        assert updater.safe_payload(path).as_posix() == path


def test_full_snapshot_copies_trusted_control_plane(tmp_path):
    updater = load_updater()
    repo = tmp_path / "repo"
    extracted = tmp_path / "extracted"
    candidate = tmp_path / "candidate"
    for root in (repo, extracted, candidate):
        root.mkdir()

    (repo / ".github/workflows").mkdir(parents=True)
    (repo / ".github/workflows/gate.yml").write_text("trusted\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts/run_release_validation.py").write_text("trusted\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests/test_gate.py").write_text("trusted\n", encoding="utf-8")
    (repo / "requirements-ci.txt").write_text("trusted==1\n", encoding="utf-8")
    (repo / "DEVELOPMENT_STATE.json").write_text(
        json.dumps({"appliedSequence": 1}), encoding="utf-8"
    )
    (repo / "VERSION.json").write_text(json.dumps({"version": "2.0.12"}), encoding="utf-8")

    payload = extracted / "files"
    (payload / "apps/documents").mkdir(parents=True)
    (payload / "apps/documents/app.js").write_text("candidate\n", encoding="utf-8")
    manifest = {
        "product": "InkDOS",
        "packageLabel": "snapshot",
        "sequence": 2,
        "mode": "full-snapshot",
        "validationProfile": "standard",
        "requires": {"previousSequence": 1, "appVersions": ["2.0.12"]},
        "files": {
            "apps/documents/app.js": {
                "sha256": updater.sha(payload / "apps/documents/app.js")
            }
        },
    }
    updater.validate_manifest(manifest)
    updater.build(repo, extracted, candidate, manifest)
    updater.ensure_control_identity(repo, candidate)

    assert (candidate / ".github/workflows/gate.yml").read_text() == "trusted\n"
    assert (candidate / "scripts/run_release_validation.py").read_text() == "trusted\n"
    assert (candidate / "tests/test_gate.py").read_text() == "trusted\n"
    assert (candidate / "requirements-ci.txt").read_text() == "trusted==1\n"
    assert (candidate / "apps/documents/app.js").read_text() == "candidate\n"


def test_workflow_never_executes_package_supplied_updater():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "/tmp/apply_update_package.py" not in text
    assert "Prepare package updater" not in text
    assert "python scripts/apply_update_package.py" in text
    assert "Validate update package without write credentials" in text
    assert "Apply with repository-trusted updater only" in text
    assert "--validation-profile none" in text
