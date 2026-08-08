from __future__ import annotations
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from browser_support import launch_browser, requested_browser_name
import json, os

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tests/browser/results'; OUT.mkdir(parents=True,exist_ok=True)
CHROMIUM=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium')

def inject(page,workspace):
    html=(ROOT/f'apps/{workspace}/index.html').read_text(encoding='utf-8')
    soup=BeautifulSoup(html,'html.parser')
    for node in soup.find_all(['script','link']): node.decompose()
    page.set_content(str(soup),wait_until='domcontentloaded')
    for css in ('shared/office-shell.css',f'apps/{workspace}/styles.css'):
        page.add_style_tag(path=str(ROOT/css))
    if workspace=='presentations':
        scripts=('shared/office-runtime.js','shared/vendor/jszip.min.js','apps/presentations/engine/compatibility.js','shared/office-shell.js','apps/presentations/state/selection-controller.js','apps/presentations/state/history-controller.js','apps/presentations/ui/inspector-controller.js','apps/presentations/ui/thumbnails-controller.js','apps/presentations/ui/presenter-notes-controller.js','apps/presentations/presentation/slideshow-controller.js','apps/presentations/io/pptx-write-adapter.js',
        'apps/presentations/io/file-controller.js','apps/presentations/io/recovery-controller.js','apps/presentations/app.js')
    elif workspace=='spreadsheets':
        page.add_style_tag(path=str(ROOT/'apps/spreadsheets/formula-reference.css'))
        page.add_style_tag(path=str(ROOT/'apps/spreadsheets/formula-editor.css'))
        scripts=('shared/office-runtime.js','shared/file-lifecycle.js','shared/file-router.js','shared/formula-engine.js','shared/vendor/jszip.min.js','apps/spreadsheets/xls-biff8-engine.js','apps/spreadsheets/worksheet-package.js','apps/spreadsheets/xlsx-engine.js','shared/office-shell.js','apps/spreadsheets/formula-safety.js',"apps/spreadsheets/history-controller.js",'apps/spreadsheets/worksheet-tabs.js','apps/spreadsheets/app.js','apps/spreadsheets/formula-model.js','apps/spreadsheets/formula-session.js','apps/spreadsheets/formula-reference.js','apps/spreadsheets/formula-editor.js')
    else:
        scripts=()
    for script in scripts: page.add_script_tag(path=str(ROOT/script))

def main():
    result={}
    with sync_playwright() as pw:
        browser=launch_browser(pw)
        page=browser.new_page(viewport={'width':1400,'height':900})
        inject(page,'documents')
        home=page.locator('.left-tools > .home-link')
        result['documents_home_visible']=home.is_visible()
        if not result['documents_home_visible']: raise RuntimeError('Documents Home is not visible')
        page.close()

        page=browser.new_page(viewport={'width':1400,'height':900})
        inject(page,'presentations')
        result['presentations_start_home_visible']=page.locator('.start-home-link').is_visible()
        page.click('#newBtn'); page.click('#templateGrid .template-option')
        result['presentations_editor_home_visible']=page.locator('.titlebar-left > .home-link').is_visible()
        if not all((result['presentations_start_home_visible'],result['presentations_editor_home_visible'])): raise RuntimeError('Presentations Home is missing')
        page.close()

        page=browser.new_page(viewport={'width':1500,'height':1000})
        inject(page,'spreadsheets'); page.click('#newEmptyBtn')
        page.wait_for_function("!document.querySelector('#gridViewport').hidden")
        a1=page.locator('.cell[data-r="0"][data-c="0"]'); c3=page.locator('.cell[data-r="2"][data-c="2"]')
        b1=a1.bounding_box(); b2=c3.bounding_box()
        page.mouse.move(b1['x']+b1['width']/2,b1['y']+b1['height']/2); page.mouse.down(); page.mouse.move(b2['x']+b2['width']/2,b2['y']+b2['height']/2,steps=12); page.mouse.up()
        selected=page.locator('.cell.in-range').count()
        result['normal_drag_selected_cells']=selected
        if selected!=9: raise RuntimeError(f'Normal drag selected {selected} cells instead of 9')
        # A formula draft that cannot accept a reference must not capture normal grid selection.
        page.click('.cell[data-r="4"][data-c="4"]'); page.keyboard.type('=S')
        page.click('.cell[data-r="5"][data-c="5"]')
        if page.locator('.cell[data-r="5"][data-c="5"]').get_attribute('class').find('selected')<0: raise RuntimeError('Formula standby blocked normal selection')
        result['formula_standby_releases_grid']=True

        # An incomplete formula draft is unsaved work even before it enters the
        # workbook model. Save must not serialize a copy that silently omits it.
        page.click('.cell[data-r="0"][data-c="0"]')
        page.keyboard.type('=S')
        page.wait_for_function("window.InkDeskSpreadsheetFormulaEditor && window.InkDeskSpreadsheetFormulaEditor.hasPendingDrafts()")
        page.click('#saveBtn')
        if not page.locator('#savePanel').is_hidden(): raise RuntimeError('Save panel opened while a formula draft was pending')
        if 'Confirm or cancel formula drafts' not in page.locator('#toast').inner_text(): raise RuntimeError('Pending formula draft save guard did not explain the block')
        result['formula_draft_blocks_save']=True

        # The same draft must trigger the normal discard confirmation and must
        # not leak into the next workbook after the user accepts that discard.
        page.once('dialog', lambda dialog: dialog.accept())
        page.click('#newBtn')
        page.wait_for_function("window.InkDeskSpreadsheetFormulaEditor && !window.InkDeskSpreadsheetFormulaEditor.hasPendingDrafts()")
        if page.locator('.cell.has-formula-draft').count(): raise RuntimeError('New workbook inherited a stale formula draft')
        result['formula_draft_cleared_on_confirmed_new_workbook']=True
        page.close()

        # Undo/Redo is workbook-wide but each action must stay bound to the
        # worksheet where it originated. Triggering history from Data must not
        # write Summary's cell snapshot into Data.
        page=browser.new_page(viewport={'width':1500,'height':1000})
        inject(page,'spreadsheets')
        fixture=ROOT/'tests/compatibility-fixtures/spreadsheets/era2_office_2007_2013_baseline.xlsx'
        page.set_input_files('#fileInput',str(fixture))
        page.wait_for_function("document.querySelectorAll('#sheetTabs button').length >= 2")
        original_summary=page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
        formula=page.locator('#formulaInput'); formula.fill('History Sheet A'); formula.press('Enter')
        page.locator('#sheetTabs button',has_text='Data').click()
        data_a1=page.locator('.cell[data-r="0"][data-c="0"]').inner_text()
        page.click('#undoBtn')
        if page.locator('.cell[data-r="0"][data-c="0"]').inner_text()!=data_a1: raise RuntimeError('Undo mutated the active worksheet instead of its origin sheet')
        page.locator('#sheetTabs button',has_text='Summary').click()
        if page.locator('.cell[data-r="0"][data-c="0"]').inner_text()!=original_summary: raise RuntimeError('Undo did not restore the originating worksheet')
        page.locator('#sheetTabs button',has_text='Data').click(); page.click('#redoBtn')
        if page.locator('.cell[data-r="0"][data-c="0"]').inner_text()!=data_a1: raise RuntimeError('Redo mutated the active worksheet instead of its origin sheet')
        page.locator('#sheetTabs button',has_text='Summary').click()
        if page.locator('.cell[data-r="0"][data-c="0"]').inner_text()!='History Sheet A': raise RuntimeError('Redo did not reapply the originating worksheet action')
        result['spreadsheet_history_sheet_isolation']=True
        page.close(); browser.close()
    (OUT/'v0201_consistency.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
