import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
NSIS_HOOK_PATH = TAURI_DIR / "windows" / "workspace-launchers.nsh"
WIX_FRAGMENT_PATH = TAURI_DIR / "windows" / "workspace-launchers.wxs"
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

    # Installed Linux packages need actual .desktop entries for every workspace.
    linux = bundle["linux"]
    for workspace, launcher in launchers.items():
        desktop_file = LINUX_LAUNCHER_DIR / f"inkdos-{workspace}.desktop"
        assert desktop_file.exists(), f"missing installed Linux launcher for {workspace}"
        text = desktop_file.read_text(encoding="utf-8")
        assert f"Exec=InkDOS --workspace {workspace}" in text
        assert f"X-InkDOS-SourceIcon={launcher['icon']}" in text, (
            f"{workspace} Linux launcher must retain the canonical existing icon source"
        )
        destination = f"/usr/share/applications/inkdos-{workspace}.desktop"
        source = f"./linux/workspace-launchers/inkdos-{workspace}.desktop"
        for target in ("deb", "rpm", "appimage"):
            files = linux[target]["files"]
            assert files[destination] == source, (
                f"{target} must install the {workspace} workspace launcher"
            )

    # No launcher may introduce a second InkDOS binary or application identity.
    serialized = json.dumps(bundle, sort_keys=True)
    assert "InkDOS-Documents" not in serialized
    assert "InkDOS-Spreadsheets" not in serialized
    assert config["productName"] == "InkDOS"
    assert config["identifier"] == "com.inkdos.desktop"


if __name__ == "__main__":
    main()
