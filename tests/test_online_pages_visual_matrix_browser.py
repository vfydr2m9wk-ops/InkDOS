from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = os.environ.get("INKDOS_ONLINE_BASE", "https://vfydr2m9wk-ops.github.io/InkDOS/").rstrip("/") + "/"
BROWSER_NAME = os.environ.get("INKDOS_AUDIT_BROWSER", "chromium").strip().lower()
CLICK_SWEEP = os.environ.get("INKDOS_CLICK_SWEEP", "0") == "1"
OUT = Path(os.environ.get("INKDOS_AUDIT_OUT", f"audit-online-{BROWSER_NAME}"))
SHOT_DIR = OUT / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
SHOT_DIR.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("home", ""),
    ("documents", "apps/documents/index.html"),
    ("spreadsheets", "apps/spreadsheets/index.html"),
    ("presentations", "apps/presentations/index.html"),
    ("pdf", "apps/pdf/index.html"),
    ("txt", "apps/txt/index.html"),
    ("epub", "apps/epub/index.html"),
]
VIEWPORTS = {
    "16x9": {"width": 1440, "height": 810},
    "4x3": {"width": 1200, "height": 900},
    "9x16": {"width": 810, "height": 1440},
    "21x9": {"width": 1680, "height": 720},
}
APPEARANCES = {
    "light": ("light", "light"),
    "dark": ("dark", "dark"),
    "system-light": ("system", "light"),
    "system-dark": ("system", "dark"),
}
DENSITIES = ("auto", "desktop", "mobile")
CONTROL_SELECTOR = "button,input[type=button],input[type=submit],[role=button]"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")


def page_snapshot(page):
    return page.evaluate(
        """() => {
          const root = document.documentElement;
          const visible = el => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' &&
                   Number(s.opacity || 1) !== 0 && r.width > 0 && r.height > 0;
          };
          const buttons = [...document.querySelectorAll('button,input[type=button],input[type=submit],[role=button]')];
          const interactive = [...document.querySelectorAll('button,a[href],input,select,textarea,[role=button],[role=menuitem],[role=menuitemradio]')];
          const clipped = interactive.filter(el => {
            if (!visible(el)) return false;
            const r = el.getBoundingClientRect();
            return r.right < 0 || r.bottom < 0 || r.left > innerWidth || r.top > innerHeight;
          }).length;
          return {
            title: document.title,
            url: location.href,
            readyState: document.readyState,
            appearance: root.dataset.appearance || root.dataset.theme || null,
            appearanceMode: root.dataset.appearanceMode || null,
            appearanceResolved: root.dataset.appearanceResolved || null,
            density: root.dataset.uiDensity || null,
            densityPreference: root.dataset.uiDensityPreference || null,
            viewport: {width: innerWidth, height: innerHeight},
            rootScroll: {width: root.scrollWidth, height: root.scrollHeight, clientWidth: root.clientWidth, clientHeight: root.clientHeight},
            horizontalRootOverflow: Math.max(0, root.scrollWidth - root.clientWidth),
            buttonCount: buttons.length,
            visibleButtonCount: buttons.filter(visible).length,
            disabledButtonCount: buttons.filter(el => !!el.disabled || el.getAttribute('aria-disabled') === 'true').length,
            interactiveCount: interactive.length,
            offViewportInteractiveCount: clipped,
            openDialogs: [...document.querySelectorAll('[role=dialog]')].filter(visible).length,
          };
        }"""
    )


def inventory_controls(page):
    return page.evaluate(
        """selector => {
          const els = [...document.querySelectorAll(selector)];
          const visible = el => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' &&
                   Number(s.opacity || 1) !== 0 && r.width > 0 && r.height > 0;
          };
          return els.map((el, index) => ({
            index,
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            text: (el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 120),
            ariaLabel: el.getAttribute('aria-label'),
            title: el.getAttribute('title'),
            role: el.getAttribute('role'),
            densityMode: el.getAttribute('data-inkdos-density-mode'),
            appearanceChoice: el.getAttribute('data-appearance-choice') || el.getAttribute('data-home-appearance-mode'),
            visible: visible(el),
            disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
          }));
        }""",
        CONTROL_SELECTOR,
    )


def post_click_state(page):
    return page.evaluate(
        """() => {
          const visible = el => {
            const s = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
          };
          return {
            url: location.href,
            openDialogs: [...document.querySelectorAll('[role=dialog]')].filter(visible).map(el => el.id || el.getAttribute('aria-label') || el.className).slice(0, 12),
            expanded: [...document.querySelectorAll('[aria-expanded="true"]')].map(el => el.id || el.getAttribute('aria-label') || el.textContent.trim().slice(0, 60)).slice(0, 12),
            checked: [...document.querySelectorAll('[aria-checked="true"],[aria-pressed="true"]')].map(el => el.id || el.getAttribute('data-inkdos-density-mode') || el.getAttribute('data-appearance-choice') || el.textContent.trim().slice(0, 60)).slice(0, 12),
          };
        }"""
    )


def run():
    report = {
        "base": BASE,
        "browser": BROWSER_NAME,
        "matrix": [],
        "controlInventory": {},
        "clickSweep": {},
        "deployment": {},
        "cacheProbe": {},
        "summary": {},
    }
    with sync_playwright() as pw:
        browser_type = getattr(pw, BROWSER_NAME)
        browser = browser_type.launch(headless=True)

        probe_context = browser.new_context(service_workers="block")
        probe_page = probe_context.new_page()
        try:
            response = probe_page.request.get(urljoin(BASE, "VERSION.json"), headers={"Cache-Control": "no-cache"})
            report["deployment"] = {
                "status": response.status,
                "ok": response.ok,
                "headers": {
                    "etag": response.headers.get("etag"),
                    "last-modified": response.headers.get("last-modified"),
                    "cache-control": response.headers.get("cache-control"),
                },
                "version": response.json() if response.ok else response.text()[:1000],
            }
        except Exception as exc:
            report["deployment"] = {"error": repr(exc)}
        probe_context.close()

        for viewport_name, viewport in VIEWPORTS.items():
            for appearance_name, (appearance_mode, color_scheme) in APPEARANCES.items():
                for density in DENSITIES:
                    context = browser.new_context(
                        viewport=viewport,
                        color_scheme=color_scheme,
                        service_workers="block",
                        accept_downloads=True,
                    )
                    context.add_init_script(
                        f"""(() => {{
                          try {{
                            localStorage.setItem('inkdos2:appearance', {json.dumps(appearance_mode)});
                            localStorage.setItem('inkdos2:ui-density', {json.dumps(density)});
                          }} catch (_) {{}}
                        }})();"""
                    )
                    page = context.new_page()
                    current_errors = []
                    page.on("pageerror", lambda exc, bucket=current_errors: bucket.append("pageerror: " + str(exc)))
                    page.on("console", lambda msg, bucket=current_errors: bucket.append("console-error: " + msg.text) if msg.type == "error" else None)
                    page.on("dialog", lambda dialog: dialog.dismiss())
                    page.on("download", lambda download: download.cancel())

                    for page_name, rel in PAGES:
                        current_errors.clear()
                        url = urljoin(BASE, rel)
                        item = {
                            "page": page_name,
                            "url": url,
                            "viewport": viewport_name,
                            "appearance": appearance_name,
                            "appearanceStorage": appearance_mode,
                            "density": density,
                            "browser": BROWSER_NAME,
                            "errors": [],
                        }
                        try:
                            response = page.goto(url, wait_until="load", timeout=30000)
                            page.wait_for_timeout(250)
                            item["httpStatus"] = response.status if response else None
                            item["snapshot"] = page_snapshot(page)
                            item["errors"] = list(current_errors)
                            shot_name = "__".join(
                                map(slug, [BROWSER_NAME, page_name, viewport_name, appearance_name, density])
                            ) + ".png"
                            shot_path = SHOT_DIR / shot_name
                            page.screenshot(path=str(shot_path), full_page=False)
                            item["screenshot"] = str(shot_path.relative_to(OUT))
                        except Exception as exc:
                            item["exception"] = repr(exc)
                            item["errors"] = list(current_errors)
                        report["matrix"].append(item)
                    page.close()
                    context.close()

        click_context = browser.new_context(
            viewport=VIEWPORTS["16x9"],
            color_scheme="light",
            service_workers="block",
            accept_downloads=True,
        )
        click_context.add_init_script(
            """(() => {
              try {
                localStorage.setItem('inkdos2:appearance', 'light');
                localStorage.setItem('inkdos2:ui-density', 'desktop');
              } catch (_) {}
            })();"""
        )
        for page_name, rel in PAGES:
            url = urljoin(BASE, rel)
            page = click_context.new_page()
            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_timeout(250)
            inventory = inventory_controls(page)
            report["controlInventory"][page_name] = inventory
            page.close()

            if not CLICK_SWEEP:
                continue
            results = []
            for control in inventory:
                entry = {"control": control, "status": "not-run"}
                if not control["visible"]:
                    entry["status"] = "hidden-in-initial-state"
                    results.append(entry)
                    continue
                if control["disabled"]:
                    entry["status"] = "disabled-in-initial-state"
                    results.append(entry)
                    continue
                test_page = click_context.new_page()
                errors = []
                file_choosers = []
                downloads = []
                test_page.on("pageerror", lambda exc, bucket=errors: bucket.append("pageerror: " + str(exc)))
                test_page.on("console", lambda msg, bucket=errors: bucket.append("console-error: " + msg.text) if msg.type == "error" else None)
                test_page.on("dialog", lambda dialog: dialog.dismiss())
                test_page.on("filechooser", lambda chooser, bucket=file_choosers: bucket.append("opened"))
                test_page.on("download", lambda download, bucket=downloads: (bucket.append(download.suggested_filename), download.cancel()))
                try:
                    test_page.goto(url, wait_until="load", timeout=30000)
                    test_page.wait_for_timeout(120)
                    loc = test_page.locator(CONTROL_SELECTOR).nth(control["index"])
                    if not loc.is_visible():
                        entry["status"] = "not-visible-on-reload"
                    elif not loc.is_enabled():
                        entry["status"] = "disabled-on-reload"
                    else:
                        before = test_page.url
                        loc.click(timeout=2500, no_wait_after=True)
                        test_page.wait_for_timeout(180)
                        entry["status"] = "clicked"
                        entry["urlBefore"] = before
                        entry["post"] = post_click_state(test_page)
                        entry["fileChooser"] = bool(file_choosers)
                        entry["downloads"] = list(downloads)
                        entry["errors"] = list(errors)
                except Exception as exc:
                    entry["status"] = "click-exception"
                    entry["exception"] = repr(exc)
                    entry["errors"] = list(errors)
                    entry["fileChooser"] = bool(file_choosers)
                    entry["downloads"] = list(downloads)
                finally:
                    test_page.close()
                results.append(entry)
            report["clickSweep"][page_name] = results
        click_context.close()

        if BROWSER_NAME == "chromium":
            cache_context = browser.new_context(viewport=VIEWPORTS["16x9"], service_workers="allow")
            cache_page = cache_context.new_page()
            cache_errors = []
            cache_page.on("pageerror", lambda exc: cache_errors.append(str(exc)))
            try:
                response = cache_page.goto(BASE, wait_until="load", timeout=30000)
                cache_page.wait_for_timeout(1200)
                report["cacheProbe"] = cache_page.evaluate(
                    """async () => {
                      const regs = 'serviceWorker' in navigator ? await navigator.serviceWorker.getRegistrations() : [];
                      const keys = 'caches' in self ? await caches.keys() : [];
                      return {
                        registrations: regs.map(r => ({scope: r.scope, active: r.active && r.active.scriptURL, waiting: r.waiting && r.waiting.scriptURL, installing: r.installing && r.installing.scriptURL})),
                        cacheKeys: keys,
                        controller: navigator.serviceWorker && navigator.serviceWorker.controller ? navigator.serviceWorker.controller.scriptURL : null,
                      };
                    }"""
                )
                report["cacheProbe"]["httpStatus"] = response.status if response else None
                report["cacheProbe"]["errors"] = cache_errors
            except Exception as exc:
                report["cacheProbe"] = {"exception": repr(exc), "errors": cache_errors}
            cache_context.close()

        browser.close()

    matrix = report["matrix"]
    report["summary"] = {
        "matrixCases": len(matrix),
        "matrixExceptions": sum(1 for x in matrix if x.get("exception")),
        "httpFailures": sum(1 for x in matrix if (x.get("httpStatus") or 200) >= 400),
        "casesWithJsErrors": sum(1 for x in matrix if x.get("errors")),
        "rootOverflowCases": sum(1 for x in matrix if x.get("snapshot", {}).get("horizontalRootOverflow", 0) > 8),
        "inventoryControls": sum(len(v) for v in report["controlInventory"].values()),
        "visibleInitialControls": sum(sum(1 for c in v if c["visible"]) for v in report["controlInventory"].values()),
        "clickSweepEnabled": CLICK_SWEEP,
        "clickExceptions": sum(
            sum(1 for x in v if x.get("status") == "click-exception")
            for v in report["clickSweep"].values()
        ),
        "clickedControls": sum(
            sum(1 for x in v if x.get("status") == "clicked")
            for v in report["clickSweep"].values()
        ),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print("Report:", OUT / "report.json")


if __name__ == "__main__":
    run()
