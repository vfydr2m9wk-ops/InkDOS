from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PdfTextboxBaselineTests(unittest.TestCase):
    def test_pdf_loads_shared_workspace_baseline(self):
        index = (ROOT / "apps" / "pdf" / "index.html").read_text(encoding="utf-8")
        self.assertIn("shared/ui/workspace-layout.css", index)
        self.assertIn("shared/ui/workspace-panel-controller.js", index)
        self.assertIn("shared/ui/workspace-layout.js", index)
        self.assertEqual(index.count("shared/file-router.js"), 1)

    def test_text_box_uses_app_dialog_instead_of_annotation_prompt(self):
        annotation = (
            ROOT / "apps" / "pdf" / "review" / "annotation-layer.js"
        ).read_text(encoding="utf-8")
        controller = (
            ROOT / "apps" / "pdf" / "review" / "review-controller.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("prompt('Text:'", annotation)
        self.assertIn("requestTextAnnotation", annotation)
        self.assertIn("requestTextEdit", annotation)
        self.assertIn("textDialogForm", controller)
        self.assertIn("annotation-update", controller)
        self.assertIn("Text box inserted.", controller)
        self.assertIn("Text box updated.", controller)

    def test_review_state_mutation_is_owned_by_controller(self):
        annotation = (
            ROOT / "apps" / "pdf" / "review" / "annotation-layer.js"
        ).read_text(encoding="utf-8")
        controller = (
            ROOT / "apps" / "pdf" / "review" / "review-controller.js"
        ).read_text(encoding="utf-8")

        self.assertNotIn("state.annotations.push", annotation)
        self.assertNotIn("state.undo.push", annotation)
        self.assertIn("function commitFreeAnnotation", controller)
        self.assertIn("state.annotations.push(annotation)", controller)
        self.assertIn("state.undo.push", controller)

    def test_text_box_insert_edit_and_undo_behavior(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable")

        script = r"""
function classList(initial) {
  const values = new Set(initial || []);
  return {
    add(value) { values.add(value); },
    remove(value) { values.delete(value); },
    contains(value) { return values.has(value); },
    toggle(value, force) {
      if (force === true) values.add(value);
      else if (force === false) values.delete(value);
      else if (values.has(value)) values.delete(value);
      else values.add(value);
      return values.has(value);
    }
  };
}

const handlers = {};
const title = { textContent: '' };
const submit = { textContent: '' };
const value = { value: '', focus() {}, select() {} };
const form = {
  addEventListener(name, fn) { handlers['form:' + name] = fn; },
  querySelector() { return submit; },
  reset() { value.value = ''; }
};
const dialog = {
  classList: classList(['hidden']),
  addEventListener(name, fn) { handlers['dialog:' + name] = fn; }
};
const cancel = { addEventListener() {} };
const commentList = {
  children: [],
  textContent: '',
  replaceChildren() { this.children = []; this.textContent = ''; },
  append(node) { this.children.push(node); }
};
const pdfPages = { addEventListener() {} };
const undoReview = {};
const dirtyMark = { hidden: true };

global.document = {
  body: { dataset: {} },
  querySelectorAll() { return []; },
  getElementById(id) { return id === 'textDialogTitle' ? title : null; },
  addEventListener() {},
  createElement() { return { className: '', textContent: '', onclick: null }; }
};
global.localStorage = { getItem() { return null; }, setItem() {} };
global.prompt = () => null;
global.getSelection = () => ({ removeAllRanges() {} });
global.InkDOSPdfAnnotationLayer = {
  createAnnotationLayer() {
    return { renderPageReview() {}, wireReviewLayer() {} };
  }
};

require('./apps/pdf/review/review-controller.js');
const state = {
  storageKey: '', fingerprint: '', annotations: [], bookmarks: [], undo: [],
  tool: 'text', textSelection: null, selectionTimer: 0, pages: new Map(), page: 1
};
let serial = 0;
const controller = global.InkDOSPdfReviewController.createReviewController({
  state,
  elements: {
    commentList, dirtyMark, textDialog: dialog, textDialogForm: form,
    textDialogValue: value, dialogCancel: cancel, pdfPages, undoReview
  },
  clamp(number, minimum, maximum) {
    return Math.max(minimum, Math.min(maximum, number));
  },
  makeId() { serial += 1; return 'id-' + serial; },
  status() {}, toast() {}, renderBookmarks() {}, navigateToPage() {}, rerender() {}
});

if (!controller.requestTextAnnotation({ page: 1, x: .1, y: .1, w: .2, h: .1 })) process.exit(10);
value.value = 'First text';
handlers['form:submit']({ preventDefault() {} });
if (state.annotations.length !== 1 || state.annotations[0].text !== 'First text') process.exit(11);
if (!state.dirty) process.exit(12);

const id = state.annotations[0].id;
if (!controller.requestTextEdit(id)) process.exit(13);
value.value = 'Edited text';
handlers['form:submit']({ preventDefault() {} });
if (state.annotations[0].text !== 'Edited text') process.exit(14);
if (state.undo[state.undo.length - 1].kind !== 'annotation-update') process.exit(15);
controller.undoLastReviewAction();
if (state.annotations[0].text !== 'First text') process.exit(16);
"""
        result = subprocess.run(
            [node, "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
