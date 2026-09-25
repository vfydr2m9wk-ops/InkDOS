#!/usr/bin/env python3
"""Regression contract for the validated PDF empty-start performance fix."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "pdf" / "app.js"


def main() -> None:
    source = APP.read_text(encoding="utf-8")

    launch = "global.InkDOSFileLaunch?.setOpenHandler?."
    gate = "if(session.active){\n  firstContentRendered=await Promise.race("
    lazy = "if(!(await ensureEditingTools()))return"
    timeout_fallback = "if(!firstContentRendered){await afterIdle(650);await ensureEditingTools()}"

    assert launch in source, "PDF direct file-launch handler must remain registered"
    assert gate in source, "PDF first-render wait must be gated by an active document"
    assert source.index(launch) < source.index(gate), (
        "Direct file-launch registration must happen before the active-document render wait"
    )

    assert "let firstContentRendered=false;" in source
    assert timeout_fallback in source, (
        "An active PDF that misses first render must retain the deferred editing-tools fallback"
    )
    assert "async function ensureEditingTools()" in source
    assert lazy in source, (
        "Editing tools must remain available on demand after an empty startup"
    )
    assert "editBtn.disabled=!active||loading" in source
    assert "await Promise.race([firstRender,new Promise(resolve=>setTimeout(resolve,2500))]);" not in source, (
        "The old unconditional 2.5 s empty-start wait must not return"
    )

    print("PDF empty-start performance contract passed.")


if __name__ == "__main__":
    main()
