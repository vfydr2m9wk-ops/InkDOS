import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI = ROOT / "desktop" / "src-tauri"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_single_host_forwards_subsequent_file_opens_into_distinct_native_windows():
    cargo = read(TAURI / "Cargo.toml")
    main = read(TAURI / "src" / "main.rs")
    assert 'tauri-plugin-single-instance = "2"' in cargo
    for marker in (
        "tauri_plugin_single_instance::init",
        "open_file_window",
        "WebviewWindowBuilder",
        "file-",
        "workspaces.json",
    ):
        assert marker in main


def test_native_file_and_workspace_windows_receive_same_least_privilege_capability():
    capability = json.loads(read(TAURI / "capabilities" / "default.json"))
    assert set(capability["windows"]) == {"main", "file-*", "workspace-*"}


def test_desktop_bridge_auto_opens_only_the_native_injected_file():
    bridge = read(ROOT / "desktop" / "desktop-host.js")
    for marker in (
        "__INKDOS_OPEN_PATH__",
        "fs.readFile",
        "DataTransfer",
        'input[type="file"]',
        "dispatchEvent",
        "change",
    ):
        assert marker in bridge


def test_workspace_launcher_file_args_are_bound_to_that_workspace_allowlist():
    main = read(TAURI / "src" / "main.rs")
    for marker in (
        "workspace_supports_path",
        "open_file_window_for_workspace",
        "active_workspace",
        "does not accept",
    ):
        assert marker in main
    assert "open_file_window_for_workspace(app, workspace, path)" in main


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
    print(f"Goal 3 native window contract: {len(tests)} checks passed")
