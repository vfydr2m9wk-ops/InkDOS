#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "config" / "components.json"
FROZEN = ROOT / "config" / "frozen-legacy.json"
AGENTS = ROOT / "AGENTS.md"
SCRIPTS = (
    ROOT / "scripts" / "agent_support.py",
    ROOT / "scripts" / "agent_context.py",
    ROOT / "scripts" / "agent_test.py",
    ROOT / "scripts" / "agent_verify.py",
)
EXPECTED = {
    "hub",
    "documents",
    "spreadsheets",
    "presentations",
    "txt",
    "epub",
    "pdf",
}


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def main():
    rules = AGENTS.read_text(encoding="utf-8")
    for marker in (
        "Preservation-first rules",
        "Do not perform opportunistic cleanup",
        "INKDOS:FROZEN-LEGACY",
        "scripts/agent_context.py",
        "scripts/agent_test.py",
        "scripts/agent_verify.py",
    ):
        require(marker in rules, f"AGENTS.md is missing maintenance rule: {marker}")

    payload = json.loads(COMPONENTS.read_text(encoding="utf-8"))
    require(payload.get("schemaVersion") == 1, "component-map schema version changed")
    components = payload.get("components", {})
    require(set(components) == EXPECTED, "component map must describe Hub plus six apps")

    for name, cfg in components.items():
        entry = ROOT / cfg["entry"]
        require(entry.is_file(), f"{name}: entry does not exist: {cfg['entry']}")
        require(cfg.get("testGlobs"), f"{name}: focused test globs are missing")
        matched = {
            path
            for pattern in cfg["testGlobs"]
            for path in ROOT.glob(pattern)
            if path.is_file()
        }
        require(matched, f"{name}: focused test globs select no tests")

    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    require(frozen.get("schemaVersion") == 1, "frozen-legacy schema version changed")
    require(frozen.get("marker") == "INKDOS:FROZEN-LEGACY", "legacy marker changed")
    require(isinstance(frozen.get("entries"), list), "frozen-legacy entries must be a list")

    for script in SCRIPTS:
        source = script.read_text(encoding="utf-8")
        compile(source, script.as_posix(), "exec")

    support = SCRIPTS[0].read_text(encoding="utf-8")
    verify = SCRIPTS[-1].read_text(encoding="utf-8")
    require("origin/main" in support, "agent scope comparison should prefer origin/main")
    require("SCOPE VIOLATION" in verify, "agent verifier must reject scope expansion")
    require("FROZEN LEGACY VIOLATION" in verify, "agent verifier must protect frozen legacy")

    print("AI maintenance guardrails contract passed.")


if __name__ == "__main__":
    main()
