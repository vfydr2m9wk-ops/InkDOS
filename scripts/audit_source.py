#!/usr/bin/env python3
"""Fail on common prototype-to-repository, offline, and security risks."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CODE_SUFFIXES = {".js", ".html", ".css", ".py"}
EXCLUDED_PARTS = {".git", "vendor", "node_modules", "__pycache__", "test-results"}
PROTOTYPE_MARKER = re.compile(
    r"\b(" + "TO" + "DO|FI" + "XME|HA" + "CK|ST" + "UB)\b|" + "not " + "implemented|coming " + "soon",
    re.I,
)
ABSOLUTE_HOST = re.compile("file:///var/mobile/" + "Containers|/var/mobile/" + "Containers")
EMPTY_CATCH = re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}")
DYNAMIC_CODE = re.compile(r"\b(?:eval|Function)\s*\(")
DOCUMENT_WRITE = re.compile(r"\bdocument\.write\s*\(")
REMOTE_CALL = re.compile(r"\b(?:fetch|importScripts|WebSocket)\s*\(\s*['\"]https?://", re.I)
INSECURE_REMOTE = re.compile(r"\b(?:fetch|importScripts|WebSocket)\s*\(\s*['\"]http://", re.I)
UNSAFE_POST_MESSAGE = re.compile(r"\.postMessage\s*\([^,]+,\s*['\"]\*['\"]\)")

class RuntimeReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.remote_runtime_refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        rel = str(data.get("rel") or "").lower().split()
        ref = data.get("src") if tag == "script" else data.get("href") if tag == "link" and "stylesheet" in rel else None
        if ref and urlparse(ref).scheme in {"http", "https"}:
            self.remote_runtime_refs.append(ref)


def excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return True
    return rel.parts[:3] == ("tests", "browser", "results")


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []
    metrics: list[tuple[int, Path]] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CODE_SUFFIXES or excluded(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT)
        lines = text.count("\n") + 1
        metrics.append((lines, rel))
        if lines > 1000:
            errors.append(f"Source file exceeds 1000 lines and must be simplified or decomposed: {rel} ({lines})")
        if PROTOTYPE_MARKER.search(text):
            errors.append(f"Prototype marker found in runtime/source file: {rel}")
        if ABSOLUTE_HOST.search(text):
            errors.append(f"Device-specific absolute path found: {rel}")
        if EMPTY_CATCH.search(text):
            errors.append(f"Empty catch block found: {rel}")
        if DOCUMENT_WRITE.search(text):
            errors.append(f"document.write usage found: {rel}")
        if REMOTE_CALL.search(text):
            errors.append(f"Automatic remote runtime call found: {rel}")
        if INSECURE_REMOTE.search(text):
            errors.append(f"Insecure remote runtime call found: {rel}")
        if UNSAFE_POST_MESSAGE.search(text) and rel != Path("shared/vendor/jszip.min.js"):
            errors.append(f"Wildcard postMessage target found: {rel}")
        if DYNAMIC_CODE.search(text):
            notes.append(f"Dynamic code construction requires manual review: {rel}")
        if path.suffix.lower() == ".html":
            parser = RuntimeReferenceParser()
            parser.feed(text)
            for ref in parser.remote_runtime_refs:
                errors.append(f"Automatic remote runtime dependency: {rel} -> {ref}")

    print("Largest non-vendor source files:")
    for lines, rel in sorted(metrics, reverse=True)[:10]:
        print(f"- {lines:4d} lines  {rel}")

    unique_notes = sorted(set(notes))
    if unique_notes:
        print("\nManual security review notes:")
        for note in unique_notes:
            print(f"- {note}")

    if errors:
        print("\nSource audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nSource audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
