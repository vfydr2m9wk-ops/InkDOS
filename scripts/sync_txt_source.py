#!/usr/bin/env python3
"""One-time, idempotent normalization of Plain Text source/template integration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "apps/txt/page.template.html"
STYLES = ROOT / "apps/txt/styles.css"

RUNTIME_BANNER = "<script>(function(){window.addEventListener('error',function(e){var b=document.getElementById('runtimeError');if(!b){b=document.createElement('div');b.id='runtimeError';b.style.cssText='position:fixed;left:8px;right:8px;bottom:8px;z-index:99999;padding:10px 12px;border-radius:10px;background:#8f1d1d;color:white;font:13px -apple-system,BlinkMacSystemFont,sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.25)';document.body.appendChild(b)}b.textContent='Runtime error: '+(e.message||'unknown error')});})();</script>\n"
MENU_BUTTON = "      <button id=\"menuBtn\" class=\"menu-btn\" type=\"button\" aria-label=\"Open general menu\" title=\"Menu\" aria-haspopup=\"dialog\" aria-expanded=\"false\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M4 7h16M4 12h16M4 17h16\"/></svg></button>"
HOME_LINK = "<a class=\"menu-btn\" href=\"../../index.html\" aria-label=\"Home\" title=\"Home\" style=\"color:inherit;text-decoration:none\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M3.5 11.5 12 4l8.5 7.5\"/><path d=\"M5.5 10.5V20h13v-9.5\"/><path d=\"M9.5 20v-6h5v6\"/></svg></a>"
OLD_MAIN = "  <main class=\"content-viewport\"><div class=\"stage\"><section id=\"surface\" class=\"editor-surface\"><textarea id=\"editor\" aria-label=\"Plain text editor\" spellcheck=\"true\" autocapitalize=\"sentences\" autocomplete=\"off\"></textarea></section></div></main>"
NEW_MAIN = "  <main class=\"content-viewport\"><div id=\"startState\" class=\"start-state\"><div class=\"start-card\"><svg class=\"start-icon\" aria-hidden=\"true\"><use href=\"#inkdosTxtIcon\"/></svg><h1>Plain Text</h1><p>Create a text file or open a TXT file locally.</p><div class=\"start-actions\"><button id=\"startNew\" type=\"button\">New text file</button><button id=\"startOpen\" class=\"primary\" type=\"button\">Open text file</button></div></div></div><div class=\"stage\"><section id=\"surface\" class=\"editor-surface\"><textarea id=\"editor\" aria-label=\"Plain text editor\" spellcheck=\"true\" autocapitalize=\"sentences\" autocomplete=\"off\"></textarea></section></div></main>"
RUNTIME_READY = "<script>document.body.dataset.runtimeReady=(globalThis.InkDOS2&&globalThis.InkDOS2.TxtAppDebug)?'true':'false';</script>"
START_GATE = "<script>(function(){const s=document.getElementById('startState'),f=document.getElementById('fileInput');document.getElementById('startNew')?.addEventListener('click',()=>{document.getElementById('newBtn')?.click();s.hidden=true});document.getElementById('startOpen')?.addEventListener('click',()=>document.getElementById('openBtn')?.click());f?.addEventListener('change',()=>{if(f.files&&f.files.length)s.hidden=true});})();</script>"
CONTENT_MARKER = "/* Content boundary: ContentViewport owns available content space; textarea owns document scroll. */\n"
START_CSS = ".start-state{position:absolute;inset:0;z-index:4;display:grid;place-items:center;padding:18px max(18px,var(--safe-r));background:var(--txt-bg);pointer-events:none}.start-card{width:min(430px,100%);padding:28px;border:1px solid var(--txt-line);border-radius:22px;background:var(--txt-surface);box-shadow:var(--txt-shadow);text-align:center;pointer-events:auto}.start-icon{width:68px;height:68px}.start-card h1{margin:14px 0 6px}.start-card p{margin:0 0 18px;color:var(--txt-muted)}.start-actions{display:flex;justify-content:center;gap:8px;flex-wrap:wrap}.start-actions button{min-height:44px;border:1px solid var(--txt-line);border-radius:11px;background:var(--txt-surface-soft);padding:0 16px}.start-actions .primary{background:var(--txt-accent-strong);color:#fff;border-color:var(--txt-accent-strong)}.\n"


def require_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Plain Text normalization target missing: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    page = TEMPLATE.read_text(encoding="utf-8")
    page = page.replace(RUNTIME_BANNER, "", 1)
    if HOME_LINK not in page:
        page = require_replace(page, MENU_BUTTON, MENU_BUTTON + HOME_LINK, "Home bridge")
    if 'id="startState"' not in page:
        page = require_replace(page, OLD_MAIN, NEW_MAIN, "first-open card")
    if START_GATE not in page:
        page = require_replace(page, RUNTIME_READY, START_GATE + "\n" + RUNTIME_READY, "first-open gate")
    TEMPLATE.write_text(page, encoding="utf-8")

    css = STYLES.read_text(encoding="utf-8")
    if START_CSS not in css:
        css = require_replace(css, CONTENT_MARKER, CONTENT_MARKER + START_CSS, "first-open styles")
    STYLES.write_text(css, encoding="utf-8")
    print("Plain Text template/source integration normalized.")


if __name__ == "__main__":
    main()
