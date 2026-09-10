# Prompt 2 Stage B Presentations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve reproducible Presentations fidelity defects and deliver the approved toolbar regrouping without broadening product scope.

**Architecture:** Keep `PresentationModel` and the command registry as behavior boundaries. Fix fidelity at the narrowest proven layer: importer/model/writer for data, slide surface for full rendering, slide-panel controller for thumbnail projection, and toolbar markup/CSS/bindings for visual organization. Each INKBUG gets independent evidence and tests.

**Tech Stack:** Static HTML/CSS/JavaScript, Python contract tests, Playwright Chromium/Firefox/WebKit CI, OOXML/PPT/PPTX local parsers and writers.

**Spec:** `docs/superpowers/specs/2026-09-10-prompt2-stage-b-presentations-design.md`

## Global Constraints

- Immutable regression reference: `1986ae0fd81c94fa8202c10d9dea6fcd11d807af`.
- Synthetic/privacy-safe fixtures only.
- No speculative fix for iPad/WKWebView/XeOS-only behavior.
- Keep `preview` on a launchable, basically sane candidate only.
- Preserve existing command IDs and local-first/offline architecture.
- No unrelated refactor or Office-parity expansion.

---

### Task 1: Thumbnail aspect-ratio and geometry projection

**Files:**
- Modify: `tests/test_presentations_stability_contract.py`
- Modify: `apps/presentations/ui/slide-panel-controller.js`
- Potentially modify: `apps/presentations/view/presentation-surface.css`

**Interfaces:**
- Consumes: slide `widthEmu`, `heightEmu`, and object EMU bounds.
- Produces: thumbnail paper with matching slide ratio and object coordinates scaled to the actual thumbnail viewport.

- [ ] Add a failing contract/browser regression proving non-16:9 slides and resized portrait thumbnails do not use a hard-coded `160px` geometry basis.
- [ ] Run the focused regression and record the expected RED.
- [ ] Replace the fixed projection basis with one derived from the thumbnail paper geometry while keeping the slide's own aspect ratio.
- [ ] Run Presentations contract + browser regression and record GREEN.
- [ ] Commit as a separately traceable thumbnail fidelity fix.

### Task 2: Legacy PPT text clipping investigation

**Files:**
- Inspect/modify only if proven: legacy PPT importer/model files under `apps/presentations/io/`, `apps/presentations/view/slide-surface.js`, focused tests/fixtures.

**Interfaces:**
- Consumes: imported text bounds, margins, font size, line spacing, wrapping and vertical alignment.
- Produces: read-only slide rendering that respects source text metrics within slide bounds.

- [ ] Build a privacy-safe synthetic legacy-PPT fixture or existing synthetic equivalent that stresses wrapping/box height.
- [ ] Reproduce clipping consistently and trace importer → normalized object → DOM styles.
- [ ] If reproducible, allocate/deduplicate an INKBUG ID and write the failing regression.
- [ ] Implement only the proven metric/geometry correction; do not use global visible overflow.
- [ ] Verify exact reproduction plus Presentations/cross-browser gates; otherwise record `NEEDS REAL DEVICE CONFIRMATION` and make no runtime edit.

### Task 3: PPT → editable PPTX geometry/text fidelity

**Files:**
- Inspect/modify only if proven: legacy PPT importer, presentation model, PPTX writer/conversion path, focused round-trip tests.

**Interfaces:**
- Consumes: normalized legacy slide/object geometry and formatting.
- Produces: editable PPTX whose slide-relative geometry/text properties remain materially equivalent.

- [ ] Create synthetic conversion cases covering 4:3 and 16:9 slides, text boxes, shapes and images.
- [ ] Compare source-normalized and generated/reopened model ratios/metrics.
- [ ] Allocate one INKBUG per distinct root cause and capture RED before production edits.
- [ ] Apply the smallest correction at the source of each divergence.
- [ ] Run focused round-trip + full relevant browser/integrity gates and verify reopened output.

### Task 4: Approved Presentations toolbar regrouping

**Files:**
- Modify: `apps/presentations/index.html`
- Modify: `apps/presentations/ui/editor.css`
- Modify only if required for state projection: `apps/presentations/ui/editing-controller.js`, `apps/presentations/ui/ppt-p1-tools.js`, `apps/presentations/ui/ppt-p2-tools.js`
- Test: Presentations command/control and feature regression coverage.

**Interfaces:**
- Consumes: existing command registry and current enabled/active/color state.
- Produces: grouped semantic controls with accessible labels and original InkDOS icons.

- [ ] Add a failing contract regression for semantic groups/labels and absence of raw prototype color-dot affordances.
- [ ] Regroup controls without changing command semantics.
- [ ] Replace color-dot controls with semantic text/fill/line color affordances and current-color indicators.
- [ ] Verify keyboard, narrow landscape layout, command-state projection and cross-browser behavior.
- [ ] Commit toolbar work independently from fidelity bug commits.

### Task 5: Stage-B integration gate

**Files:**
- Update audit/checkpoint documentation and derived integrity metadata only after runtime/test changes are stable.

- [ ] Run repository contracts and Presentations focused tests.
- [ ] Run relevant format-preservation round trips.
- [ ] Run Chromium/Firefox/WebKit stability and feature regressions.
- [ ] Verify no new console/runtime errors and no cross-app leakage.
- [ ] Re-fetch `main`, `preview`, issue #63, open Prompt-2 PRs and candidate branch; stop on drift/race.
- [ ] Promote `preview` only to a fully launchable candidate, then merge only on complete GREEN evidence.
- [ ] Verify post-merge `main` and persist exact SHAs/evidence/status in issue #63.
