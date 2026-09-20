import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "desktop"
TAURI = DESKTOP / "src-tauri"
LEGACY_DESKTOP_WORKFLOW = ROOT / ".github" / "workflows" / "desktop-tauri.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
PROMOTION_WORKFLOW = ROOT / ".github" / "workflows" / "promote-release-tag.yml"
PROMOTION_REQUEST = ROOT / ".github" / "release-promotion.json"
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


def test_tauri_rust_dependencies_are_pinned_to_verified_release_versions():
    cargo = read(TAURI / "Cargo.toml")
    for marker in (
        'rust-version = "1.98.1"',
        'tauri-build = { version = "=2.6.3"',
        'tauri = { version = "=2.11.5"',
        'tauri-plugin-single-instance = "=2.4.4"',
        'tauri-plugin-dialog = "=2.7.3"',
        'tauri-plugin-fs = "=2.5.2"',
        'tauri-plugin-opener = "=2.5.5"',
        'tauri-plugin-updater = "=2.11.0"',
        'serde = { version = "=1.0.229"',
        'serde_json = "=1.0.151"',
    ):
        assert marker in cargo
    lowered = cargo.lower()
    assert "electron" not in lowered
    assert "node" not in lowered


def test_capability_is_explicit_and_has_no_broad_static_filesystem_scope():
    capability = json.loads(read(TAURI / "capabilities" / "default.json"))
    assert set(capability["windows"]) == {"main", "file-*", "workspace-*"}
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


def test_associated_file_delivery_waits_until_workspace_load_handlers_finish():
    bridge = read(DESKTOP / "desktop-host.js")
    assert "if (document.readyState === 'complete') g.setTimeout(autoOpenNativeInjectedFile, 0);" in bridge
    assert "g.addEventListener('load', () => g.setTimeout(autoOpenNativeInjectedFile, 0), { once: true });" in bridge
    assert "\n  autoOpenNativeInjectedFile();\n" not in bridge


def test_stager_injects_bridge_without_editing_source_html_or_shipping_status_docs():
    stager = read(DESKTOP / "scripts" / "stage_web.py")
    assert "desktop-host.js" in stager
    assert "<head>" in stager
    assert "web-dist" in stager
    assert "service-worker.js" in stager
    assert "apps" in stager
    assert "assets" in stager
    assert "--check" in stager
    assert "PROJECT_STATUS.md" not in stager


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


def test_legacy_desktop_workflow_is_absent_and_unified_release_owns_native_builds():
    assert not LEGACY_DESKTOP_WORKFLOW.exists(), "legacy desktop-tauri workflow must not be reintroduced"
    workflow = read(RELEASE_WORKFLOW)
    for marker in (
        "v*.*.*",
        "python desktop/scripts/stage_web.py --check",
        "python desktop/scripts/release_version.py --check-config",
        "python tests/test_tauri_desktop_contract.py",
        "windows-latest",
        "macos-latest",
        "ubuntu-22.04",
        "cargo tauri build --bundles",
    ):
        assert marker in workflow
    assert "workflow_dispatch" not in workflow


def test_release_has_one_tag_only_entrypoint_and_no_promotion_state():
    workflow = read(RELEASE_WORKFLOW)
    assert "v*.*.*" in workflow
    assert "workflow_dispatch" not in workflow
    assert "reuse_run_id" not in workflow
    assert "inputs." not in workflow
    assert "RELEASE_TAG: ${{ github.ref_name }}" in workflow
    assert not PROMOTION_WORKFLOW.exists()
    assert not PROMOTION_REQUEST.exists()


def test_tag_release_workflow_builds_every_platform_before_publication():
    workflow = read(RELEASE_WORKFLOW)
    for marker in (
        "windows-latest",
        "macos-latest",
        "ubuntu-22.04",
        "python desktop/scripts/release_version.py --check-tag",
        "python desktop/scripts/release_version.py --check-config",
        "python desktop/scripts/generate_workspace_icons.py",
        "InkDOS-Windows",
        "InkDOS-macOS",
        "InkDOS-Linux",
        "actions/download-artifact@v4",
        "contents: write",
        "gh release create",
        "https://vfydr2m9wk-ops.github.io/InkDOS/",
        "dtolnay/rust-toolchain@6bed0761d98439e5a578e2877258200ad565ba87",
        "toolchain: 1.98.1",
        'cargo install tauri-cli --version "2.11.4" --locked',
    ):
        assert marker in workflow
    assert workflow.index("python desktop/scripts/generate_workspace_icons.py") < workflow.index("cargo tauri build --bundles")
    assert "needs: [validate, build]" in workflow or "needs:\n      - validate\n      - build" in workflow
    assert "setup-node" not in workflow
    assert "npm install" not in workflow


def test_release_builds_only_supported_installer_formats():
    workflow = read(RELEASE_WORKFLOW)
    for marker in (
        "bundles: nsis",
        "bundles: app,dmg",
        "bundles: appimage",
        "bundle/nsis/*.exe",
        "bundle/dmg/*.dmg",
        "bundle/macos/*.app.tar.gz",
        "bundle/appimage/*.AppImage",
    ):
        assert marker in workflow
    for forbidden in (
        "bundles: nsis,msi",
        "bundles: deb,appimage,rpm",
        "bundle/msi/",
        "bundle/deb/",
        "bundle/rpm/",
        "'.msi'",
        "'.deb'",
        "'.rpm'",
    ):
        assert forbidden not in workflow


def test_tag_release_publishes_only_current_run_final_assets():
    workflow = read(RELEASE_WORKFLOW)
    assert "release-final" in workflow
    assert "run-id:" not in workflow
    assert "Download reused" not in workflow
    assert "Download current-run native artifacts" in workflow
    assert "Download current-run provenance" in workflow
    assert "required_installers = ('.exe', '.dmg', '.AppImage')" in workflow
    assert "updater_required = ('.exe.sig', '.app.tar.gz', '.app.tar.gz.sig', '.AppImage.sig')" in workflow
    assert 'if [ "${#ASSETS[@]}" -lt 8 ]; then' in workflow


def test_generated_desktop_bundles_are_ignored_within_desktop_boundary():
    ignored = read(DESKTOP / ".gitignore")
    for marker in (
        "web-dist/",
        "src-tauri/target/",
        "*.dmg",
        "*.AppImage",
    ):
        assert marker in ignored


def test_bundle_targets_cover_only_supported_installers():
    config = json.loads(read(TAURI / "tauri.conf.json"))
    assert set(config["bundle"]["targets"]) == {"nsis", "app", "dmg", "appimage"}
    assert "wix" not in config["bundle"].get("windows", {})
    linux = config["bundle"].get("linux", {})
    assert "deb" not in linux
    assert "rpm" not in linux


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"desktop contract: {len(tests)} checks passed")
