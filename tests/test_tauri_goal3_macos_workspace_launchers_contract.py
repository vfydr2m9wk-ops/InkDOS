import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_DIR = ROOT / "desktop" / "src-tauri"
CONFIG_PATH = TAURI_DIR / "tauri.conf.json"
LAUNCHERS_PATH = ROOT / "desktop" / "launchers.json"
GENERATOR_PATH = ROOT / "desktop" / "scripts" / "generate_macos_workspace_launchers.py"
MACOS_LAUNCHER_ROOT = TAURI_DIR / "macos" / "workspace-launchers"
DESKTOP_BUILD_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "desktop-tauri.yml"


def main() -> None:
    launchers = json.loads(LAUNCHERS_PATH.read_text(encoding="utf-8"))
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert GENERATOR_PATH.exists(), "macOS workspace launcher materializer must exist"
    assert MACOS_LAUNCHER_ROOT.exists(), "macOS workspace launcher staging root must exist"

    macos = config["bundle"].get("macOS", {})
    files = macos.get("files", {})
    assert files.get("Helpers/InkDOS Workspace Launchers") == "./macos/workspace-launchers", (
        "the single InkDOS.app bundle must embed lightweight workspace launchers under Contents/Helpers"
    )

    generator = GENERATOR_PATH.read_text(encoding="utf-8")
    assert 'launcher["icon"]' in generator
    assert '"cargo", "tauri", "icon"' in generator
    assert "icon.icns" in generator
    assert "--workspace" in generator
    assert "../../../../MacOS/InkDOS" in generator

    for workspace, launcher in launchers.items():
        assert launcher["executable"] == "InkDOS"
        assert launcher["icon"].startswith("assets/icons/")
        assert workspace in generator, f"macOS launcher generator must materialize {workspace}"

    workflow = DESKTOP_BUILD_WORKFLOW_PATH.read_text(encoding="utf-8")
    generation_token = "python desktop/scripts/generate_macos_workspace_launchers.py"
    build_token = "cargo tauri build --bundles"
    assert generation_token in workflow, "production macOS build must materialize workspace launchers"
    assert workflow.index(generation_token) < workflow.index(build_token)
    assert "if: runner.os == 'macOS'" in workflow

    serialized = json.dumps(config["bundle"], sort_keys=True)
    assert "InkDOS-Documents" not in serialized
    assert "InkDOS-Spreadsheets" not in serialized
    assert config["productName"] == "InkDOS"
    assert config["identifier"] == "com.inkdos.desktop"


if __name__ == "__main__":
    main()
