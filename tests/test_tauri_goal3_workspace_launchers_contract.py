import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES_PATH = ROOT / "desktop" / "workspaces.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
MAIN_RS_PATH = ROOT / "desktop" / "src-tauri" / "src" / "main.rs"


def main() -> None:
    workspaces = json.loads(WORKSPACES_PATH.read_text(encoding="utf-8"))
    assert LAUNCHERS_PATH.exists(), "desktop/launchers.json must define workspace launch entries"

    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    assert set(launchers) == set(workspaces), "launcher set must match workspace authority exactly"

    executable_names = set()
    for workspace, spec in workspaces.items():
        launcher = launchers[workspace]
        assert launcher["workspace"] == workspace
        assert launcher["icon"] == spec["icon"], (
            f"{workspace} launcher must reuse the existing workspace icon exactly"
        )
        assert launcher["args"] == ["--workspace", workspace], (
            f"{workspace} launcher must route through the shared host with --workspace"
        )
        executable_names.add(launcher["executable"])

    assert executable_names == {"InkDOS"}, "all workspace launchers must use one InkDOS executable"

    main_rs = MAIN_RS_PATH.read_text(encoding="utf-8")
    assert '"--workspace"' in main_rs, "native host must recognize the workspace-launch argument"
    assert "workspace_for_id" in main_rs, "workspace launches must validate against workspaces.json"
    assert "open_workspace_window" in main_rs, "workspace launch must open a native workspace window"


if __name__ == "__main__":
    main()
