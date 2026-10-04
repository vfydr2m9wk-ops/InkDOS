"""Desktop beta tools channel contract.

Beta tools reach the desktop app without a desktop release, so the host must treat them as
untrusted code: signed bundles only (pinned key, separate from the updater key), served into
windows that no capability names and that every app command refuses. Publishing must never
touch the desktop updater's `releases/latest`.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI = ROOT / "desktop" / "src-tauri"
WORKFLOW = ROOT / ".github" / "workflows" / "beta-channel.yml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    main_rs = (TAURI / "src" / "main.rs").read_text(encoding="utf-8")
    beta_rs = (TAURI / "src" / "beta.rs").read_text(encoding="utf-8")

    # every app command refuses beta windows
    commands = re.findall(r"#\[tauri::command\]\s*(?:async\s+)?fn\s+(\w+)\(([^)]*)\)[^{]*\{\s*([^\n]*)", main_rs)
    require(len(commands) >= 6, f"expected the InkDOS app commands, found {[c[0] for c in commands]}")
    for name, params, first_line in commands:
        require("webview: tauri::Webview" in params, f"{name} must receive the calling webview")
        require("require_trusted_window(&webview)?" in first_line, f"{name} must check the calling window first")
    guard = re.search(r"fn require_trusted_window[^{]*\{(.*?)\n\}", main_rs, re.S)
    require(guard and "beta" not in guard.group(1) and '"main"' in guard.group(1), "trusted windows are main, file-* and workspace-* only")

    # no capability grants anything to beta windows (or to every window)
    for capability in (TAURI / "capabilities").glob("*.json"):
        windows = json.loads(capability.read_text(encoding="utf-8")).get("windows", [])
        require(all(not w.startswith("beta") and w not in {"*", "beta-*"} for w in windows),
                f"{capability.name} must not name beta windows: {windows}")
    require('pub const WINDOW_PREFIX: &str = "beta-";' in beta_rs, "beta windows use the beta- label prefix")

    # signed bundles only, pinned key separate from the updater's
    require('include_str!("../beta-channel.pub")' in beta_rs, "the beta public key is pinned in the binary")
    require("verify_signature(" in beta_rs and "manifest.files.contains_key(path)" in beta_rs,
            "bundles are signature-checked and only listed files are served")
    pub = (TAURI / "beta-channel.pub").read_text(encoding="utf-8").strip()
    updater_key = json.loads((TAURI / "tauri.conf.json").read_text(encoding="utf-8"))["plugins"]["updater"]["pubkey"]
    require(pub and pub != updater_key, "the beta channel must not reuse the updater key")

    # publishing: prerelease, never latest, separate secrets, pinned actions
    workflow = WORKFLOW.read_text(encoding="utf-8")
    require("--prerelease" in workflow and "--latest=false" in workflow, "beta releases must not become releases/latest")
    require("secrets.INKDOS_BETA_SIGNING_KEY" in workflow and "secrets.TAURI_SIGNING_PRIVATE_KEY" not in workflow,
            "beta bundles are signed with the beta key, never the updater key")
    for line in re.findall(r"uses:\s*(\S+)", workflow):
        require(re.search(r"@[0-9a-f]{40}$", line) is not None, f"action not pinned to a commit: {line}")
    require("tests/test_home_pdf_lab_browser.py" in workflow, "beta tools are tested before publishing")

    # the bundle builder stages every tool entry with hashes
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "beta"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_beta_bundle.py"), "stage", "--out", str(out),
                        "--version", "1", "--commit", "0" * 40], check=True, capture_output=True)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        require(all(tool["entry"] in manifest["files"] for tool in manifest["tools"]), "tool entries must be in the bundle")
        require(all(re.fullmatch(r"[0-9a-f]{64}", h) for h in manifest["files"].values()), "every file carries a SHA-256")
    print("Desktop beta channel contract: OK")


if __name__ == "__main__":
    main()
