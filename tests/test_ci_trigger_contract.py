#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def trigger_block(text: str) -> str:
    return text.split("permissions:", 1)[0]


def main() -> None:
    integrity = (WORKFLOWS / "ci-integrity.yml").read_text(encoding="utf-8")
    desktop = (WORKFLOWS / "desktop-tauri.yml").read_text(encoding="utf-8")
    stability = (WORKFLOWS / "stability-freeze-regression.yml").read_text(encoding="utf-8")

    integrity_trigger = trigger_block(integrity)
    desktop_trigger = trigger_block(desktop)
    stability_trigger = trigger_block(stability)

    # The universal merge/main gate stays broad; heavy specialized workflows are path-aware.
    require("push:" in integrity_trigger and "- main" in integrity_trigger, "integrity gate no longer runs on main")
    require("paths:" not in integrity_trigger, "integrity gate must remain universal rather than path-limited")

    require("paths:" in desktop_trigger, "desktop workflow is not path-aware")
    require("paths-ignore:" not in desktop_trigger, "desktop workflow still uses broad negative filtering")
    for marker in ("'desktop/**'", "'apps/**'", "'shared/**'", "'service-worker.js'", "'VERSION.json'"):
        require(marker in desktop_trigger, f"desktop trigger misses runtime dependency: {marker}")
    require("'tests/test_tauri_desktop_contract.py'" in desktop_trigger, "desktop contract changes do not trigger desktop validation")

    require("paths:" in stability_trigger, "stability workflow is not path-aware")
    require("paths-ignore:" not in stability_trigger, "stability workflow still uses broad negative filtering")
    for marker in ("'apps/**'", "'shared/**'", "'service-worker.js'", "'STABILITY_STATE.json'", "'SOURCE_LOCK.json'"):
        require(marker in stability_trigger, f"stability trigger misses runtime dependency: {marker}")
    require("'tests/test_*stability*'" in stability_trigger, "stability test changes do not trigger stability validation")
    require("'tests/test_cross_suite_*'" in stability_trigger, "cross-suite stability test changes do not trigger stability validation")

    # Release/CI-only changes should not fan out into native builds or the heavy stability matrix.
    for irrelevant in ("'.github/workflows/release.yml'", "'tests/test_release_pipeline_contract.py'"):
        require(irrelevant not in desktop_trigger, f"desktop trigger includes release-only path: {irrelevant}")
        require(irrelevant not in stability_trigger, f"stability trigger includes release-only path: {irrelevant}")

    print("InkDOS path-aware CI trigger contract: PASS")


if __name__ == "__main__":
    main()
