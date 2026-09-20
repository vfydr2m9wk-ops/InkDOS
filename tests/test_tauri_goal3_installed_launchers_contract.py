import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
NSIS_HOOK_PATH = TAURI_DIR / "windows" / "workspace-launchers.nsh"
WINDOWS_ICON_DIR = TAURI_DIR / "windows" / "workspace-icons"
ICON_GENERATOR_PATH = ROOT / "desktop" / "scripts" / "generate_workspace_icons.py"
RELEASE_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release.yml"
LINUX_LAUNCHER_DIR = TAURI_DIR / "linux" / "workspace-launchers"


def _assert_workspace_tokens(text: str, launchers: dict) -> None:
    for workspace, launcher in launchers.items():
        assert workspace in text, f"installed launcher integration must mention {workspace}"
        assert f"--workspace {workspace}" in text or f"--workspace\" \"{workspace}" in text, (
            f"installed launcher for {workspace} must invoke the shared host with --workspace"
        )
        assert launcher["executable"] == "InkDOS"


def main() -> None:
    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    bundle = config["bundle"]

    # Windows production distribution is NSIS-only. The installer hook must
    # materialize the workspace launch entries without reintroducing MSI/WiX.
    assert NSIS_HOOK_PATH.exists(), "NSIS installer hook must create workspace launch shortcuts"
    assert "wix" not in bundle["windows"], "MSI/WiX configuration must not be reintroduced"

    nsis = bundle["windows"]["nsis"]
    assert nsis["installerHooks"] == "./windows/workspace-launchers.nsh"

    nsis_text = NSIS_HOOK_PATH.read_text(encoding="utf-8")
    _assert_workspace_tokens(nsis_text, launchers)

    # Windows shortcuts must use workspace-specific native ICOs derived from
    # the exact canonical icon sources. Generated ICOs are build artifacts: they
    # must be materialized before packaging, then embedded by NSIS/WiX directly.
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

    # The production desktop build must materialize native icons before both
    # cargo check and native bundling.
    workflow_text = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")
    generation_token = "python desktop/scripts/generate_workspace_icons.py"
    cargo_check_token = "cargo check"
    build_token = "cargo tauri build --bundles"
    assert generation_token in workflow_text
    assert workflow_text.index(generation_token) < workflow_text.index(cargo_check_token)
    assert workflow_text.index(generation_token) < workflow_text.index(build_token)

    # Linux production distribution is AppImage-only. Workspace .desktop files
    # remain canonical launcher definitions, but must not be injected into the
    # AppImage as competing application identities.
    linux = bundle["linux"]
    assert set(linux) == {"appimage"}
    appimage_files = linux["appimage"].get("files", {})
    for workspace, launcher in launchers.items():
        desktop_file = LINUX_LAUNCHER_DIR / f"inkdos-{workspace}.desktop"
        assert desktop_file.exists(), f"missing canonical Linux launcher definition for {workspace}"
        text = desktop_file.read_text(encoding="utf-8")
        assert f"Exec=InkDOS --workspace {workspace}" in text
        assert f"Icon=inkdos-{workspace}" in text
        assert f"X-InkDOS-SourceIcon={launcher['icon']}" in text
        destination = f"/usr/share/applications/inkdos-{workspace}.desktop"
        assert destination not in appimage_files

    # No launcher may introduce a second InkDOS binary or application identity.
    serialized = json.dumps(bundle, sort_keys=True)
    assert "InkDOS-Documents" not in serialized
    assert "InkDOS-Spreadsheets" not in serialized
    assert config["productName"] == "InkDOS"
    assert config["identifier"] == "com.inkdos.desktop"


if __name__ == "__main__":
    main()
