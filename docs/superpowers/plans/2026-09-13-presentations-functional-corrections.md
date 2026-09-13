# Presentations Functional Corrections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Presentations function like a practical slide editor: overflowing text stays visible/preserved, supported objects/text boxes are easy to select and move, and text editing is distinct from object manipulation.

**Architecture:** Keep the existing presentation model/history/export pipeline. Concentrate interaction changes in `SlideSurface` and narrowly scoped CSS: explicit object-selection mode, deliberate text-edit entry, direct drag of selected editable objects, existing resize/rotate gesture reuse, and editable text overflow that is not hard-clipped. Do not redesign the PPTX renderer or chase pixel-perfect Gamma/PowerPoint fidelity.

**Tech Stack:** Static JavaScript/CSS, existing InkDOS Presentations session/selection/history, Playwright browser tests, current PPT/PPTX regression suite.

**Spec:** `docs/superpowers/specs/2026-09-13-pre-release-ui-slides-intervention-design.md`

## Global Constraints

- Execute after CSV/TSV preservation and adaptive-density blocks are green.
- Functionality/preservation outrank visual fidelity.
- Do not rewrite imported geometry merely because text overflows.
- Preserve existing supported PPTX autofit/shrink semantics where applicable.
- Keep locked/imported-unmapped restrictions unless separately proven safe.
- One coherent history operation per move/resize/rotate gesture.
- Existing open/edit/save/undo/PPT/PPTX preservation regressions must remain green.

---

### Task 1: Add RED overflow and interaction contracts

**Files:**
- Modify: `tests/test_presentations_stability_contract.py`
- Modify: `tests/test_presentations_stability_browser.py`
- Test target: `apps/presentations/view/slide-surface.js`
- Test target: `apps/presentations/view/presentation-surface.css`

**Interfaces:**
- Consumes current `SlideSurface.create({session,stage,shell,canvas,selection,history,onModelChange})`.
- Produces required behavior markers for object mode, text-edit mode, direct dragging, and non-clipping editable text.

- [ ] **Step 1: Add static contract for non-clipping editable text**

Require editable rich text to avoid `overflow:hidden` on the text-content path and require a distinct class/data state for text editing. Keep slide-canvas clipping intact so slide content outside the slide does not leak globally.

- [ ] **Step 2: Add static contract for explicit editing state**

Require state such as `editingTextId` (or equivalent), deliberate enter/exit functions, Escape handling, and direct object drag using the existing gesture/history machinery.

- [ ] **Step 3: Add browser overflow regression**

Insert a text box whose text exceeds its nominal height; assert full text remains in the DOM/visible editable flow and model text is intact after blur/history.

- [ ] **Step 4: Add browser selection/movement regression**

Assert first click selects without forcing text editing; drag selected object and verify model `x/y` change; undo restores original geometry; thumbnail/model callback completes.

- [ ] **Step 5: Add browser text-edit separation regression**

Enter text edit deliberately (double click on fine pointer; equivalent API/event path for touch), drag/select inside text and assert object geometry does not change; press Escape and confirm object mode returns.

- [ ] **Step 6: Run tests and confirm RED**

```bash
python tests/test_presentations_stability_contract.py
BROWSER=chromium python tests/test_presentations_stability_browser.py
```

Expected: FAIL on current hard clipping/direct-edit interaction model.

- [ ] **Step 7: Commit RED tests**

```bash
git add tests/test_presentations_stability_contract.py tests/test_presentations_stability_browser.py
git commit -m "test(presentations): cover overflow and object interaction"
```

---

### Task 2: Remove hard clipping from editable text without rewriting geometry

**Files:**
- Modify: `apps/presentations/view/presentation-surface.css`
- Modify if required: `apps/presentations/view/slide-surface.js`
- Test: `tests/test_presentations_stability_contract.py`
- Test: `tests/test_presentations_stability_browser.py`

**Interfaces:**
- Consumes current text box model (`h`, margins, `autoFitScale`, paragraphs/runs).
- Produces visible editable overflow while preserving source geometry/model data.

- [ ] **Step 1: Keep box geometry but let editable content overflow vertically**

Do not change `o.h` just to display overflow. Remove hard clipping from `.rich-text-content`/editable text path and ensure the selected text box can display content beyond its nominal height during editing/view where no supported autofit rule requires shrink.

- [ ] **Step 2: Preserve slide boundary clipping**

Keep `.slide-canvas{overflow:hidden}` so content cannot paint outside the slide itself. This still allows text to extend past its own box while remaining clipped at slide edges.

- [ ] **Step 3: Keep supported autofit scale behavior**

Continue applying existing `o.autoFitScale` to runs/paragraph line sizes. Do not invent automatic box growth on file open.

- [ ] **Step 4: Run focused tests**

```bash
python tests/test_presentations_stability_contract.py
BROWSER=chromium python tests/test_presentations_stability_browser.py
```

Expected: overflow regression passes; interaction may remain RED until Task 3.

- [ ] **Step 5: Commit overflow fix**

```bash
git add apps/presentations/view/presentation-surface.css apps/presentations/view/slide-surface.js tests/test_presentations_stability_contract.py tests/test_presentations_stability_browser.py
git commit -m "fix(presentations): keep overflowing text visible"
```

---

### Task 3: Separate object mode from text-edit mode

**Files:**
- Modify: `apps/presentations/view/slide-surface.js`
- Modify: `apps/presentations/view/presentation-surface.css`
- Test: `tests/test_presentations_stability_browser.py`

**Interfaces:**
- Produces `enterTextEdit(objectId)`, `exitTextEdit({commit})` or equivalent internal functions; selected object remains authoritative in `selection`; text edit state is local to SlideSurface.

- [ ] **Step 1: Default text boxes to object interaction mode**

A first pointer/click selects the text box but does not immediately place the contentEditable surface into active text editing.

- [ ] **Step 2: Enter text editing deliberately**

On fine-pointer desktop, double click a selected text box to enable/focus its `.rich-text-content`. On touch, use a deliberate second tap/activation that does not conflict with drag. Preserve spellcheck and existing focus/blur snapshot behavior once editing starts.

- [ ] **Step 3: Exit edit mode safely**

Escape and pointer interaction outside the active text content must commit pending text through the existing history/model path, disable active editing, and return to object mode without losing content.

- [ ] **Step 4: Prevent object movement while editing text**

Pointerdown/move inside active text content must stop the object drag path so selecting text cannot move the text box.

- [ ] **Step 5: Add visual state only where useful**

Use a class/data attribute to distinguish object selection from active text editing. Do not introduce large new chrome.

- [ ] **Step 6: Run browser regression**

```bash
BROWSER=chromium python tests/test_presentations_stability_browser.py
```

Expected: selection/edit-mode assertions pass.

- [ ] **Step 7: Commit mode separation**

```bash
git add apps/presentations/view/slide-surface.js apps/presentations/view/presentation-surface.css tests/test_presentations_stability_browser.py
git commit -m "feat(presentations): separate object and text edit modes"
```

---

### Task 4: Allow direct drag of selected editable objects

**Files:**
- Modify: `apps/presentations/view/slide-surface.js`
- Modify: `apps/presentations/ui/editor.css` only if cursor/selection feedback needs adjustment
- Test: `tests/test_presentations_stability_browser.py`

**Interfaces:**
- Reuses current gesture object (`kind`, `id`, `p0`, geometry, `before`) and `moveGesture/endGesture` history commit.
- Produces direct object drag without requiring the small dedicated move handle.

- [ ] **Step 1: Factor gesture start so handle and object body can share it**

Create a helper that starts `move`, `resize`, or `rotate` with the same snapshot/coordinate logic. Existing handles continue to use resize/rotate; move handle may remain as an affordance but is no longer required.

- [ ] **Step 2: Start move from selected object body in object mode**

For `editableGeometry(o)`, pointerdown on a selected text/image/shape/table object body starts move unless text-edit mode is active or the event comes from an interactive text-edit surface.

- [ ] **Step 3: Preserve slide-boundary rules and one history commit**

Keep current clamping logic and `history.commitFromBefore('Move object', before)` at gesture end. Call `onModelChange({renderThumbs:true})` only once after a meaningful move.

- [ ] **Step 4: Verify mouse/trackpad and touch pointer paths**

Use Pointer Events, `touch-action` only where needed, and pointer capture/window listeners already present. Avoid separate mouse-only code.

- [ ] **Step 5: Run browser tests**

```bash
BROWSER=chromium python tests/test_presentations_stability_browser.py
BROWSER=firefox python tests/test_presentations_stability_browser.py
BROWSER=webkit python tests/test_presentations_stability_browser.py
```

Expected: PASS on all three.

- [ ] **Step 6: Commit direct movement**

```bash
git add apps/presentations/view/slide-surface.js apps/presentations/ui/editor.css tests/test_presentations_stability_browser.py
git commit -m "feat(presentations): drag selected objects directly"
```

---

### Task 5: Verify preservation and avoid fidelity scope creep

**Files:**
- No broad production changes unless a focused regression proves one is needed.
- Existing tests: `tests/test_presentations_stability_contract.py`, `tests/test_presentations_stability_browser.py`, Goal 2 PPTX preservation/fidelity tests already on the branch.

- [ ] **Step 1: Run Presentations contract + browser matrix**

```bash
python tests/test_presentations_stability_contract.py
BROWSER=chromium python tests/test_presentations_stability_browser.py
BROWSER=firefox python tests/test_presentations_stability_browser.py
BROWSER=webkit python tests/test_presentations_stability_browser.py
```

- [ ] **Step 2: Run existing Goal 2/PPTX preservation regressions registered by release validation**

Use `scripts/run_release_validation.py` or the narrow registered tests when full execution is available. Do not change font metrics/character spacing/layout merely to improve screenshots unless a data-loss/usability regression requires it.

- [ ] **Step 3: Run cross-suite stability**

```bash
python tests/test_cross_suite_stability_contract.py
BROWSER=chromium python tests/test_cross_suite_stability_browser.py
```

Repeat browser suite on Firefox/WebKit at the coherent intervention checkpoint.

- [ ] **Step 4: Record exact green SHA and hand off to intervention completion gate**

Do not resume Goal 3 until CSV, density, Presentations, cross-suite checks, and final integrity refresh are all green.

---

### Task 6: Complete intervention and resume Goal 3 automatically

- [ ] **Step 1: Refetch branch/PR/CI to ensure no concurrent mutation is unaccounted for**
- [ ] **Step 2: Refresh integrity/checksum metadata once for the coherent three-part intervention**
- [ ] **Step 3: Run final relevant release/static/browser gates on the exact refreshed head**
- [ ] **Step 4: Write durable checkpoint with exact SHA, CSV/density/Presentations evidence, and any known non-blocking fidelity limits**
- [ ] **Step 5: Refetch the completed Goal 3 diagnostic from frozen SHA `6161eb20...` and retain valid evidence**
- [ ] **Step 6: Immediately resume Goal 3 on the current branch without resetting intervention commits; then continue Goal 4 and final 2.3 release sequence**
