"""Desktop (Tauri) webview CSP contract.

The desktop host enforces its own Content-Security-Policy in addition to the per-page meta CSP, so a
page that ever ships without a meta CSP still cannot run foreign or eval'd script with access to the
Tauri IPC (window.__TAURI__). The host policy must stay strict, and must not block anything the
staged pages' own meta CSP allows (hash sources are added per page by Tauri at build time).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
STAGED_DIRS = ("apps", "shared", "assets")
# Web-edition-only sources the desktop host deliberately keeps blocking: the InkDOS-tools site (its own
# origin) backs Home's Advanced tools, hidden on desktop, and the OpenDocument/iWork viewers, which the
# desktop edition does not associate and which report "viewer did not load" there instead of opening.
WEB_ONLY = {"frame-src": {"https://inkdos-offic.pages.dev"}}
CSP_META = re.compile(r'http-equiv\s*=\s*["\']Content-Security-Policy["\']\s+content\s*=\s*"([^"]+)"', re.IGNORECASE)


def host_policy() -> dict[str, set[str]]:
    security = json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))["app"]["security"]
    csp = security["csp"]
    assert isinstance(csp, dict) and csp, "desktop webview must define its own CSP"
    return {name: set(value.split()) for name, value in csp.items()}


def page_policies():
    pages = [ROOT / "index.html"] + [p for d in STAGED_DIRS for p in (ROOT / d).rglob("*.html") if not p.name.endswith(".template.html")]
    for page in pages:
        match = CSP_META.search(page.read_text(encoding="utf-8"))
        assert match, f"staged page without meta CSP: {page.relative_to(ROOT)}"
        directives = {}
        for part in match.group(1).split(";"):
            tokens = part.split()
            if tokens:
                directives[tokens[0]] = set(tokens[1:])
        yield page.relative_to(ROOT), directives


def test_host_csp_is_strict():
    policy = host_policy()
    for name in ("default-src", "script-src", "object-src", "base-uri", "frame-src", "form-action"):
        assert name in policy, name
    assert policy["object-src"] == {"'none'"} and policy["base-uri"] == {"'none'"}
    assert policy["frame-src"] in ({"'none'"}, {"'self'"})
    for name, sources in policy.items():
        assert "'unsafe-eval'" not in sources, name
        assert not any(s in sources for s in ("*", "http:", "https:")), name
    assert "'unsafe-inline'" not in policy["script-src"]
    security = json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))["app"]["security"]
    # only style-src may skip Tauri's nonce/hash injection (it would disable 'unsafe-inline' styles)
    assert security.get("dangerousDisableAssetCspModification", False) in (False, ["style-src"])


def test_host_csp_does_not_block_what_pages_allow():
    policy = host_policy()
    for page, directives in page_policies():
        for name, sources in directives.items():
            allowed = policy.get(name, policy["default-src"])
            missing = {s for s in sources if not s.startswith("'sha256-") and s != "'none'"} - allowed - WEB_ONLY.get(name, set())
            assert not missing, f"{page}: host CSP {name} would block {sorted(missing)}"


if __name__ == "__main__":
    test_host_csp_is_strict()
    test_host_csp_does_not_block_what_pages_allow()
    print("Tauri desktop CSP contract: OK")
