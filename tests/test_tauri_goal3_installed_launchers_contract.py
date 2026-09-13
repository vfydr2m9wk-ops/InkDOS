import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
NSIS_HOOK_PATH = TAURI_DIR / "windows" / "workspace-launchers.nsh"
WIX_FRAGMENT_PATH = TAURI_DIR / "windows" / "workspace-launchers.wxs"
WINDOWS_ICON_DIR = TAURI_DIR / "windows" / "workspace-icons"
ICON_GENERATOR_PATH = ROOT / "desktop" / "scripts" / "generate_workspace_icons.py"
DESKTOP_BUILD_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "desktop-tauri.yml"
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

    # Windows ships both NSIS and MSI, so both installers must materialize the
    # same workspace launch entries instead of relying on launchers.json alone.
    assert NSIS_HOOK_PATH.exists(), "NSIS installer hook must create workspace launch shortcuts"
    assert WIX_FRAGMENT_PATH.exists(), "MSI WiX fragment must create workspace launch shortcuts"

    nsis = bundle["windows"]["nsis"]
    assert nsis["installerHooks"] == "./windows/workspace-launchers.nsh"

    wix = bundle["windows"]["wix"]
    assert "./windows/workspace-launchers.wxs" in wix["fragmentPaths"]
    assert "InkDOSWorkspaceLaunchers" in wix["componentGroupRefs"]

    nsis_text = NSIS_HOOK_PATH.read_text(encoding="utf-8")
    wix_text = WIX_FRAGMENT_PATH.read_text(encoding="utf-8")
    _assert_workspace_tokens(nsis_text, launchers)
    _assert_workspace_tokens(wix_text, launchers)

    # Tauri's generated WiX template exposes INSTALLDIR. Custom fragments must
    # attach to that directory id; INSTALLFOLDER is not defined and fails at
    # light.exe link time with LGHT0094.
    assert 'DirectoryRef Id="INSTALLDIR"' in wix_text
    assert 'DirectoryRef Id="INSTALLFOLDER"' not in wix_text
    assert '[INSTALLFOLDER]' not in wix_text
    assert 'WorkingDirectory="INSTALLFOLDER"' not in wix_text
    for workspace in launchers:
        assert 'Target="[INSTALLDIR]InkDOS.exe"' in wix_text
        assert 'WorkingDirectory="INSTALLDIR"' in wix_text

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

        icon_id = f"InkDOS{workspace.title().replace('-', '')}Icon"
        file_id = f"InkDOS{workspace.title().replace('-', '')}IconFile"
        assert f'Icon Id="{icon_id}"' in wix_text, (
            f"WiX must declare a workspace-specific icon id for {workspace}"
        )
        assert f'File Id="{file_id}"' in wix_text, (
            f"WiX must install the generated workspace icon for {workspace}"
        )
        assert f'Source="windows\\workspace-icons\\{workspace}\\icon.ico"' in wix_text
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
    workflow_text = DESKTOP_BUILD_WORKFLOW_PATH.read_text(encoding="utf-8")
    generation_token = "python desktop/scripts/generate_workspace_icons.py"
    cargo_check_token = "cargo check"
    build_token = "cargo tauri build --bundles"
    assert generation_token in workflow_text
    assert workflow_text.index(generation_token) < workflow_text.index(cargo_check_token)
    assert workflow_text.index(generation_token) < workflow_text.index(build_token)

    # Installed Linux packages need actual .desktop entries for every workspace.
    # freedesktop launchers reference an icon name, not an absolute private path;
    # the canonical source asset is installed into the standard hicolor tree so
    # linuxdeploy can resolve the launcher icon while building AppImage.
    linux = bundle["linux"]
    for workspace, launcher in launchers.items():
        desktop_file = LINUX_LAUNCHER_DIR / f"inkdos-{workspace}.desktop"
        assert desktop_file.exists(), f"missing installed Linux launcher for {workspace}"
        text = desktop_file.read_text(encoding="utf-8")
        assert f"Exec=InkDOS --workspace {workspace}" in text
        assert f"Icon=inkdos-{workspace}" in text
        assert "/usr/share/inkdos/workspace-icons/" not in text
        assert f"X-InkDOS-SourceIcon={launcher['icon']}" in text, (
            f"{workspace} Linux launcher must retain the canonical existing icon source"
        )
        destination = f"/usr/share/applications/inkdos-{workspace}.desktop"
        source = f"./linux/workspace-launchers/inkdos-{workspace}.desktop"
        icon_suffix = Path(launcher["icon"]).suffix
        icon_destination = (
            f"/usr/share/icons/hicolor/scalable/apps/inkdos-{workspace}{icon_suffix}"
            if icon_suffix == ".svg"
            else f"/usr/share/icons/hicolor/256x256/apps/inkdos-{workspace}{icon_suffix}"
        )
        for target in ("deb", "rpm", "appimage"):
            files = linux[target]["files"]
            assert files[destination] == source, (
                f"{target} must install the {workspace} workspace launcher"
            )
            assert files[icon_destination] == f"../../{launcher['icon']}", (
                f"{target} must install {workspace}'s canonical icon in the freedesktop hicolor tree"
            )

    # No launcher may introduce a second InkDOS binary or application identity.
    serialized = json.dumps(bundle, sort_keys=True)
    assert "InkDOS-Documents" not in serialized
    assert "InkDOS-Spreadsheets" not in serialized
    assert config["productName"] == "InkDOS"
    assert config["identifier"] == "com.inkdos.desktop"


if __name__ == "__main__":
    main()
