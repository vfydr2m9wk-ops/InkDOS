from __future__ import annotations
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class V0201ConsistencyTests(unittest.TestCase):
    def test_documents_home_is_first_title_action(self):
        html=(ROOT/'apps/documents/index.html').read_text(encoding='utf-8')
        block=re.search(r'<div class="left-tools">(.*?)</div>',html,re.S).group(1)
        self.assertLess(block.index('home-link'),block.index('id="newBtn"'))
        self.assertIn('href="../../index.html"',block)
        self.assertIn('Return to InkDOS home',block)

    def test_presentations_home_exists_before_and_after_open(self):
        html=(ROOT/'apps/presentations/index.html').read_text(encoding='utf-8')
        self.assertIn('class="start-home-link"',html)
        block=re.search(r'<div class="titlebar-left">(.*?)</div>',html,re.S).group(1)
        self.assertLess(block.index('home-link'),block.index('id="newSmall"'))
        self.assertEqual(html.count('href="../../index.html"'),2)

    def test_normal_grid_drag_uses_global_hit_testing_without_pointer_capture(self):
        script=(ROOT/'apps/spreadsheets/app.js').read_text(encoding='utf-8')
        for marker in ('function gridCellAtPoint(','document.elementFromPoint?.(','function moveDragSelection(','pointermove',"pointercancel',endDragSelection","blur',endDragSelection"):
            self.assertIn(marker,script)
        cell_down=re.search(r'function cellDown\(e\)\{(.*?)\}\nfunction cellEnter',script,re.S).group(1)
        self.assertNotIn('setPointerCapture',cell_down)

    def test_formula_capture_is_armed_only(self):
        script=(ROOT/'apps/spreadsheets/formula-reference.js').read_text(encoding='utf-8')
        styles=(ROOT/'apps/spreadsheets/formula-reference.css').read_text(encoding='utf-8')
        self.assertIn("const VERSION = '0.20.1'",script)
        self.assertIn("armed ? 'armed' : 'standby'",script)
        self.assertIn("formulaReferenceMode !== 'armed'",script)
        self.assertIn('[data-formula-reference-mode="armed"]',styles)
        self.assertNotIn('[data-formula-reference-mode="active"]',styles)

    def test_public_version_and_cache_are_synchronized(self):
        version=json.loads((ROOT/'VERSION.json').read_text())['version']
        self.assertEqual(version,'1.0.0-beta.6')
        self.assertEqual(json.loads((ROOT/'package.json').read_text())['version'],version)
        self.assertEqual(json.loads((ROOT/'app-manifest.json').read_text())['version'],version)
        self.assertIn(f"inkdos-shell-v{version}",(ROOT/'service-worker.js').read_text())
        self.assertIn('InkDOS — Ink Desk Offline Suite',(ROOT/'index.html').read_text())

    def test_critical_existing_functions_remain_present(self):
        documents=(ROOT/'apps/documents/app.js').read_text()
        sheets=(ROOT/'apps/spreadsheets/app.js').read_text()
        formulas=(ROOT/'apps/spreadsheets/formula-editor.js').read_text()
        presentations=(ROOT/'apps/presentations/app.js').read_text()
        slideshow=(ROOT/'apps/presentations/presentation/slideshow-controller.js').read_text()
        for marker in ('openFile','LocalDocxWriter.save','beforeunload'):
            self.assertIn(marker,documents)
        for marker in ('newWorkbook','prepareSave','selectedRefs','copySelection','pasteSelection'):
            self.assertIn(marker,sheets)
        for marker in ('formulaCanSelectReference','balanceFormula','drafts'):
            self.assertIn(marker,formulas)
        for marker in ('loadPptx','savePptx','beforeunload','InkDOSPresentationsSlideshow.create'):
            self.assertIn(marker,presentations)
        for marker in ('enter(fromFirst = false)','move(delta)','async exit()'):
            self.assertIn(marker,slideshow)
        shell=(ROOT/'shared/office-shell.js').read_text()
        controller=(ROOT/'shared/ui/document-session-controller.js').read_text()
        self.assertIn('Object.freeze(Object.assign(',controller)
        self.assertNotIn('InkDOSRuntime.requestDownload = requestDownload',controller)
        self.assertIn('document-session-controller.js',shell)


    def test_all_workspace_pages_declare_existing_favicons(self):
        expected = {
            "documents": "documents.png",
            "spreadsheets": "spreadsheets.png",
            "presentations": "presentations.png",
            "pdf": "pdf.png",
            "txt": "txt.png",
            "epub": "epub.png",
        }
        for module, icon in expected.items():
            html = (ROOT / "apps" / module / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                f'<link rel="icon" href="../../assets/icons/{icon}">',
                html,
                module,
            )
            self.assertTrue((ROOT / "assets" / "icons" / icon).is_file())


    def test_mutable_development_state_is_excluded_from_release_checksums(self):
        checksum_manifest=(ROOT/'CHECKSUMS.sha256').read_text(encoding='utf-8')
        self.assertNotIn('  DEVELOPMENT_STATE.json',checksum_manifest)
        for relative in ('scripts/generate_checksums.py','scripts/verify_checksums.py'):
            script=(ROOT/relative).read_text(encoding='utf-8')
            self.assertIn('"DEVELOPMENT_STATE.json"',script,relative)

if __name__=='__main__': unittest.main()
