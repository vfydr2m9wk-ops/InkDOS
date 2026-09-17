#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy_path = ROOT / "config" / "shared-runtime-policy.json"
    helper_path = SCRIPTS / "shared_runtime_policy.py"
    require(policy_path.is_file(), "central shared runtime policy is missing")
    require(helper_path.is_file(), "shared runtime policy helper is missing")

    from shared_runtime_policy import is_allowed_shared_relpath

    for relpath in (
        "ui-density.js",
        "ui-density.css",
        "localization/ui-localization.js",
        "localization/settings-strip.js",
        "localization/locales/pt-BR.js",
        "localization/locales/ja.js",
    ):
        require(is_allowed_shared_relpath(relpath), f"approved shared runtime rejected: {relpath}")

    for relpath in (
        "arbitrary-runtime.js",
        "vendor/unapproved.js",
        "../outside.js",
        "/absolute.js",
    ):
        require(not is_allowed_shared_relpath(relpath), f"unapproved shared runtime accepted: {relpath}")

    no_legacy = (SCRIPTS / "check_no_legacy_runtime.py").read_text(encoding="utf-8")
    isolation = (SCRIPTS / "validate_app_isolation.py").read_text(encoding="utf-8")
    for name, text in (("check_no_legacy_runtime.py", no_legacy), ("validate_app_isolation.py", isolation)):
        require("shared_runtime_policy" in text, f"{name} does not consume the central policy")
    require("ALLOWED_SHARED_FILES" not in no_legacy, "legacy validator still owns a private shared allowlist")
    require("APPROVED_SHARED_RUNTIME" not in isolation, "isolation validator still owns a private shared allowlist")

    ci_path = ROOT / ".github" / "workflows" / "ci-integrity.yml"
    require(ci_path.is_file(), "dedicated CI integrity workflow is missing")
    ci = ci_path.read_text(encoding="utf-8")
    require("pull_request:" in ci, "CI integrity workflow does not run on pull requests")
    require("push:" in ci and "- main" in ci, "CI integrity workflow does not run on main pushes")
    require("contents: read" in ci, "CI integrity workflow must be read-only")
    require("python tests/test_ci_flow_contract.py" in ci, "CI integrity workflow does not enforce its own contract")
    require("python scripts/run_release_validation.py" in ci, "CI integrity workflow does not run the complete repository gate")

    apply_path = ROOT / ".github" / "workflows" / "apply-inkdos-update.yml"
    apply = apply_path.read_text(encoding="utf-8")
    trigger_block = apply.split("permissions:", 1)[0]
    require("workflow_dispatch:" in trigger_block, "update package workflow lost manual dispatch")
    require("push:" not in trigger_block, "update package workflow still owns ordinary main-push CI")
    require("Validate repository" not in apply, "update package workflow still contains ordinary repository validation job")
    require("Validate update package without write credentials" in apply, "read-only package validation boundary is missing")
    require("Apply prevalidated package" in apply, "write-scoped package apply boundary is missing")

    print("InkDOS CI flow contract: PASS")


if __name__ == "__main__":
    main()
