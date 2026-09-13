import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
TAURI = DESKTOP / "src-tauri"
WORKFLOW = ROOT / ".github" / "workflows" / "desktop-tauri.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_VERSION = DESKTOP / "scripts" / "release_version.py"


def read(path: Path) -> str:
    assert path.exists(), f"required desktop file is missing: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def test_tauri_shell_configuration_matches_inkdos_release():
    version = json.loads(read(ROOT / "VERSION.json"))["version"]
    config = json.loads(read(TAURI / "tauri.conf.json"))
    assert config["productName"] == "InkDOS"
    assert config["version"] == version
    assert config["identifier"] == "com.inkdos.desktop"
    assert config["build"]["frontendDist"] == "../web-dist"
    assert config["app"]["withGlobalTauri"] is True
    assert config["app"]["windows"][0]["label"] == "main"


def test_tauri_rust_dependencies_are_v2_and_node_free():
    cargo = read(TAURI / "Cargo.toml")
    assert 'tauri = { version = "2"' in cargo
    assert 'tauri-plugin-dialog = "2"' in cargo
    assert 'tauri-plugin-fs = "2"' in cargo
    assert 'tauri-plugin-opener = "2"' in cargo
    lowered = cargo.lower()
    assert "electron" not in lowered
    assert "node" not in lowered


def test_capability_is_explicit_and_has_no_broad_static_filesystem_scope():
    capability = json.loads(read(TAURI / "capabilities" / "default.json"))
    assert capability["windows"] == ["main"]
    permissions = capability["permissions"]
    required = {
        "core:default",
        "dialog:allow-open",
        "dialog:allow-save",
        "fs:allow-read-file",
        "fs:allow-write-file",
        "opener:allow-default-urls",
    }
    assert required.issubset(set(permissions))
    assert all(not isinstance(item, dict) or item.get("identifier") != "fs:scope" for item in permissions)
    assert "shell:allow-execute" not in permissions
    assert "shell:allow-spawn" not in permissions


def test_desktop_bridge_maps_native_open_save_and_external_links():
    bridge = read(DESKTOP / "desktop-host.js")
    for marker in (
        "window.__TAURI__",
        "dialog.save",
        "fs.writeFile",
        "dialog.open",
        "fs.readFile",
        "showSaveFilePicker",
        "DataTransfer",
        "opener.openUrl",
        "deliveryConfirmed",
    ):
        assert marker in bridge


def test_stager_injects_bridge_without_editing_source_html():
    stager = read(DESKTOP / "scripts" / "stage_web.py")
    assert "desktop-host.js" in stager
    assert "<head>" in stager
    assert "web-dist" in stager
    assert "service-worker.js" in stager
    assert "apps" in stager
    assert "assets" in stager
    assert "--check" in stager


def test_release_version_utility_uses_version_json_as_authority():
    utility = read(RELEASE_VERSION)
    for marker in (
        "VERSION.json",
        "tauri.conf.json",
        "--check-config",
        "--sync-config",
        "--check-tag",
        "v{version}",
    ):
        assert marker in utility


def test_native_build_workflow_targets_main_or_manual_checkpoint_without_node():
    workflow = read(WORKFLOW)
    for marker in (
        "main",
        "workflow_dispatch",
        "windows-latest",
        "macos-latest",
        "ubuntu-22.04",
        "cargo tauri build",
        "InkDOS-Windows",
        "InkDOS-macOS",
        "InkDOS-Linux",
        "libwebkit2gtk-4.1-dev",
        "python desktop/scripts/stage_web.py",
        "python desktop/scripts/release_version.py --check-config",
    ):
        assert marker in workflow
    assert "desktop-tauri" not in workflow
    assert "feature/inkdos-2.3" not in workflow
    assert "setup-node" not in workflow
    assert "npm install" not in workflow
    assert "npm run" not in workflow


def test_tag_release_workflow_builds_every_platform_before_publication():
    workflow = read(RELEASE_WORKFLOW)
    for marker in (
        "v*.*.*",
        "windows-latest",
        "macos-latest",
        "ubuntu-22.04",
        "python desktop/scripts/release_version.py --check-tag",
        "python desktop/scripts/release_version.py --check-config",
        "InkDOS-Windows",
        "InkDOS-macOS",
        "InkDOS-Linux",
        "actions/download-artifact@v4",
        "contents: write",
        "gh release create",
        "https://vfydr2m9wk-ops.github.io/InkDOS/",
    ):
        assert marker in workflow
    assert "needs: [validate, build]" in workflow or "needs:\n      - validate\n      - build" in workflow
    assert "setup-node" not in workflow
    assert "npm install" not in workflow


def test_tag_release_publishes_only_final_installer_files():
    workflow = read(RELEASE_WORKFLOW)
    assert "release-final" in workflow
    for suffix in (".exe", ".msi", ".dmg", ".deb", ".AppImage", ".rpm"):
        assert suffix in workflow
    assert "find release-assets -type f -print0" not in workflow


def test_generated_desktop_bundles_are_ignored_within_desktop_boundary():
    ignored = read(DESKTOP / ".gitignore")
    for marker in (
        "web-dist/",
        "src-tauri/target/",
        "*.dmg",
        "*.AppImage",
        "*.msi",
        "*.rpm",
    ):
        assert marker in ignored


def test_bundle_targets_cover_expected_installers():
    config = json.loads(read(TAURI / "tauri.conf.json"))
    targets = set(config["bundle"]["targets"])
    assert {"nsis", "msi", "app", "dmg", "deb", "appimage", "rpm"}.issubset(targets)


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"desktop contract: {len(tests)} checks passed")
