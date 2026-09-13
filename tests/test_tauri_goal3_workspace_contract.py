import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "desktop" / "workspaces.json"

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


if __name__ == "__main__":
    test_goal3_workspace_authority_is_explicit_and_non_overlapping()
    print("Goal 3 workspace authority contract: PASS")
