#!/usr/bin/env python3
"""Generate deterministic hash-based CSP meta tags for InkDOS entry points."""
from __future__ import annotations

from pathlib import Path
import argparse
import base64
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = (
    Path("index.html"),
    Path("apps/documents/index.html"),
    Path("apps/spreadsheets/index.html"),
    Path("apps/presentations/index.html"),
    Path("apps/pdf/index.html"),
    Path("apps/txt/index.html"),
    Path("apps/epub/index.html"),
)

# Generated CSP metadata is emitted as its own indented line for formatted HTML.
# Remove that whole line first so render(render(html)) is byte-for-byte stable.
# The second expression handles compact/minified entry points where the tag may be
# adjacent to other markup on the same line.
CSP_META_LINE_RE = re.compile(
    r'(?mi)^[ \t]*<meta\s+[^>]*http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>[ \t]*(?:\r?\n)?'
)
CSP_META_RE = re.compile(
    r'<meta\s+[^>]*http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
    re.IGNORECASE,
)
SCRIPT_RE = re.compile(
    r'<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
CHARSET_RE = re.compile(r'<meta\s+charset\s*=\s*["\'][^"\']+["\'][^>]*>', re.IGNORECASE)

BASE_DIRECTIVES = (
    "default-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "worker-src 'self' blob:",
    "media-src 'self' data: blob:",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'none'",
    "frame-src 'none'",
    "manifest-src 'self'",
)


def strip_existing_csp(text: str) -> str:
    """Return the pre-CSP canonical HTML, preserving unrelated whitespace."""
    without_lines = CSP_META_LINE_RE.sub("", text)
    return CSP_META_RE.sub("", without_lines)


def inline_script_hashes(text: str) -> list[str]:
    hashes: set[str] = set()
    for match in SCRIPT_RE.finditer(text):
        attrs = match.group("attrs") or ""
        if re.search(r"\bsrc\s*=", attrs, re.IGNORECASE):
            continue
        body = match.group("body")
        digest = hashlib.sha256(body.encode("utf-8")).digest()
        hashes.add("'sha256-" + base64.b64encode(digest).decode("ascii") + "'")
    return sorted(hashes)


def policy_for(text_without_csp: str) -> str:
    hashes = inline_script_hashes(text_without_csp)
    script = "script-src 'self'"
    if hashes:
        script += " " + " ".join(hashes)
    return "; ".join((BASE_DIRECTIVES[0], script, *BASE_DIRECTIVES[1:]))


def render(text: str) -> str:
    clean = strip_existing_csp(text)
    policy = policy_for(clean)
    meta = f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
    charset = CHARSET_RE.search(clean)
    if not charset:
        raise RuntimeError("Entry point does not contain a quoted meta charset tag")
    pretty = "\n" in clean[: charset.end() + 4]
    insertion = ("\n  " if pretty else "") + meta
    rendered = clean[: charset.end()] + insertion + clean[charset.end() :]
    # Defensive invariant: generated CSP must be intrinsically idempotent.
    # Do not recurse through render(); compare against one canonical strip/reinsert.
    canonical_clean = strip_existing_csp(rendered)
    canonical_charset = CHARSET_RE.search(canonical_clean)
    if not canonical_charset:
        raise RuntimeError("Generated CSP lost the meta charset tag")
    canonical_pretty = "\n" in canonical_clean[: canonical_charset.end() + 4]
    canonical_insertion = ("\n  " if canonical_pretty else "") + meta
    canonical = (
        canonical_clean[: canonical_charset.end()]
        + canonical_insertion
        + canonical_clean[canonical_charset.end() :]
    )
    if rendered != canonical:
        raise RuntimeError("CSP renderer is not idempotent")
    return rendered


def process(path: Path, check: bool) -> bool:
    source = path.read_text(encoding="utf-8")
    expected = render(source)
    if source == expected:
        return False
    if check:
        print(f"CSP metadata is stale or missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return True
    path.write_text(expected, encoding="utf-8")
    print(f"Updated CSP: {path.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = False
    for rel in ENTRY_POINTS:
        path = ROOT / rel
        if not path.is_file():
            print(f"Missing CSP entry point: {rel}", file=sys.stderr)
            return 2
        changed = process(path, args.check) or changed
    if args.check and changed:
        return 1
    if args.check:
        print("InkDOS CSP metadata is current for all entry points.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
