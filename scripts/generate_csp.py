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

# Generated CSP metadata is emitted as its own indented line only when the
# charset tag itself occupies a whitespace-only formatted line. Compact entry
# points keep the CSP tag adjacent so strip/reinsert is byte-stable.
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


# Home hosts a launched file's workspace in a same-origin frame, the PDF workspace hosts the
# PDF tools (beta) page in its panel, and Documents, Spreadsheets and Presentations show
# OpenDocument and Apple iWork files in the InkDOS-tools viewers (view only); the other
# workspaces frame nothing.
FRAME_SELF_ENTRY_POINTS = frozenset({Path("index.html"), Path("apps/pdf/index.html"),
                                     Path("apps/documents/index.html"), Path("apps/spreadsheets/index.html"),
                                     Path("apps/presentations/index.html")})
# InkDOS-tools is served from its own origin (a separate GitHub organization) so its third-party
# code cannot reach InkDOS storage; Home's Advanced tools panel and the three viewers frame it.
TOOLS_ORIGIN = "https://inkdos-tools.github.io"
FRAME_TOOLS_ENTRY_POINTS = frozenset({Path("index.html"), Path("apps/documents/index.html"),
                                      Path("apps/spreadsheets/index.html"), Path("apps/presentations/index.html")})


def policy_for(text_without_csp: str, frame_self: bool = False, frame_tools: bool = False) -> str:
    hashes = inline_script_hashes(text_without_csp)
    script = "script-src 'self'"
    if hashes:
        script += " " + " ".join(hashes)
    frame = "frame-src 'self'" + (" " + TOOLS_ORIGIN if frame_tools else "")
    rest = [(frame if frame_self and d == "frame-src 'none'" else d) for d in BASE_DIRECTIVES[1:]]
    return "; ".join((BASE_DIRECTIVES[0], script, *rest))


def insertion_for(text: str, charset: re.Match[str], meta: str) -> str:
    """Return a CSP insertion that preserves the entry point's local layout."""
    line_start = text.rfind("\n", 0, charset.start()) + 1
    line_end = text.find("\n", charset.end())
    if line_end < 0:
        line_end = len(text)
    prefix = text[line_start : charset.start()]
    suffix = text[charset.end() : line_end]
    # Pretty mode is safe only when the charset occupies its own physical line:
    # both sides of it may contain indentation/whitespace, but no other markup.
    # This deliberately classifies both the compact TXT bundle and Spreadsheet
    # (where viewport follows charset on the same line) as compact.
    if prefix.strip() or suffix.strip():
        return meta
    return "\n" + prefix + meta


def render(text: str, frame_self: bool = False, frame_tools: bool = False) -> str:
    """Render exactly one deterministic CSP meta tag into an entry point.

    Idempotence is intentionally enforced at the artifact boundary by
    ``process(..., check=True)`` and the dedicated regression test. Keeping the
    renderer itself single-pass avoids a circular self-check during deterministic
    bundle construction (notably the compact Plain Text entry point).
    """
    clean = strip_existing_csp(text)
    policy = policy_for(clean, frame_self, frame_tools)
    meta = f'<meta http-equiv="Content-Security-Policy" content="{policy}">'
    charset = CHARSET_RE.search(clean)
    if not charset:
        raise RuntimeError("Entry point does not contain a quoted meta charset tag")
    insertion = insertion_for(clean, charset, meta)
    return clean[: charset.end()] + insertion + clean[charset.end() :]


def process(path: Path, check: bool) -> bool:
    source = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)
    expected = render(source, relative in FRAME_SELF_ENTRY_POINTS, relative in FRAME_TOOLS_ENTRY_POINTS)
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
