#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from collections import deque
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("INKDOS_ONLINE_BASE", "http://127.0.0.1:8000/").rstrip("/") + "/"
OUT = Path(os.environ.get("INKDOS_BUTTON_AUDIT_OUT", "audit-button-clicks"))
OUT.mkdir(parents=True, exist_ok=True)
MAX_DEPTH = int(os.environ.get("INKDOS_BUTTON_AUDIT_DEPTH", "3"))
MAX_STATES = int(os.environ.get("INKDOS_BUTTON_AUDIT_STATES", "90"))
BUTTON_SELECTOR = 'button,input[type="button"],input[type="submit"],[role="button"]'

spec = importlib.util.spec_from_file_location(
    "stateful", ROOT / "tests" / "test_online_stateful_control_surfaces_browser.py"
)
stateful = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(stateful)

PAGES = stateful.PAGES


def make_fixtures(td: Path):
    epub = td / "audit.epub"
    stateful.minimal_epub(epub)
    return {"epub": epub}


def init_context(browser):
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        service_workers="block",
        accept_downloads=True,
    )
    ctx.add_init_script(
        """(() => {
          try {
            localStorage.setItem('inkdos2:appearance','light');
            localStorage.setItem('inkdos2:ui-density','desktop');
          } catch (_) {}
        })();"""
    )
    return ctx


def button_snapshot(page):
    return page.evaluate(
        """selector => {
          const visible = el => {
            const s=getComputedStyle(el), r=el.getBoundingClientRect();
            return s.display!=='none' && s.visibility!=='hidden' &&
              Number(s.opacity||1)!==0 && r.width>0 && r.height>0;
          };
          const path = el => {
            if (el.id) return '#'+CSS.escape(el.id);
            const parts=[];
            let node=el;
            while(node && node.nodeType===1 && node!==document.body){
              const tag=node.tagName.toLowerCase();
              let nth=1, sib=node;
              while((sib=sib.previousElementSibling)) if(sib.tagName===node.tagName) nth++;
              parts.unshift(tag+':nth-of-type('+nth+')');
              node=node.parentElement;
            }
            return 'body > '+parts.join(' > ');
          };
          const norm = s => String(s||'').trim().replace(/\s+/g,' ').slice(0,160);
          return [...document.querySelectorAll(selector)].map((el,index)=>({
            index,
            path:path(el),
            id:el.id||null,
            aria:el.getAttribute('aria-label'),
            text:norm(el.innerText||el.value),
            title:el.getAttribute('title'),
            command:el.getAttribute('data-command'),
            visible:visible(el),
            disabled:!!el.disabled || el.getAttribute('aria-disabled')==='true',
            expanded:el.getAttribute('aria-expanded'),
            pressed:el.getAttribute('aria-pressed'),
            checked:el.getAttribute('aria-checked'),
          }));
        }""",
        BUTTON_SELECTOR,
    )


def visible_signature(buttons):
    rows = []
    for b in buttons:
        if b["visible"]:
            rows.append(
                (
                    b["path"],
                    b["disabled"],
                    b.get("expanded"),
                    b.get("pressed"),
                    b.get("checked"),
                )
            )
    return json.dumps(sorted(rows), separators=(",", ":"))


def describe(b):
    return b.get("id") or b.get("aria") or b.get("text") or b.get("title") or b["path"]


def boot(browser, app, fixtures, active=True):
    ctx = init_context(browser)
    page = ctx.new_page()
    errors = []
    console_errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
    )
    page.goto(urljoin(BASE, PAGES[app]), wait_until="load", timeout=30000)
    page.wait_for_timeout(180)
    if active and app != "home":
        stateful.prepare_active(app, page, fixtures)
        page.wait_for_timeout(180)
    return ctx, page, errors, console_errors


def replay(browser, app, fixtures, active, sequence):
    ctx, page, errors, console_errors = boot(browser, app, fixtures, active=active)
    dialogs = []
    choosers = []
    downloads = []
    page.on("dialog", lambda d: (dialogs.append({"type": d.type, "message": d.message}), d.dismiss()))
    page.on("filechooser", lambda c: choosers.append(True))
    page.on("download", lambda d: (downloads.append(d.suggested_filename), d.cancel()))
    for path in sequence:
        loc = page.locator(path)
        if loc.count() == 0:
            raise RuntimeError(f"Replay control disappeared: {path}")
        if not loc.first.is_visible():
            raise RuntimeError(f"Replay control not visible: {path}")
        if not loc.first.is_enabled():
            raise RuntimeError(f"Replay control disabled: {path}")
        loc.first.click(timeout=3000, no_wait_after=True)
        page.wait_for_timeout(150)
    return ctx, page, errors, console_errors, dialogs, choosers, downloads


def audit_app(browser, app, fixtures, active):
    inventory = {}
    clicks = {}
    states = []
    queue = deque([[]])
    seen_signatures = set()

    while queue and len(states) < MAX_STATES:
        sequence = queue.popleft()
        try:
            ctx, page, errors, console_errors, dialogs, choosers, downloads = replay(
                browser, app, fixtures, active, sequence
            )
        except Exception as exc:
            states.append({"sequence": sequence, "replayError": repr(exc)})
            continue

        buttons = button_snapshot(page)
        sig = visible_signature(buttons)
        if sig in seen_signatures:
            page.close()
            ctx.close()
            continue
        seen_signatures.add(sig)
        state_id = f"{'active' if active else 'initial'}:{len(states)}"
        states.append(
            {
                "id": state_id,
                "depth": len(sequence),
                "sequence": sequence,
                "visible": [describe(b) for b in buttons if b["visible"]],
                "errors": list(errors),
                "consoleErrors": list(console_errors),
            }
        )

        for b in buttons:
            rec = inventory.setdefault(
                b["path"],
                {
                    "path": b["path"],
                    "id": b.get("id"),
                    "aria": b.get("aria"),
                    "text": b.get("text"),
                    "title": b.get("title"),
                    "command": b.get("command"),
                    "seen": 0,
                    "visibleStates": [],
                    "enabledStates": [],
                    "disabledStates": [],
                },
            )
            rec["seen"] += 1
            if b["visible"]:
                rec["visibleStates"].append(state_id)
                if b["disabled"]:
                    rec["disabledStates"].append(state_id)
                else:
                    rec["enabledStates"].append(state_id)

        for b in buttons:
            if not b["visible"] or b["disabled"]:
                continue
            path = b["path"]
            if path in clicks:
                continue

            click = {
                "path": path,
                "control": describe(b),
                "state": state_id,
                "sequence": sequence,
                "status": "not-run",
                "dialogs": [],
                "fileChooser": False,
                "downloads": [],
                "errors": [],
                "consoleErrors": [],
            }
            try:
                (
                    cctx,
                    cpage,
                    cerrs,
                    cconsole,
                    cdialogs,
                    cchoosers,
                    cdownloads,
                ) = replay(browser, app, fixtures, active, sequence)
                before = button_snapshot(cpage)
                before_sig = visible_signature(before)
                loc = cpage.locator(path)
                if loc.count() == 0:
                    click["status"] = "missing-on-replay"
                elif not loc.first.is_visible():
                    click["status"] = "not-visible-on-replay"
                elif not loc.first.is_enabled():
                    click["status"] = "disabled-on-replay"
                else:
                    loc.first.click(timeout=3000, no_wait_after=True)
                    cpage.wait_for_timeout(180)
                    after = button_snapshot(cpage)
                    after_sig = visible_signature(after)
                    click["status"] = "clicked"
                    click["stateChanged"] = before_sig != after_sig
                    click["urlAfter"] = cpage.url
                    click["dialogs"] = list(cdialogs)
                    click["fileChooser"] = bool(cchoosers)
                    click["downloads"] = list(cdownloads)
                    click["errors"] = list(cerrs)
                    click["consoleErrors"] = list(cconsole)
                    if (
                        before_sig != after_sig
                        and len(sequence) < MAX_DEPTH
                        and cpage.url.startswith(BASE)
                    ):
                        queue.append(sequence + [path])
                cpage.close()
                cctx.close()
            except Exception as exc:
                click["status"] = "click-exception"
                click["exception"] = repr(exc)
            clicks[path] = click

        page.close()
        ctx.close()

    return {
        "activeRoot": active,
        "inventory": inventory,
        "clicks": clicks,
        "states": states,
        "stateLimitReached": len(states) >= MAX_STATES,
    }


def merge_runs(runs):
    inventory = {}
    clicks = {}
    for run in runs:
        for path, rec in run["inventory"].items():
            dst = inventory.setdefault(
                path,
                {
                    "path": path,
                    "id": rec.get("id"),
                    "aria": rec.get("aria"),
                    "text": rec.get("text"),
                    "title": rec.get("title"),
                    "command": rec.get("command"),
                    "seen": 0,
                    "visibleStates": [],
                    "enabledStates": [],
                    "disabledStates": [],
                },
            )
            dst["seen"] += rec["seen"]
            for k in ("visibleStates", "enabledStates", "disabledStates"):
                dst[k].extend(rec[k])
        for path, click in run["clicks"].items():
            current = clicks.get(path)
            rank = {"clicked": 4, "disabled-on-replay": 3, "not-visible-on-replay": 2, "missing-on-replay": 1, "click-exception": 0, "not-run": 0}
            if current is None or rank.get(click["status"], 0) > rank.get(current["status"], 0):
                clicks[path] = click
    return inventory, clicks


def main():
    with tempfile.TemporaryDirectory() as td:
        fixtures = make_fixtures(Path(td))
        report = {"base": BASE, "apps": {}, "summary": {}}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for app in PAGES:
                runs = [audit_app(browser, app, fixtures, active=False)]
                if app != "home":
                    runs.append(audit_app(browser, app, fixtures, active=True))
                inventory, clicks = merge_runs(runs)
                controls = []
                for path, rec in inventory.items():
                    click = clicks.get(path)
                    if click and click["status"] == "clicked":
                        classification = "click-delivered"
                    elif rec["enabledStates"]:
                        classification = click["status"] if click else "enabled-not-clicked"
                    elif rec["visibleStates"]:
                        classification = "visible-disabled"
                    else:
                        classification = "never-visible"
                    controls.append(
                        {
                            **rec,
                            "classification": classification,
                            "click": click,
                        }
                    )
                report["apps"][app] = {
                    "controls": sorted(controls, key=lambda x: x["path"]),
                    "runs": [{"activeRoot": r["activeRoot"], "states": len(r["states"]), "stateLimitReached": r["stateLimitReached"]} for r in runs],
                }
            browser.close()

        all_controls = [c for a in report["apps"].values() for c in a["controls"]]
        clicked = [c for c in all_controls if c["classification"] == "click-delivered"]
        visible_disabled = [c for c in all_controls if c["classification"] == "visible-disabled"]
        never_visible = [c for c in all_controls if c["classification"] == "never-visible"]
        failures = [
            c
            for c in all_controls
            if c["classification"]
            in {"click-exception", "missing-on-replay", "not-visible-on-replay", "enabled-not-clicked"}
            or (c.get("click") and c["click"].get("errors"))
        ]
        report["summary"] = {
            "controlsDiscovered": len(all_controls),
            "clickDelivered": len(clicked),
            "visibleDisabled": len(visible_disabled),
            "neverVisible": len(never_visible),
            "failures": len(failures),
            "apps": {
                app: {
                    "controls": len(data["controls"]),
                    "clickDelivered": sum(1 for c in data["controls"] if c["classification"] == "click-delivered"),
                    "visibleDisabled": sum(1 for c in data["controls"] if c["classification"] == "visible-disabled"),
                    "neverVisible": sum(1 for c in data["controls"] if c["classification"] == "never-visible"),
                    "failures": sum(
                        1
                        for c in data["controls"]
                        if c["classification"]
                        in {"click-exception", "missing-on-replay", "not-visible-on-replay", "enabled-not-clicked"}
                        or (c.get("click") and c["click"].get("errors"))
                    ),
                }
                for app, data in report["apps"].items()
            },
        }
        (OUT / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
        if failures:
            print("Button audit found click failures; see", OUT / "report.json")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
