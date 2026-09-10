# Prompt 2 Presentations Toolbar Regrouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regroup the existing Presentations toolbar by user-facing function and replace prototype-like color glyphs with semantic InkDOS icons/current-color indicators without changing presentation capabilities or file behavior.

**Architecture:** Preserve every existing command/input ID and controller API. Add stable semantic group hosts to the existing horizontally scrollable toolbar, let `ppt-p1-tools.js` mount its existing dynamic controls into those hosts, and style semantic SVG color controls through the existing Presentations CSS. The work is UI-only and does not touch parser/writer/model code.

**Tech Stack:** Static HTML/CSS/JavaScript, existing InkDOS Presentations controllers, pytest static contracts, Playwright Chromium/Firefox/WebKit regression suites.

**Spec:** `docs/superpowers/specs/2026-09-10-prompt2-presentations-toolbar-design.md`

## Global Constraints

- Preserve all existing Presentations command/input IDs and event-handler semantics.
- Do not add editing capabilities or alter legacy `.ppt` read-only policy.
- Do not touch presentation parser/writer/model behavior in this subproject.
- Keep horizontal toolbar scrolling, light/dark appearance and existing touch-target conventions.
- Use original inline SVG iconography; do not copy proprietary assets.
- Use only synthetic/private-safe test data; never add user screenshots, filenames/content, credentials or telemetry.
- `preview` may move only after the cumulative Stage-B head is launchable and verified; exact-head integrity and browser gates are required before integration.

---

### Task 1: Lock the semantic toolbar contract with a RED regression

**Files:**
- Modify: `tests/test_presentations_stability_contract.py`
- Read: `apps/presentations/index.html`
- Read: `apps/presentations/ui/ppt-p1-tools.js`

**Interfaces:**
- Consumes: current toolbar DOM IDs and dynamic P1 control IDs.
- Produces: focused static regression `test_presentations_toolbar_uses_semantic_groups_and_color_controls()` protecting group hosts, IDs and semantic color-control structure.

- [ ] **Step 1: Add a failing contract test**

Add a test that reads `apps/presentations/index.html` and `apps/presentations/ui/ppt-p1-tools.js`, then asserts these exact design invariants:

```python
def test_presentations_toolbar_uses_semantic_groups_and_color_controls():
    html = read("apps/presentations/index.html")
    p1 = read("apps/presentations/ui/ppt-p1-tools.js")

    for group_id, label in (
        ("pptToolbarSlides", "Slides"),
        ("pptToolbarInsert", "Insert"),
        ("pptToolbarText", "Text formatting"),
        ("pptToolbarObjectStyle", "Object style"),
    ):
        assert f'id="{group_id}"' in html
        assert f'aria-label="{label}"' in html

    for control_id in (
        "pptP1ImageBtn", "pptP1Shape", "pptP1TextColor",
        "pptP1Fill", "pptP1Border", "pptP1Bullets", "pptP1Layout",
    ):
        assert control_id in p1

    assert "ppt-p1-color-icon" in p1
    assert "ppt-p1-color-swatch" in p1
    assert "<svg" in p1
    assert "'●'" not in p1
    assert "'○'" not in p1
```

Use the test file's existing `read(...)` helper or its established repository-root helper rather than introducing a second file-loading abstraction.

- [ ] **Step 2: Run the focused test and capture RED**

Run:

```bash
pytest -q tests/test_presentations_stability_contract.py -k toolbar_uses_semantic_groups_and_color_controls
```

Expected: FAIL because the semantic group hosts and semantic SVG/swatch structure do not exist and the current P1 color control still contains raw `●` / `○` glyphs.

- [ ] **Step 3: Confirm RED is scoped, not an unrelated repository failure**

Run:

```bash
pytest -q tests/test_presentations_stability_contract.py
```

Expected: existing tests PASS and only the newly added toolbar contract FAILS. If another test fails, diagnose that failure before production edits.

- [ ] **Step 4: Commit the RED regression alone**

```bash
git add tests/test_presentations_stability_contract.py
git commit -m "test: define semantic Presentations toolbar contract"
```

Do not update `preview` to this RED-only commit.

---

### Task 2: Establish semantic group hosts without changing commands

**Files:**
- Modify: `apps/presentations/index.html`
- Test: `tests/test_presentations_stability_contract.py`

**Interfaces:**
- Consumes: all current static command IDs (`undoBtn`, `redoBtn`, `slidePanelBtn`, `prevSlideBtn`, `nextSlideBtn`, `addSlideBtn`, `duplicateSlideBtn`, `deleteSlideBtn`, `insertTextBtn`, `fontSize`, `boldBtn`, `italicBtn`, `alignSelect`, `zoomMenuBtn`, `presentBtn`).
- Produces: stable dynamic mount hosts `pptToolbarSlides`, `pptToolbarInsert`, `pptToolbarText`, `pptToolbarObjectStyle` while retaining static History/navigation and View/presentation groups.

- [ ] **Step 1: Reorganize only toolbar containers in `index.html`**

Keep every existing button/select element and ID. Use this group topology:

```html
<div class="tool-group" role="group" aria-label="History and navigation">...</div>
<span class="tool-divider" aria-hidden="true"></span>
<div id="pptToolbarSlides" class="tool-group" role="group" aria-label="Slides">...</div>
<span class="tool-divider" aria-hidden="true"></span>
<div id="pptToolbarInsert" class="tool-group" role="group" aria-label="Insert">...</div>
<span class="tool-divider" aria-hidden="true"></span>
<div id="pptToolbarText" class="tool-group" role="group" aria-label="Text formatting">...</div>
<span class="tool-divider" aria-hidden="true"></span>
<div id="pptToolbarObjectStyle" class="tool-group" role="group" aria-label="Object style"></div>
<span class="tool-divider" aria-hidden="true"></span>
<div class="tool-group" role="group" aria-label="View and presentation">...</div>
```

Place New/Duplicate/Delete in `pptToolbarSlides`, Insert Text in `pptToolbarInsert`, font size/Bold/Italic/Alignment in `pptToolbarText`, and Zoom/Present in View and presentation. Do not create duplicate static controls.

- [ ] **Step 2: Run syntax/static contract tests**

```bash
pytest -q tests/test_presentations_stability_contract.py
```

Expected: the group-host portion of the new test now passes; the test remains RED only on dynamic semantic color-control expectations.

- [ ] **Step 3: Verify command IDs are unique in the resulting HTML**

Use the repository's existing HTML/static contract checks; additionally inspect the focused test output if it already counts IDs. If no existing uniqueness assertion covers these controls, extend the focused test with:

```python
for control_id in ("addSlideBtn", "duplicateSlideBtn", "deleteSlideBtn", "insertTextBtn", "fontSize", "boldBtn", "italicBtn", "alignSelect", "zoomMenuBtn", "presentBtn"):
    assert html.count(f'id="{control_id}"') == 1
```

- [ ] **Step 4: Commit the semantic host change**

```bash
git add apps/presentations/index.html tests/test_presentations_stability_contract.py
git commit -m "refactor: group Presentations toolbar by function"
```

---

### Task 3: Mount existing P1 tools into their semantic groups

**Files:**
- Modify: `apps/presentations/ui/ppt-p1-tools.js`
- Test: `tests/test_presentations_stability_contract.py`

**Interfaces:**
- Consumes: group hosts `pptToolbarSlides`, `pptToolbarInsert`, `pptToolbarText`, `pptToolbarObjectStyle`.
- Produces: same existing controls and event handlers, mounted as: Layout→Slides; Image/Shape→Insert; Bullets/Text color→Text formatting; Fill/Border→Object style.

- [ ] **Step 1: Replace the monolithic `pptP1Tools` insertion with host-based mounting**

Keep `build()` idempotent. Resolve the four group hosts, create each existing control exactly once, and append controls as follows:

```javascript
slides.append(layout);
insert.append(image, shape);
text.append(bullets, textCtl.wrap);
objectStyle.append(fillCtl.wrap, borderCtl.wrap);
```

Retain the hidden image file input and every existing `onclick` / `onchange` handler. Keep `sync()` using the same control IDs and editable/object-selection policy.

If any required host is absent, return before creating controls so partial initialization cannot duplicate or orphan controls.

- [ ] **Step 2: Preserve an idempotence marker without implementation jargon in the visible toolbar**

`pptP1Tools` may remain an internal JS marker only if needed, but no visible group should expose `Object editing`, `P1`, or `P2`. Prefer a private `built` boolean or a non-visible data marker if that is simpler than retaining an empty DOM group.

- [ ] **Step 3: Run the focused contract**

```bash
pytest -q tests/test_presentations_stability_contract.py -k toolbar_uses_semantic_groups_and_color_controls
```

Expected: still RED only for semantic color SVG/swatch behavior until Task 4; group placement/control-ID checks should pass.

- [ ] **Step 4: Commit dynamic regrouping**

```bash
git add apps/presentations/ui/ppt-p1-tools.js tests/test_presentations_stability_contract.py
git commit -m "refactor: mount presentation tools by semantic group"
```

---

### Task 4: Replace raw color glyphs with semantic icons and current-color indicators

**Files:**
- Modify: `apps/presentations/ui/ppt-p1-tools.js`
- Modify: `apps/presentations/ui/editor.css`
- Test: `tests/test_presentations_stability_contract.py`

**Interfaces:**
- Consumes: existing native color input values and `sync()` selected-object state.
- Produces: semantic `.ppt-p1-color-icon` SVG and `.ppt-p1-color-swatch` whose color reflects the associated input; existing input IDs/events remain authoritative.

- [ ] **Step 1: Implement semantic icon markup in `colorControl(...)`**

Replace the raw glyph span with an inline SVG selected by `kind`. Use repository-safe SVG paths, for example:

```javascript
const icons={
  text:'<svg class="ppt-p1-color-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 18 12 5l6 13M8.5 13h7"/></svg>',
  fill:'<svg class="ppt-p1-color-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="m7 5 8 8-5 5-6-6zM13 7l2-2 4 4-2 2"/></svg>',
  border:'<svg class="ppt-p1-color-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="5" width="14" height="14" rx="1"/><path d="M7 17 17 7"/></svg>'
};
```

Append a separate `<span class="ppt-p1-color-swatch" aria-hidden="true"></span>` and set a wrapper CSS custom property such as `--tool-color` from the input value.

- [ ] **Step 2: Synchronize the current-color indicator**

Add a small helper:

```javascript
function setControlColor(control,value){
  if(!control||!value)return;
  control.input.value=value;
  control.wrap.style.setProperty('--tool-color',value);
}
```

Call it when creating each control and from `sync()` when the selected object exposes applicable text/fill/border values. Do not synthesize a value that would mutate the selected object; this is display synchronization only.

- [ ] **Step 3: Style the semantic controls in `editor.css`**

Use existing tokens/currentColor for icon chrome and `var(--tool-color)` only for the swatch. Keep the native color input focusable/clickable. A suitable structure is:

```css
.ppt-p1-color-control{position:relative;display:inline-grid;place-items:center;min-width:36px;min-height:36px}
.ppt-p1-color-icon{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}
.ppt-p1-color-swatch{position:absolute;left:8px;right:8px;bottom:4px;height:3px;border-radius:999px;background:var(--tool-color,currentColor);pointer-events:none}
```

Adapt selectors to the existing `.ppt-p1-color-input` CSS so the actual input remains interactive; do not hide it with `display:none` or remove keyboard access.

- [ ] **Step 4: Run focused GREEN**

```bash
pytest -q tests/test_presentations_stability_contract.py -k toolbar_uses_semantic_groups_and_color_controls
```

Expected: PASS.

- [ ] **Step 5: Run all Presentations static contracts**

```bash
pytest -q tests/test_presentations_stability_contract.py
```

Expected: PASS.

- [ ] **Step 6: Commit semantic color controls**

```bash
git add apps/presentations/ui/ppt-p1-tools.js apps/presentations/ui/editor.css tests/test_presentations_stability_contract.py
git commit -m "feat: add semantic presentation color controls"
```

---

### Task 5: Verify browser behavior and cumulative Stage-B safety

**Files:**
- Test only; no production files should change unless a reproduced regression requires a separately diagnosed fix.

**Interfaces:**
- Consumes: cumulative Stage-B candidate containing INKBUG-0011 fix plus the toolbar commits.
- Produces: exact-head evidence sufficient to decide whether the candidate is launchable and whether `preview` may advance.

- [ ] **Step 1: Run Presentations app-local/browser tests**

Run the repository's Presentations browser/stability test targets, including `tests/test_presentations_stability_browser.py` if present and relevant feature-browser contracts. Verify in Chromium first, then Firefox and WebKit using the existing test command/matrix rather than inventing a second harness.

Expected: existing editing, selection, image/shape insertion, text formatting, color changes, disabled/read-only legacy-PPT behavior, toolbar scrolling and Present controls remain functional.

- [ ] **Step 2: Re-run the Stage-B fidelity regression**

Run the focused 4:3/16:9 legacy-PPT→PPTX round-trip test that reproduces INKBUG-0011.

Expected: PASS with no duplicate text object and supported text/shape/image object presence/bounds preserved according to the existing regression tolerance.

- [ ] **Step 3: Run repository and package-integrity gates**

Run the existing repository validation/clean-snapshot/integrity commands defined by the repository workflows. Do not weaken checks or manually bless stale metadata. If derived checksums need refresh, use only the repository's established generated-metadata process.

- [ ] **Step 4: Obtain exact-head Chromium/Firefox/WebKit matrix**

Require all existing validation jobs on the exact candidate SHA: repository contracts, format-preservation round trips, Stability Chromium/Firefox/WebKit and Feature browser regressions Chromium/Firefox/WebKit.

Expected: all GREEN. A bot-authored metadata head with `action_required`/zero jobs is not exact-head evidence; obtain a subsequent executable human-authored candidate/check suite rather than claiming verification.

- [ ] **Step 5: Update the Prompt-2 checkpoint**

Record in issue #63: Stage B; exact branch/head; INKBUG-0011 status; toolbar unit status; tests/jobs; clipping remains `NEEDS REAL DEVICE CONFIRMATION / SYNTHETIC REPRODUCTION`; `preview` target; and the exact next action.

- [ ] **Step 6: Promote `preview` only if sane and verified**

If the exact cumulative candidate is GREEN and launchable, fast-forward `preview` to it after a fresh `main`/`preview`/#63/open-PR/head reconciliation. Do not move preview to any RED-only or partially verified state.

- [ ] **Step 7: Commit only if verification produced a legitimate repository metadata delta**

Any generated integrity metadata commit must contain only the repository-defined derived files and must be followed by exact-head verification before merge. Do not create a content-free commit merely to manufacture CI evidence.