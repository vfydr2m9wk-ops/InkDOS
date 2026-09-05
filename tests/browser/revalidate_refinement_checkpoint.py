#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_support import launch_browser

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / 'tests/browser/results/refinement_checkpoint.json'
APPS = ('documents', 'spreadsheets', 'presentations', 'pdf', 'txt', 'epub')
WIDTHS = (320, 360, 375, 390, 412, 430, 768, 1024, 1280, 1440)


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def stripped(html: str) -> str:
    html = re.sub(r'<link\b[^>]*>', '', html, flags=re.I)
    return re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S | re.I)


def add_linked_styles(page, html: str, page_path: str) -> None:
    base = (ROOT / page_path).parent
    for tag in re.findall(r'<link\b[^>]*>', html, flags=re.I):
        if 'stylesheet' not in tag.lower():
            continue
        match = re.search(r'href=["\']([^"\']+)', tag, flags=re.I)
        if not match:
            continue
        href = match.group(1).split('?', 1)[0]
        if '://' in href:
            continue
        candidate = (base / href).resolve()
        try:
            candidate.relative_to(ROOT)
        except ValueError:
            continue
        if candidate.is_file() and candidate.suffix == '.css':
            page.add_style_tag(content=candidate.read_text(encoding='utf-8'))


def storage(page) -> None:
    page.evaluate("""() => {
      const values = new Map();
      Object.defineProperty(window, 'localStorage', {configurable:true, value:{
        getItem:key => values.has(key) ? values.get(key) : null,
        setItem:(key,value) => values.set(key,String(value)),
        removeItem:key => values.delete(key),
        clear:() => values.clear()
      }});
    }""")


def inject_scripts(page, app_home: bool = False) -> None:
    storage(page)
    for path in (
        'shared/product-config.js',
        'modules/module-registry.js',
        'modules/module-loader.js',
        'shared/recent-files.js',
        'shared/file-router.js',
        'shared/app-shell.js',
    ):
        page.add_script_tag(content=source(path))
    if app_home:
        page.add_script_tag(content=source('shared/app-home.js'))


def rgb(value: str) -> list[int]:
    parts = [int(item) for item in re.findall(r'\d+', value)[:3]]
    return parts if len(parts) == 3 else [0, 0, 0]


def contrast(foreground: str, background: str) -> float:
    def luminance(values: list[int]) -> float:
        channels = []
        for value in values:
            channel = value / 255
            channels.append(channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4)
        return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]
    first, second = luminance(rgb(foreground)), luminance(rgb(background))
    return (max(first, second) + .05) / (min(first, second) + .05)


def no_document_overflow(page) -> bool:
    return page.evaluate('() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1')


def main() -> int:
    with sync_playwright() as pw:
        browser = launch_browser(pw)
        page = browser.new_page(viewport={'width': 390, 'height': 844})

        home_html = source('index.html')
        page.set_content(stripped(home_html), wait_until='load')
        add_linked_styles(page, home_html, 'index.html')
        inject_scripts(page)
        page.add_script_tag(content=source('shared/suite-shell.js'))
        page.wait_for_function('() => Boolean(window.InkDOSSuite)')

        assert page.locator('.hub-intro').count() == 0
        assert page.locator('.workspace-grid').count() == 0
        assert page.locator('[data-recent-filter]').count() == 7
        assert page.locator('[data-app-launcher-trigger]').count() == 1
        assert page.locator('[data-settings-trigger]').count() == 1
        assert page.locator('[data-app-launcher-trigger].inkdos-global-trigger').count() == 1
        assert page.locator('[data-settings-trigger].inkdos-global-trigger').count() == 1
        assert page.locator('[data-app-launcher-trigger].suite-menu').count() == 0
        assert page.locator('[data-settings-trigger].suite-menu').count() == 0
        assert 'background-color' not in page.locator('[data-app-launcher-trigger]').evaluate(
            "el => getComputedStyle(el).transitionProperty"
        )
        page.locator('[data-app-launcher-trigger]').click()
        assert page.locator('.inkdos-app-launcher-item').count() == 6
        page.keyboard.press('Escape')
        assert not page.locator('[data-recent-clear]').is_visible()
        assert page.locator('[data-recent-open].suite-action.primary').count() == 1
        assert page.locator('[data-recent-open]').evaluate("el => !el.hasAttribute('style')")

        page.evaluate("() => InkDOSAppShell.applyTheme('dark', false)")
        home_box = page.locator('.recent-section').bounding_box()
        assert home_box and home_box['x'] >= 19 and home_box['x'] + home_box['width'] <= 371
        open_colors = page.locator('[data-recent-open]').evaluate(
            "el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]"
        )
        menu_colors = page.locator('[data-app-launcher-trigger]').evaluate(
            "el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]"
        )
        settings_colors = page.locator('[data-settings-trigger]').evaluate(
            "el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]"
        )
        assert contrast(*open_colors) >= 4.5, f"dark Open file colors={open_colors} contrast={contrast(*open_colors):.2f}"
        assert contrast(*menu_colors) >= 4.5, f"dark menu colors={menu_colors} contrast={contrast(*menu_colors):.2f}"
        assert contrast(*settings_colors) >= 4.5, f"dark settings colors={settings_colors} contrast={contrast(*settings_colors):.2f}"
        assert page.evaluate("() => getComputedStyle(document.body).backgroundImage.includes('rgb(23, 26, 32)')")

        page.evaluate("() => InkDOSAppShell.applyTheme('light', false)")
        light_open = page.locator('[data-recent-open]').evaluate(
            "el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]"
        )
        assert contrast(*light_open) >= 4.5, f"light Open file colors={light_open} contrast={contrast(*light_open):.2f}"

        page.evaluate("""() => {
          InkDOSRecentFiles.registerCreated({appId:'documents', name:'Report.docx', extension:'docx'});
          InkDOSSuite.renderRecent();
        }""")
        assert page.locator('.recent-row').count() == 1
        assert page.locator('[data-recent-clear]').is_visible()
        for width in WIDTHS:
            page.set_viewport_size({'width': width, 'height': 800})
            assert no_document_overflow(page), width

        app_results = {}
        for app in APPS:
            app_html = source(f'apps/{app}/index.html')
            page.set_content(stripped(app_html), wait_until='load')
            add_linked_styles(page, app_html, f'apps/{app}/index.html')
            inject_scripts(page, app_home=True)
            page.wait_for_function("() => Boolean(document.querySelector('.inkdos-app-home-page'))")
            creates = page.locator('[data-app-home-action="create"]').count()
            opens = page.locator('[data-app-home-action="open"]').count()
            assert opens == 1
            assert creates == (0 if app in {'pdf', 'epub'} else 1)
            open_action = page.locator('[data-app-home-action="open"]')
            assert open_action.evaluate("el => el.classList.contains('inkdos-app-home-action-primary')"), app
            open_colors = open_action.evaluate("el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]")
            assert open_colors[1] == 'rgb(47, 111, 237)', (app, open_colors)
            assert contrast(*open_colors) >= 4.5, (app, open_colors, contrast(*open_colors))
            if creates:
                create_action = page.locator('[data-app-home-action="create"]')
                assert not create_action.evaluate("el => el.classList.contains('inkdos-app-home-action-primary')"), app
                create_colors = create_action.evaluate("el => [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]")
                assert create_colors[1] == 'rgb(255, 255, 255)', (app, create_colors)
                assert contrast(*create_colors) >= 4.5, (app, create_colors, contrast(*create_colors))
            topbar = page.locator('.inkdos-app-home-topbar').bounding_box()
            assert topbar and topbar['y'] <= 30, (app, topbar)
            assert page.locator('.inkdos-app-launcher-item').count() == 6

            assert page.locator('[data-app-home]').evaluate("el => el.parentElement === document.body"), app
            assert page.locator('[data-app-home]').evaluate("el => getComputedStyle(el).position === 'fixed'"), app
            checked = []
            for width in WIDTHS:
                page.set_viewport_size({'width': width, 'height': 800})
                assert no_document_overflow(page), (app, width)
                host = page.locator('[data-app-home]').bounding_box()
                assert host and host['x'] >= -1 and host['x'] <= 1, (app, width, host)
                assert host['width'] >= width - 1 and host['x'] + host['width'] <= width + 1, (app, width, host)
                checked.append(width)
            page.set_viewport_size({'width': 667, 'height': 375})
            assert no_document_overflow(page), (app, 'landscape')
            landscape_host = page.locator('[data-app-home]').bounding_box()
            assert landscape_host and landscape_host['width'] >= 666, (app, 'landscape', landscape_host)

            if app == 'documents':
                page.set_viewport_size({'width': 390, 'height': 844})
                host = page.locator('[data-app-home]').bounding_box()
                assert host and host['width'] >= 389
                assert page.locator('.inkdos-app-home-page').is_visible()
                assert 'Documents' in page.locator('.inkdos-app-home-page').inner_text()

            app_results[app] = {'create': creates, 'open': opens, 'widths': checked, 'landscape': True}

        payload = {
            'browser': os.environ.get('INKDOS_BROWSER', 'chromium'),
            'home_widths': list(WIDTHS),
            'apps': app_results,
            'home_dark_contrast': {'open': round(contrast(*open_colors), 2), 'launcher': round(contrast(*menu_colors), 2)},
        }
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
        browser.close()
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
