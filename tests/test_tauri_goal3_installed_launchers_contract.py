import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
NSIS_HOOK_PATH = TAURI_DIR / "windows" / "workspace-launchers.nsh"
ICON_GENERATOR_PATH = ROOT / "desktop" / "scripts" / "generate_workspace_icons.py"
RELEASE_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release.yml"


def main() -> None:
    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    bundle = config["bundle"]

    # Desktop releases are Windows-only (NSIS); macOS and Linux builds were discontinued after 2.7.8 and their
    # launcher files removed. The NSIS installer materializes one launch shortcut per workspace.
    assert bundle["targets"] == ["nsis"]
    assert NSIS_HOOK_PATH.exists(), "NSIS installer hook must create workspace launch shortcuts"
    nsis = bundle["windows"]["nsis"]
    assert nsis["installerHooks"] == "./windows/workspace-launchers.nsh"
    assert "wix" not in bundle["windows"]

    nsis_text = NSIS_HOOK_PATH.read_text(encoding="utf-8")
    for workspace, launcher in launchers.items():
        assert workspace in nsis_text, f"installed launcher integration must mention {workspace}"
        assert f"--workspace {workspace}" in nsis_text or f"--workspace\" \"{workspace}" in nsis_text, (
            f"installed launcher for {workspace} must invoke the shared host with --workspace"
        )
        assert launcher["executable"] == "InkDOS"

    # Windows shortcuts must use workspace-specific native ICOs derived from
    # the exact canonical icon sources. Generated ICOs are build artifacts: they
    # must be materialized before packaging, then embedded by NSIS directly.
    assert ICON_GENERATOR_PATH.exists(), "workspace native-icon materializer must be retained"
    generator_text = ICON_GENERATOR_PATH.read_text(encoding="utf-8")
    assert 'launcher["icon"]' in generator_text
    assert '"cargo", "tauri", "icon"' in generator_text
    assert '"windows" / "workspace-icons"' in generator_text
    assert '!define HOOK_FILE_DIR "${__FILEDIR__}"' in nsis_text, (
        "NSIS hook must capture its own directory before macro expansion"
    )
    for workspace, launcher in launchers.items():
        icon_token = f"workspace-icons\\{workspace}\\icon.ico"
        assert icon_token in nsis_text, (
            f"NSIS shortcut for {workspace} must bind its workspace-specific native icon"
        )
        assert f'SetOutPath "$INSTDIR\\workspace-icons\\{workspace}"' in nsis_text
        assert f'File /oname=icon.ico "${{HOOK_FILE_DIR}}\\workspace-icons\\{workspace}\\icon.ico"' in nsis_text, (
            f"NSIS installer must embed the generated {workspace} ICO beside the shared host"
        )
        assert launcher["icon"].startswith("assets/icons/"), (
            f"{workspace} native icon must remain derived from the canonical icon source"
        )

    # Do not make cargo check depend on generated files via bundle.resources or
    # a late beforeBundleCommand hook: Tauri validates resource paths during its
    # Rust build script before that hook can run.
    assert "beforeBundleCommand" not in config.get("build", {})
    serialized_resources = json.dumps(bundle.get("resources", {}), sort_keys=True)
    assert "windows/workspace-icons" not in serialized_resources

    # The release build must materialize native icons before both cargo check and native bundling.
    workflow_text = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")
    generation_token = "python desktop/scripts/generate_workspace_icons.py"
    assert generation_token in workflow_text
    assert workflow_text.index(generation_token) < workflow_text.index("cargo check")
    assert workflow_text.index(generation_token) < workflow_text.index("cargo tauri build --bundles")

    # No launcher may introduce a second InkDOS binary or application identity.
    serialized = json.dumps(bundle, sort_keys=True)
    assert "InkDOS-Documents" not in serialized
    assert "InkDOS-Spreadsheets" not in serialized
    assert config["productName"] == "InkDOS"
    assert config["identifier"] == "com.inkdos.desktop"
    print("Windows installed workspace launchers contract: OK")


if __name__ == "__main__":
    main()
