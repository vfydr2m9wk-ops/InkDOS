from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps/presentations/app.js"
STATE = ROOT / "apps/presentations/state"
UI = ROOT / "apps/presentations/ui"
SELECTION = STATE / "selection-controller.js"
HISTORY = STATE / "history-controller.js"
INSPECTOR = UI / "inspector-controller.js"
THUMBNAILS = UI / "thumbnails-controller.js"
NOTES = UI / "presenter-notes-controller.js"
SLIDESHOW = ROOT / "apps/presentations/presentation/slideshow-controller.js"
FILE_IO = ROOT / "apps/presentations/io/file-controller.js"
RECOVERY_IO = ROOT / "apps/presentations/io/recovery-controller.js"
PPTX_WRITER = ROOT / "apps/presentations/io/pptx-write-adapter.js"
HTML = ROOT / "apps/presentations/index.html"
WORKER = ROOT / "service-worker.js"


class PresentationsModularizationTests(unittest.TestCase):
    def test_feature_components_load_before_app(self):
        html = HTML.read_text(encoding="utf-8")
        components = (
            "state/selection-controller.js?v=0.20.2.25",
            "state/history-controller.js?v=0.20.2.25",
            "ui/inspector-controller.js?v=0.20.2.25",
            "ui/thumbnails-controller.js?v=0.20.2.25",
            "ui/presenter-notes-controller.js?v=0.20.2.25",
            "presentation/slideshow-controller.js?v=0.20.2.25",
            "io/pptx-write-adapter.js?v=0.20.2.25",
            "io/file-controller.js?v=0.20.2.25",
            "io/recovery-controller.js?v=0.20.2.25",
        )
        app = "app.js?v=0.20.2.25"
        for component in components:
            self.assertIn(component, html)
            self.assertLess(html.index(component), html.index(app))

    def test_extracted_components_are_readable_and_within_new_source_limits(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        for path in (SELECTION, HISTORY, INSPECTOR, THUMBNAILS, NOTES, SLIDESHOW, PPTX_WRITER, FILE_IO, RECOVERY_IO):
            self.assertTrue(path.is_file(), path)
            source = path.read_text(encoding="utf-8").splitlines()
            self.assertLessEqual(len(source), policy["extensions"][".js"]["newFileMaxLines"], path)
            long_lines = [
                line for line in source
                if len(line) > policy["extensions"][".js"]["maxPhysicalLineLength"]
            ]
            self.assertEqual(long_lines, [], path)
            self.assertNotIn(str(path.relative_to(ROOT)), policy["grandfatheredDebt"])

    def test_app_delegates_extracted_state_and_ui_behavior(self):
        app = APP.read_text(encoding="utf-8")
        selection = SELECTION.read_text(encoding="utf-8")
        history = HISTORY.read_text(encoding="utf-8")
        inspector = INSPECTOR.read_text(encoding="utf-8")
        thumbnails = THUMBNAILS.read_text(encoding="utf-8")
        notes = NOTES.read_text(encoding="utf-8")
        slideshow = SLIDESHOW.read_text(encoding="utf-8")
        file_io = FILE_IO.read_text(encoding="utf-8")
        recovery_io = RECOVERY_IO.read_text(encoding="utf-8")
        writer = PPTX_WRITER.read_text(encoding="utf-8")

        self.assertIn("InkDeskPresentationsSelection.create", app)
        self.assertIn("InkDeskPresentationsHistory.create", app)
        self.assertIn("InkDeskPresentationsInspector.create", app)
        self.assertIn("InkDeskPresentationsThumbnails.create", app)
        self.assertIn("InkDeskPresentationsNotes.create", app)
        self.assertIn("InkDeskPresentationsSlideshow.create", app)
        self.assertIn("InkDeskPresentationsPptxWriter.create", app)
        self.assertIn("InkDeskPresentationsFileIO.create", app)
        self.assertIn("InkDeskPresentationsRecovery.create", app)
        self.assertIn("class PresentationSelectionController", selection)
        self.assertIn("class PresentationHistoryController", history)
        self.assertIn("class PresentationInspectorController", inspector)
        self.assertIn("class PresentationThumbnailsController", thumbnails)
        self.assertIn("class PresentationNotesController", notes)
        self.assertIn("class PresentationSlideshowController", slideshow)
        self.assertIn("class PresentationPptxWriteAdapter", writer)
        self.assertIn("class PresentationFileController", file_io)
        self.assertIn("class PresentationRecoveryController", recovery_io)

        self.assertNotIn("let undoStack", app)
        self.assertNotIn("let redoStack", app)
        self.assertNotIn("historyBeforeDrag", app)
        self.assertNotIn("function startDrag(", app)
        self.assertNotIn("function startResize(", app)
        self.assertNotIn("function startRotate(", app)
        self.assertNotIn("function addSelectionHandles(", app)
        self.assertNotIn("const COLORS=[", app)
        self.assertNotIn("let inspectorOpen=false", app)
        self.assertNotIn("compactInspectorQuery", app)
        self.assertNotIn("function renderMini(", app)
        self.assertNotIn("ui.notes.addEventListener('input'", app)
        self.assertNotIn("$('togglePresentationsBtn').onclick", app)
        self.assertNotIn("$('toggleNotesBtn').onclick", app)
        self.assertNotIn("function presentMode(", app)
        self.assertNotIn("function fitPresent(", app)
        self.assertNotIn("function movePresent(", app)
        self.assertNotIn("function exitPresentMode(", app)
        self.assertNotIn("presentTouchStart", app)
        self.assertNotIn("presentHelpTimer", app)
        self.assertNotIn("sourcePptxBuffer", app)
        self.assertNotIn("async function saveImportedPptx", app)
        self.assertNotIn("async function saveNewPptx", app)
        self.assertNotIn("function presentationRecoveryKey", app)
        self.assertNotIn("function patchImportedSlide(", app)
        self.assertNotIn("function shapeObj(", app)
        self.assertNotIn("function picObj(", app)
        self.assertNotIn("function patchSlideTransition(", app)

    def test_state_controllers_own_selection_interactions_and_history_stacks(self):
        selection = SELECTION.read_text(encoding="utf-8")
        history = HISTORY.read_text(encoding="utf-8")
        self.assertIn("this.selectedId = null", selection)
        self.assertIn("this.drag = null", selection)
        self.assertIn("startDrag(event)", selection)
        self.assertIn("startResize(event)", selection)
        self.assertIn("startRotate(event)", selection)
        self.assertIn("addHandles(element)", selection)
        self.assertIn("this.undoStack = []", history)
        self.assertIn("this.redoStack = []", history)
        self.assertIn("action(fn)", history)
        self.assertIn("undo()", history)
        self.assertIn("redo()", history)

    def test_slideshow_controller_owns_presentation_mode_lifecycle(self):
        slideshow = SLIDESHOW.read_text(encoding="utf-8")
        file_io = FILE_IO.read_text(encoding="utf-8")
        recovery_io = RECOVERY_IO.read_text(encoding="utf-8")
        self.assertIn("enter(fromFirst = false)", slideshow)
        self.assertIn("move(delta)", slideshow)
        self.assertIn("async exit()", slideshow)
        self.assertIn("async toggleFullscreen()", slideshow)
        self.assertIn("handleKeydown(event)", slideshow)
        self.assertIn("this.touchStart = null", slideshow)
        self.assertIn("this.helpTimer = null", slideshow)
        self.assertIn("new global.ResizeObserver", slideshow)


    def test_io_controllers_own_open_save_and_recovery_lifecycle(self):
        file_io = FILE_IO.read_text(encoding="utf-8")
        recovery_io = RECOVERY_IO.read_text(encoding="utf-8")
        for marker in (
            "async load(file)",
            "async save()",
            "async saveImportedPptx()",
            "async saveNewPptx()",
            "this.sourceBuffer = null",
            "validateZipPackage",
        ):
            self.assertIn(marker, file_io)
        for marker in (
            "async capture()",
            "async restore(context)",
            "startNewDocument()",
            "startOpenedFile(file, buffer)",
            "markDirty()",
            "markClean()",
            "promptLatest()",
        ):
            self.assertIn(marker, recovery_io)

    def test_pptx_writer_owns_package_preserving_mutation_helpers(self):
        writer = PPTX_WRITER.read_text(encoding="utf-8")
        for marker in (
            "class PresentationPptxWriteAdapter",
            "async patchImportedSlide(zip,slideData)",
            "async appendNewObjectsToSlide(zip,slideDoc,slidePath,slideData)",
            "patchSlideTransition(doc,transition)",
            "shapeObjectXml(object)",
            "pictureObjectXml(object,rid,index)",
            "orderMatchesSource()",
        ):
            self.assertIn(marker, writer)

    def test_presentations_app_ratchet_moves_down_after_io_extraction(self):
        policy = json.loads((ROOT / "architecture-policy.json").read_text(encoding="utf-8"))
        debt = policy["grandfatheredDebt"]["apps/presentations/app.js"]
        lines = APP.read_text(encoding="utf-8").splitlines()
        long_lines = sum(
            len(line) > policy["extensions"][".js"]["maxPhysicalLineLength"]
            for line in lines
        )
        self.assertEqual(debt["maxLines"], len(lines))
        self.assertEqual(debt["maxLongLines"], long_lines)
        self.assertLess(debt["maxLines"], 783)
        self.assertLess(debt["maxLines"], 700)
        self.assertLessEqual(debt["maxLongLines"], 56)

    def test_offline_shell_precaches_every_extracted_component(self):
        worker = WORKER.read_text(encoding="utf-8")
        for component in (
            "./apps/presentations/state/selection-controller.js",
            "./apps/presentations/state/history-controller.js",
            "./apps/presentations/ui/inspector-controller.js",
            "./apps/presentations/ui/thumbnails-controller.js",
            "./apps/presentations/ui/presenter-notes-controller.js",
            "./apps/presentations/presentation/slideshow-controller.js",
            "./apps/presentations/io/pptx-write-adapter.js",
            "./apps/presentations/io/file-controller.js",
            "./apps/presentations/io/recovery-controller.js",
        ):
            self.assertIn(component, worker)

    def test_manual_browser_harnesses_load_components_before_presentations_app(self):
        paths = (
            "tests/browser/revalidate_v0201_consistency.py",
            "tests/browser/revalidate_pptx_three_eras.py",
            "tests/browser/revalidate_cross_workspace_isolation.py",
            "tests/browser/revalidate_transactional_open_failures.py",
            "tests/browser/revalidate_launch_and_offline_modes.py",
        )
        components = (
            "apps/presentations/state/selection-controller.js",
            "apps/presentations/state/history-controller.js",
            "apps/presentations/ui/inspector-controller.js",
            "apps/presentations/ui/thumbnails-controller.js",
            "apps/presentations/ui/presenter-notes-controller.js",
            "apps/presentations/presentation/slideshow-controller.js",
            "apps/presentations/io/pptx-write-adapter.js",
            "apps/presentations/io/file-controller.js",
            "apps/presentations/io/recovery-controller.js",
        )
        app = "apps/presentations/app.js"
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for component in components:
                self.assertIn(component, text, relative)
                self.assertLess(text.index(component), text.index(app), relative)


if __name__ == "__main__":
    unittest.main()
