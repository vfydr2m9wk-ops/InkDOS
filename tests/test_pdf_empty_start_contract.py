#!/usr/bin/env python3
"""Focused contract for the accepted empty-PDF startup behavior."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps" / "pdf" / "app.js").read_text(encoding="utf-8")

launch = "global.InkDOSFileLaunch?.setOpenHandler?."
active_gate = "if(session.active){\n  firstContentRendered=await Promise.race"
first_render_wait = "setTimeout(()=>resolve(false),2500)"
deferred_tools = "if(!firstContentRendered){await afterIdle(650);await ensureEditingTools()}"
reader_idle = "await afterIdle(900);"

assert launch in APP, "direct file-launch handler must remain registered"
assert active_gate in APP, "first-render timeout must be gated by an active document"
assert first_render_wait in APP, "active-document first-render safeguard must remain"
assert deferred_tools in APP, "active-document fallback tool hydration must remain"
assert reader_idle in APP, "reader-tool deferral must remain"
assert APP.index(launch) < APP.index(active_gate), "direct launch registration must precede startup waiting"

gate_start = APP.index(active_gate)
gate_end = APP.index(reader_idle, gate_start)
gated = APP[gate_start:gate_end]
assert first_render_wait in gated and deferred_tools in gated
assert "if(session.active)" in gated

print("PDF empty-start readiness contract passed.")
