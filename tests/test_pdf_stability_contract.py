#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "apps" / "pdf"
def text(path): return path.read_text(encoding="utf-8")

def main():
    app=text(PDF/"app.js");editor=text(PDF/"pdfjs"/"editor-adapter.js");review=text(PDF/"extensions"/"review-annotations.js");nav=text(PDF/"ui"/"navigation-controller.js");layout=text(PDF/"view"/"page-layout.js");commands=text(PDF/"ui"/"command-controller.js");registry=text(PDF/"runtime"/"commands"/"command-registry.js");bindings=text(PDF/"ui"/"command-bindings.js");rail=text(PDF/"ui"/"toolbar-rail.js");mode=text(PDF/"modes"/"mode-controller.js");mode_bindings=text(PDF/"ui"/"mode-bindings.js");reader_ui=text(PDF/"ui"/"reader-tools.js");reader_runtime=text(PDF/"features"/"reader"/"reader-runtime.js");page_ui=text(PDF/"ui"/"page-tools.js");page_runtime=text(PDF/"features"/"page-tools"/"page-tools-runtime.js")
    actions={"move":text(PDF/"features"/"page-tools"/"actions"/"move-page.js"),"rotate":text(PDF/"features"/"page-tools"/"actions"/"rotate-page.js"),"delete":text(PDF/"features"/"page-tools"/"actions"/"delete-page.js"),"extract":text(PDF/"features"/"page-tools"/"actions"/"extract-page.js"),"split":text(PDF/"features"/"page-tools"/"actions"/"split-pdf.js"),"merge":text(PDF/"features"/"page-tools"/"actions"/"merge-pdfs.js")}
    assert "editingstateschanged" in editor and "annotationeditorstateschanged" in editor
    for command in ("pdf.comment.open","pdf.comment.cancel","pdf.comment.save"): assert command in review
    assert "registry?.bindElement(pin,COMMENT_COMMANDS.open)" in review and "m.layer.append(pin);this.registry?.bindElement" in review
    for forbidden in ("pin.onclick","cancel.onclick","back.onclick","dlg.onsubmit"): assert forbidden not in review
    assert "dlg.addEventListener('submit',this._commentSubmit)" in review and "registry?.execute(COMMENT_COMMANDS.save)" in review
    assert "new NS.ReviewAnnotations({editor,session,chrome,registry})" in app
    assert "DEFAULT_TAB='outline'" in nav and "open(DEFAULT_TAB)" in nav and "anchor?.isConnected" in nav
    for forbidden in ("$('closeNavigation').onclick","$('outlineTab').onclick","$('pagesTab').onclick","$('thumbPrevBlock').onclick","$('thumbNextBlock').onclick","b.onclick=","card.onclick="): assert forbidden not in nav
    assert "registry?.bindElement" in nav and "pdf.navigation.outline.go" in nav and "pdf.navigation.page.go" in nav
    for command in ("pdf.navigation.toggle","pdf.navigation.close","pdf.navigation.tab.outline","pdf.navigation.tab.pages","pdf.navigation.thumb.previous","pdf.navigation.thumb.next","pdf.navigation.outline.go","pdf.navigation.page.go"): assert command in bindings
    assert "navPanelBtn:'pdf.navigation.toggle'" in bindings and "closeNavigation:'pdf.navigation.close'" in bindings
    assert "pdf.navigation.toggle',{" not in commands and "navigation.toggle" not in commands
    for command in ("appearance.light","appearance.dark","appearance.system"): assert command in bindings
    assert "[data-appearance-choice]" in bindings and "NS.Appearance.set(choice)" in bindings
    assert "data-appearance-choice" not in commands and "NS.Appearance.set" not in commands
    assert "userScrollEpoch" in layout and "sameMetrics" in layout and "userEpoch===this.userScrollEpoch" in layout and "scrollIntoView" not in layout
    for path in ("runtime/commands/command-registry.js","ui/command-bindings.js","ui/toolbar-rail.js","ui/mode-bindings.js","features/reader/reader-runtime.js","features/page-tools/page-tools-runtime.js"): assert path in app
    for name in ("move-page.js","rotate-page.js","delete-page.js","extract-page.js","split-pdf.js","merge-pdfs.js"): assert name in app
    assert "function installToolbarRail" not in app and "NS.ToolbarRail" in rail and "NS.CommandRegistry" in registry and "bindElement" in registry
    assert "history.undo" in commands and "history.redo" in commands and "annotation.delete" in commands
    assert "$('undoBtn').onclick" not in commands and "$('redoBtn').onclick" not in commands and "$('deleteAnnotationBtn').onclick" not in commands
    assert "undoBtn:'history.undo'" in bindings and "deleteAnnotationBtn:'annotation.delete'" in bindings
    assert "querySelectorAll" not in mode and "data-pdf-mode" not in mode and "data-annotate-tool" not in mode and "subscribe" in mode
    for command in ("pdf.mode.view","pdf.mode.annotate","pdf.tool.select","pdf.tool.text","pdf.tool.pen","pdf.tool.highlight","pdf.tool.underline","pdf.tool.comment"): assert command in mode_bindings
    assert "ModeBindings.create" in app
    for command in ("reader.search","reader.search.close","reader.search.query","reader.search.previous","reader.search.next","reader.search.reveal","reader.rotate-view","reader.print"): assert command in reader_ui
    for forbidden in ("searchBtn.onclick","rotateBtn.onclick","printBtn.onclick","prevBtn.onclick","nextBtn.onclick","b.onclick=()=>reveal"): assert forbidden not in reader_ui
    assert "getTextContent" not in reader_ui and "layout.rotateView" not in reader_ui and "getTextContent" in reader_runtime and "layout.rotateView" in reader_runtime
    assert "reader.search',{" not in commands and "reader.print',{" not in commands and "reader.rotate-view',{" not in commands
    for command in ("pdf.pages.panel.toggle","pdf.pages.panel.close","pdf.pages.move","pdf.pages.rotate","pdf.pages.delete","pdf.pages.extract","pdf.pages.split","pdf.pages.merge.choose","pdf.pages.merge.files"): assert command in page_ui
    assert "$('closePageTools').onclick" not in page_ui and 'data-command="pdf.pages.panel.close"' in page_ui
    for forbidden in ("PageToolsEngine.movePage","PageToolsEngine.rotatePage","PageToolsEngine.deletePage","PageToolsEngine.extractPages","PageToolsEngine.splitAfter","PageToolsEngine.merge"): assert forbidden not in page_ui
    assert "snapshotCurrent" not in page_ui and "verifyPdf" not in page_ui and "PageToolsRuntime" in page_runtime
    expected={"move":"PageToolsEngine.movePage","rotate":"PageToolsEngine.rotatePage","delete":"PageToolsEngine.deletePage","extract":"PageToolsEngine.extractPages","split":"PageToolsEngine.splitAfter","merge":"PageToolsEngine.merge"};action_names=("PageMoveAction","PageRotateAction","PageDeleteAction","PageExtractAction","PageSplitAction","PageMergeAction");own_map={"move":"PageMoveAction","rotate":"PageRotateAction","delete":"PageDeleteAction","extract":"PageExtractAction","split":"PageSplitAction","merge":"PageMergeAction"}
    for key,source in actions.items():
        assert expected[key] in source and own_map[key] in source
        for other in action_names:
            if other!=own_map[key]: assert other not in source
    print("PDF stability/static isolation contract passed.")
if __name__=="__main__": main()
