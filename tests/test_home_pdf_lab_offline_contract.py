"""PDF tools (beta), web edition: the tools page works offline after its first use.

Every local file the page loads (labs/pdf/index.html scripts and styles) is in the service worker's
offline lists: the page's own files on demand (hashed, cached on first use, never precached for
every visitor), the PDF workspace files it reuses through the app shell.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PAGE = ROOT / "labs/pdf/index.html"


def listed(name: str) -> list[str]:
    return json.loads(re.search(r"const " + name + r"=(\[.*?\]);", SW, re.S)[1])


def test_tools_page_is_cached_on_first_use():
    html = PAGE.read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"#:]+)"', html)
    files = {"./" + (PAGE.parent / ref).resolve().relative_to(ROOT).as_posix() for ref in refs}
    files.add("./labs/pdf/index.html")
    shell, on_demand = set(listed("APP_SHELL")), set(listed("ON_DEMAND"))
    missing = sorted(f for f in files if f not in shell | on_demand)
    assert not missing, missing
    assert not any(p.startswith("./labs/") for p in shell), "the tools page must not be precached for every visitor"
    for path in files:
        assert f'"{path}":' in SW, f"{path} has no offline hash"
