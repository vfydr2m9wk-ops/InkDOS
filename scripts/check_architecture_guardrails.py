#!/usr/bin/env python3
"""Enforce the current InkDOS runtime complexity ratchet."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "architecture-policy.json"
IMPORT_RE = re.compile(
    r"(?:\bimport\s+(?:[^'\"]+?\s+from\s+)?|\bexport\s+[^'\"]*?\s+from\s+|\bimport\s*\()"
    r"['\"]([^'\"]+)['\"]"
)

def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def runtime_files(policy: dict) -> list[Path]:
    extensions = set(policy["extensions"])
    found: list[Path] = []
    for root_name in policy["runtimeRoots"]:
        root = ROOT / root_name
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in extensions:
                continue
            if "vendor" in path.parts:
                continue
            found.append(path)
    return sorted(found)


def metrics(path: Path, max_line_length: int) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return len(lines), sum(len(line) > max_line_length for line in lines)


def resolve_relative_import(source: Path, specifier: str) -> Path | None:
    if not specifier.startswith("."):
        return None
    candidate = (source.parent / specifier).resolve()
    candidates = [candidate]
    if not candidate.suffix:
        candidates += [candidate.with_suffix(".js"), candidate / "index.js"]
    for item in candidates:
        try:
            item.relative_to(ROOT)
        except ValueError:
            continue
        if item.is_file() and item.suffix == ".js":
            return item
    return None


def local_import_graph(files: list[Path]) -> tuple[dict[Path, set[Path]], list[str]]:
    graph: dict[Path, set[Path]] = {path.resolve(): set() for path in files if path.suffix == ".js"}
    errors: list[str] = []
    for path in files:
        if path.suffix != ".js":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT)
        source_workspace = rel.parts[1] if len(rel.parts) > 1 and rel.parts[0] == "apps" else None
        for specifier in IMPORT_RE.findall(text):
            target = resolve_relative_import(path, specifier)
            if target is None:
                continue
            graph[path.resolve()].add(target.resolve())
            target_rel = target.relative_to(ROOT)
            target_workspace = (
                target_rel.parts[1]
                if len(target_rel.parts) > 1 and target_rel.parts[0] == "apps"
                else None
            )
            if source_workspace and target_workspace and source_workspace != target_workspace:
                errors.append(
                    f"Cross-workspace runtime dependency: {rel} -> {target_rel}"
                )
            if rel.parts and rel.parts[0] == "shared" and target_workspace:
                errors.append(f"Shared runtime imports workspace code: {rel} -> {target_rel}")
    return graph, errors


def find_cycles(graph: dict[Path, set[Path]]) -> list[list[Path]]:
    cycles: list[list[Path]] = []
    state: dict[Path, int] = {}
    stack: list[Path] = []

    def visit(node: Path) -> None:
        state[node] = 1
        stack.append(node)
        for target in graph.get(node, ()):
            if target not in graph:
                continue
            if state.get(target, 0) == 0:
                visit(target)
            elif state.get(target) == 1:
                start = stack.index(target)
                cycle = stack[start:] + [target]
                if cycle not in cycles:
                    cycles.append(cycle)
        stack.pop()
        state[node] = 2

    for node in graph:
        if state.get(node, 0) == 0:
            visit(node)
    return cycles


def main() -> int:
    policy = load_policy()
    debt = policy.get("grandfatheredDebt", {})
    errors: list[str] = []
    files = runtime_files(policy)

    seen_debt: set[str] = set()
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        cfg = policy["extensions"][path.suffix]
        line_count, long_lines = metrics(path, int(cfg["maxPhysicalLineLength"]))
        inherited = debt.get(rel)
        if inherited:
            seen_debt.add(rel)
            if line_count > int(inherited["maxLines"]):
                errors.append(
                    f"Grandfathered source grew beyond its ratchet: {rel} "
                    f"({line_count} > {inherited['maxLines']} lines)"
                )
            if long_lines > int(inherited["maxLongLines"]):
                errors.append(
                    f"Grandfathered source added long physical lines: {rel} "
                    f"({long_lines} > {inherited['maxLongLines']})"
                )
        else:
            if line_count > int(cfg["newFileMaxLines"]):
                errors.append(
                    f"Runtime source exceeds the new-file line limit: {rel} "
                    f"({line_count} > {cfg['newFileMaxLines']})"
                )
            if long_lines:
                errors.append(
                    f"Runtime source has {long_lines} physical line(s) over "
                    f"{cfg['maxPhysicalLineLength']} characters: {rel}"
                )

    missing_debt = sorted(set(debt) - seen_debt)
    if missing_debt:
        errors.extend(
            f"Architecture debt entry points to a missing runtime file: {rel}"
            for rel in missing_debt
        )

    graph, dependency_errors = local_import_graph(files)
    errors.extend(dependency_errors)
    for cycle in find_cycles(graph):
        pretty = " -> ".join(path.relative_to(ROOT).as_posix() for path in cycle)
        errors.append(f"Relative runtime import cycle: {pretty}")

    print(
        f"Architecture guardrails checked {len(files)} runtime JS/CSS files; "
        f"{len(debt)} inherited debt entries are ratcheted."
    )
    if errors:
        print("\nArchitecture guardrails failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Architecture guardrails passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
