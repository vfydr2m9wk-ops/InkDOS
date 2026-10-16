"""Tool bar pickers of Documents, Presentations and Spreadsheets (owner, 2026-10-15): the 2.8 look (icon pickers,
value boxes) is written in each page and each picker is a fixed box with its dropdown invisible on top, so a host that
restyles native dropdowns (XeOS) cannot turn them back into wide dark menus. tests/test_toolbar_pickers_browser.py
checks the same in a browser."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = {
    'documents': ('formatbar', ['styleSelect', 'fontSelect', 'alignmentSelect', 'lineSpacing'], ['sizeSelect']),
    'presentations': ('editbar', ['pptP1Shape', 'pptP1Layout', 'pptP2Transition', 'fontFamily', 'alignSelect',
                                  'pptP1BorderWidth', 'pptP1BorderStyle', 'pptP1Arrange'], ['fontSize']),
    'spreadsheets': ('formatbar', ['numberFormat', 'fontFamily', 'borderSides', 'borderStyle', 'borderWidth',
                                   'alignmentSelect', 'verticalAlignmentSelect', 'wrapSelect', 'rotationSelect',
                                   'operationSelect'], ['fontSize', 'functionSelect']),
}


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def look(app):
    html = read(f'apps/{app}/index.html')
    start = html.index('<style id="toolbarLook">')
    return html, html[start:html.index('</style>', start)]


def script_lists(app):
    js = read(f'apps/{app}/ui/toolbar-pickers.js')
    match = re.search(r'const icons=(\[[^\]]*\]),values=(\[[^\]]*\])', js)
    assert match, app
    return js, json.loads(match.group(1)), json.loads(match.group(2))


def test_each_page_carries_the_look_and_the_picker_script():
    for app in APPS:
        html, css = look(app)
        assert '<script src="ui/toolbar-pickers.js"></script>' in html, app
        # the look lives in the page: a separate stylesheet did not apply in XeOS
        assert 'href="ui/visual-system.css"' not in html and 'href="ui/editor-toolbar.css"' not in html, app
        for rule in ('.inkdos-picker{', '.inkdos-picker>*{', '.inkdos-value-picker{', '.inkdos-picker>.inkdos-picker-label{',
                     '.inkdos-picker:has(>select:disabled)', '.inkdos-picker:has(>select[hidden])'):
            assert rule in css, (app, rule)


def test_scripts_wrap_the_pickers_the_look_draws():
    for app, (bar, icons, values) in APPS.items():
        _, css = look(app)
        js, got_icons, got_values = script_lists(app)
        assert got_icons == icons and got_values == values, app
        assert f'closest("#{bar}")' in js, app
        for picker in icons:
            # the box itself carries the icon, in light and in dark
            rules = re.findall(r'([^{}]*\.inkdos-picker\[data-for="' + picker + r'"\][^{}]*)\{([^}]*)\}', css)
            images = [sel for sel, body in rules if 'background-image' in body]
            assert any('data-appearance-resolved="dark"' not in sel for sel in images), (app, picker)
            assert any('data-appearance-resolved="dark"' in sel for sel in images), (app, picker)


def test_dropdown_lists_are_not_cut_to_the_icon():
    for app in APPS:
        _, css = look(app)
        children = re.search(r'\.inkdos-picker>\*\{([^}]*)\}', css).group(1)
        assert 'opacity:0!important' in children and 'min-width:260px!important' in children, app
        js, _, _ = script_lists(app)
        assert '["min-width","260px"]' in js, app


def test_offline_copy_includes_the_picker_script():
    worker = read('service-worker.js')
    for app in APPS:
        assert f'"./apps/{app}/ui/toolbar-pickers.js"' in worker, app
