#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ("pdf", "documents", "presentations", "txt", "epub", "spreadsheets")


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.resources: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        data = dict(attrs)
        if tag == "script" and data.get("src"):
            self.resources.append(data["src"])
        elif tag == "link" and "stylesheet" in str(data.get("rel", "")).lower() and data.get("href"):
            self.resources.append(data["href"])


def normalize_resource(index_path: Path, raw: str) -> str | None:
    split = urlsplit(raw)
    if split.scheme in {"http", "https"} or split.netloc:
        raise AssertionError(f"External runtime dependency in {index_path.relative_to(ROOT)}: {raw}")
    path = split.path
    if not path or path.startswith(("data:", "blob:", "javascript:")):
        return None
    if path.startswith("/"):
        resolved = ROOT / path.lstrip("/")
    else:
        resolved = (index_path.parent / path).resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise AssertionError(f"Resource escapes repository root: {raw}") from exc
    return "./" + relative.as_posix()


def main() -> None:
    state = json.loads((ROOT / "STABILITY_STATE.json").read_text(encoding="utf-8"))
    assert state["currentWorkspace"] == "cross-suite", state
    assert state["completedWorkspaces"] == list(WORKSPACES), state

    sw = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    match = re.search(r"const APP_SHELL=\[(.*?)\];", sw, re.S)
    assert match, "service-worker APP_SHELL not found"
    precache = set(re.findall(r'"(\./[^"]+)"', match.group(1)))

    missing: list[str] = []
    checked: list[str] = []
    inline_only: list[str] = []
    for workspace in WORKSPACES:
        index_path = ROOT / "apps" / workspace / "index.html"
        assert index_path.is_file(), index_path
        parser = ResourceParser()
        parser.feed(index_path.read_text(encoding="utf-8"))
        resources = [normalize_resource(index_path, raw) for raw in parser.resources]
        resources = [path for path in resources if path]
        if not resources:
            inline_only.append(workspace)
        assert len(resources) == len(set(resources)), f"Duplicate runtime resource in {workspace}"
        for resource in resources:
            checked.append(resource)
            if resource not in precache:
                missing.append(resource)

        for navigation in (f'./apps/{workspace}/', f'./apps/{workspace}/index.html'):
            assert navigation in sw, f"Missing offline navigation route: {navigation}"

    assert not missing, "Resources missing from APP_SHELL:\n" + "\n".join(sorted(set(missing)))
    assert "./index.html" in precache
    assert "./manifest.webmanifest" in precache
    assert "./service-worker.js" not in precache, "Service worker must update from the network, not cache itself"

    inline_note = f"; inline bootstrap: {', '.join(inline_only)}" if inline_only else ""
    print(f"Cross-suite static contract: OK ({len(set(checked))} declared workspace resources checked{inline_note})")


if __name__ == "__main__":
    main()
