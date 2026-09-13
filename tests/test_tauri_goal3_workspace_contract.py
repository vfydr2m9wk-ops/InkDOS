import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "desktop" / "workspaces.json"
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"

EXPECTED = {
    "documents": ({"docx"}, "assets/icons/documents.svg"),
    "spreadsheets": ({"xls", "xlsx", "csv", "tsv"}, "assets/icons/spreadsheets.svg"),
    "presentations": ({"pptx"}, "assets/icons/presentations.png"),
    "pdf": ({"pdf"}, "assets/icons/pdf.svg"),
    "epub": ({"epub"}, "assets/icons/epub.svg"),
    "txt": ({
        "txt", "xml", "md", "markdown", "json", "jsonl", "ndjson",
        "yaml", "yml", "log", "ini", "cfg", "conf", "toml", "properties",
    }, "assets/icons/txt.svg"),
}


def test_goal3_workspace_authority_is_explicit_and_non_overlapping():
    assert WORKSPACES.exists(), "Goal 3 requires desktop/workspaces.json as the native routing authority"
    payload = json.loads(WORKSPACES.read_text(encoding="utf-8"))
    assert set(payload) == set(EXPECTED)
    claimed = set()
    for workspace, (expected_extensions, expected_icon) in EXPECTED.items():
        entry = payload[workspace]
        assert set(entry["extensions"]) == expected_extensions
        assert entry["route"] == f"apps/{workspace}/index.html"
        assert entry["icon"] == expected_icon
        assert claimed.isdisjoint(expected_extensions)
        claimed |= expected_extensions


def test_tauri_bundle_file_associations_match_workspace_authority():
    payload = json.loads(WORKSPACES.read_text(encoding="utf-8"))
    config = json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))
    associations = config["bundle"]["fileAssociations"]
    actual = {entry["name"]: set(entry["ext"]) for entry in associations}
    expected = {workspace: set(entry["extensions"]) for workspace, entry in payload.items()}
    assert actual == expected


if __name__ == "__main__":
    test_goal3_workspace_authority_is_explicit_and_non_overlapping()
    test_tauri_bundle_file_associations_match_workspace_authority()
    print("Goal 3 workspace/file-association contracts: PASS")
