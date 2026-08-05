#!/usr/bin/env python3
"""Fail on common prototype-to-repository, offline, and security risks."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
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
OPAQUE_EXCEPTION_MARKER = "INKDESK_ALLOW_OPAQUE_TARGET"
OPAQUE_EXCEPTION_FILE = Path("shared/file-router.js")


@dataclass(frozen=True)
class PostMessageCall:
    line: int
    second_argument: str
    allowed_opaque_exception: bool


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


def _skip_space_and_comments(source: str, index: int) -> int:
    length = len(source)
    while index < length:
        if source[index].isspace():
            index += 1
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            return length if newline < 0 else _skip_space_and_comments(source, newline + 1)
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            return length if end < 0 else _skip_space_and_comments(source, end + 2)
        break
    return index


def _consume_quoted(source: str, index: int, quote: str) -> int:
    index += 1
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        index += 1
    return len(source)


def _consume_template(source: str, index: int) -> int:
    index += 1
    expression_depth = 0
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if expression_depth == 0 and char == "`":
            return index + 1
        if source.startswith("${", index):
            expression_depth += 1
            index += 2
            continue
        if expression_depth and char == "}":
            expression_depth -= 1
        if char in {"'", '"'}:
            index = _consume_quoted(source, index, char)
            continue
        if char == "`":
            index = _consume_template(source, index)
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        index += 1
    return len(source)


def _parse_call_arguments(source: str, open_paren: int) -> tuple[list[str], int]:
    arguments: list[str] = []
    start = open_paren + 1
    index = start
    stack: list[str] = [")"]
    matching = {"(": ")", "[": "]", "{": "}"}

    while index < len(source):
        char = source[index]
        if char in {"'", '"'}:
            index = _consume_quoted(source, index, char)
            continue
        if char == "`":
            index = _consume_template(source, index)
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if char in matching:
            stack.append(matching[char])
            index += 1
            continue
        if stack and char == stack[-1]:
            stack.pop()
            if not stack:
                arguments.append(source[start:index])
                return arguments, index + 1
            index += 1
            continue
        if char == "," and len(stack) == 1:
            arguments.append(source[start:index])
            start = index + 1
        index += 1
    return arguments, len(source)


def _is_wildcard_literal(expression: str) -> bool:
    without_comments = re.sub(r"/\*.*?\*/|//[^\n]*", "", expression, flags=re.S).strip()
    return bool(re.fullmatch(r"(['\"`])\*\1", without_comments))


def find_wildcard_postmessage_calls(source: str) -> list[PostMessageCall]:
    """Conservatively parse postMessage calls and return wildcard targetOrigin uses.

    This scanner tracks nested parentheses/braces/brackets, quoted strings, templates,
    comments, multiline calls, optional chaining and commas inside the first argument.
    It intentionally treats malformed input conservatively rather than claiming safety.
    """

    calls: list[PostMessageCall] = []
    index = 0
    length = len(source)
    identifier = "postMessage"

    while index < length:
        char = source[index]
        if char in {"'", '"'}:
            index = _consume_quoted(source, index, char)
            continue
        if char == "`":
            index = _consume_template(source, index)
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = length if newline < 0 else newline + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = length if end < 0 else end + 2
            continue
        if source.startswith(identifier, index):
            before = source[index - 1] if index else ""
            after_index = index + len(identifier)
            after = source[after_index] if after_index < length else ""
            if (before.isalnum() or before in "_$") or (after.isalnum() or after in "_$"):
                index += 1
                continue
            cursor = _skip_space_and_comments(source, after_index)
            if source.startswith("?.", cursor):
                cursor = _skip_space_and_comments(source, cursor + 2)
            if cursor < length and source[cursor] == "(":
                arguments, end = _parse_call_arguments(source, cursor)
                if len(arguments) >= 2 and _is_wildcard_literal(arguments[1]):
                    line = source.count("\n", 0, index) + 1
                    line_start = source.rfind("\n", 0, index) + 1
                    line_end = source.find("\n", index)
                    if line_end < 0:
                        line_end = length
                    marker_nearby = OPAQUE_EXCEPTION_MARKER in source[max(0, line_start - 240):min(length, line_end + 240)]
                    calls.append(PostMessageCall(line, arguments[1].strip(), marker_nearby))
                index = max(end, index + len(identifier))
                continue
        index += 1
    return calls


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []
    metrics: list[tuple[int, Path]] = []
    opaque_exceptions: list[tuple[Path, int]] = []

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CODE_SUFFIXES or excluded(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT)
        lines = text.count("\n") + 1
        metrics.append((lines, rel))
        if lines > 1000:
            errors.append(f"Source file exceeds 1000 lines and needs an explicit refactoring plan: {rel} ({lines})")
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
        if path.suffix.lower() in {".js", ".html"}:
            for call in find_wildcard_postmessage_calls(text):
                if call.allowed_opaque_exception and rel == OPAQUE_EXCEPTION_FILE:
                    opaque_exceptions.append((rel, call.line))
                else:
                    errors.append(f"Wildcard postMessage target found: {rel}:{call.line}")
        if DYNAMIC_CODE.search(text):
            notes.append(f"Dynamic code construction requires manual review: {rel}")
        if path.suffix.lower() == ".html":
            parser = RuntimeReferenceParser()
            parser.feed(text)
            for ref in parser.remote_runtime_refs:
                errors.append(f"Automatic remote runtime dependency: {rel} -> {ref}")

    if len(opaque_exceptions) > 1:
        locations = ", ".join(f"{path}:{line}" for path, line in opaque_exceptions)
        errors.append(f"More than one opaque-origin postMessage exception exists: {locations}")

    print("Largest non-vendor source files:")
    for lines, rel in sorted(metrics, reverse=True)[:10]:
        print(f"- {lines:4d} lines  {rel}")

    if opaque_exceptions:
        path, line = opaque_exceptions[0]
        print(f"\nDocumented opaque-origin exception: {path}:{line}")

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
