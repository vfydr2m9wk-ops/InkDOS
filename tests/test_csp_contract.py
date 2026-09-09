#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_csp.py"

spec = importlib.util.spec_from_file_location("generate_csp", SCRIPT)
assert spec and spec.loader
generate_csp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_csp)

META_RE = re.compile(
    r'<meta\s+[^>]*http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
    re.IGNORECASE,
)
CONTENT_RE = re.compile(r'content="(?P<content>[^"]*)"', re.IGNORECASE)


def assert_policy(rendered: str, label: str) -> None:
    metas = META_RE.findall(rendered)
    assert len(metas) == 1, f"{label}: expected exactly one CSP meta tag, got {len(metas)}"
    match = CONTENT_RE.search(metas[0])
    assert match, f"{label}: CSP meta tag has no generated double-quoted content policy"
    policy = match.group("content")
    script_directive = next(
        (directive.strip() for directive in policy.split(";") if directive.strip().startswith("script-src ")),
        None,
    )
    assert script_directive, f"{label}: missing script-src"
    assert "'self'" in script_directive, f"{label}: script-src must retain self"
    assert "'unsafe-inline'" not in script_directive, f"{label}: unsafe-inline JavaScript is forbidden"
    assert "'unsafe-eval'" not in script_directive, f"{label}: unsafe-eval is forbidden"
    assert "object-src 'none'" in policy, f"{label}: object-src must be none"
    assert "base-uri 'none'" in policy, f"{label}: base-uri must be none"


def assert_idempotent(source: str, label: str) -> None:
    once = generate_csp.render(source)
    twice = generate_csp.render(once)
    assert once == twice, f"{label}: CSP rendering is not byte-for-byte idempotent"
    assert_policy(once, label)


def main() -> None:
    # Synthetic formatted and compact inputs lock both canonicalization paths.
    assert_idempotent(
        '<!doctype html>\n<html>\n<head>\n  <meta charset="utf-8">\n  <script>console.log("x")</script>\n</head>\n</html>\n',
        "synthetic-pretty",
    )
    assert_idempotent(
        '<!doctype html><html><head><meta charset="utf-8"><script>console.log("x")</script></head></html>',
        "synthetic-compact",
    )

    for rel in generate_csp.ENTRY_POINTS:
        path = ROOT / rel
        assert path.is_file(), f"missing entry point: {rel}"
        assert_idempotent(path.read_text(encoding="utf-8"), rel.as_posix())

    print("CSP idempotence and script policy contract: OK")


if __name__ == "__main__":
    main()
