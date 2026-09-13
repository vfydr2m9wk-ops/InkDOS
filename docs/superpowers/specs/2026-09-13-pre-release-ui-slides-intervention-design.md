# InkDOS 2.3 Pre-release Intervention

## Status

**USER-APPROVED — 2026-09-13**

This specification temporarily supersedes the normal Goal 3 sequence only long enough to complete three required pre-release corrections. It does not discard completed Goal 1, Goal 2, or Goal 3 work.

## Frozen Goal 3 checkpoint

InkDOS 2.3 had already advanced into Goal 3 when this intervention was approved.

Preserved Goal 3 checkpoint:

`6161eb20f7b5d8d7e58214c38c7c65202abe24c1` — `chore(goal3): narrow package diagnostics to failing bundles`

Any Goal 3 diagnostic already running from that SHA may finish and its evidence may be retained. No new Goal 3 mutation is allowed until the intervention completion gate is green.

The feature branch continues forward from the frozen work; it must never be reset to the freeze SHA after intervention commits land.

## Product priority

For InkDOS 2.3, priority is:

1. functional editing behavior and data preservation;
2. comfortable use on the actual device class;
3. visual fidelity/refinement.

Pixel-perfect reproduction of complex PowerPoint/Gamma layouts is not a release goal when the editor is functionally usable and preservation remains safe.

## Approved intervention order

Execute in this exact order:

1. **Delimited-text correction** — fix CSV/TSV delimiter detection and same-format preservation.
2. **Adaptive interface density** — Auto/Desktop/Mobile, frame/chrome density only.
3. **Presentations functional corrections** — text overflow visibility and intuitive object/text-box selection/movement.
4. Focused and cross-workspace/browser verification.
5. Integrity/checksum refresh at one coherent intervention checkpoint.
6. Record durable intervention completion with exact SHA/tests.
7. **Immediately resume Goal 3 automatically**, incorporating valid diagnostic evidence from the frozen Goal 3 work.
8. Continue Goal 3 → Goal 4 → final InkDOS 2.3 validation/release without asking for another approval.

## Part A — Delimited text preservation

Canonical detailed design:

`docs/superpowers/specs/2026-09-13-delimited-text-preservation-correction-design.md`

Required outcome:

- `.tsv` remains tab-delimited;
- `.csv` detects comma, semicolon, or stable tab structure with quote-aware logic;
- quoted delimiters and multiline quoted fields are not misclassified;
- detected delimiter is retained in workbook/session metadata;
- same-format Save/Share reuses the source delimiter;
- supported BOM/encoding behavior remains intact;
- source line-ending convention is preserved when safely determinable;
- no silent trim/coercion of literal cell text;
- synthetic privacy-safe regression tests cover semicolon CSV;
- existing CSV/TSV → XLSX compatibility warning remains intact.

## Part B — Adaptive interface density

Canonical detailed design:

`docs/superpowers/specs/2026-09-13-adaptive-interface-density-design.md`

Required outcome:

- suite-wide preference: `Auto` (default), `Desktop`, `Mobile`;
- Auto resolves to Desktop when usable viewport width is at least 900 CSS px and `(hover: hover) and (pointer: fine)` matches; otherwise Mobile;
- manual override is available through hamburger/settings UI and persists locally across workspaces;
- mode changes frame/chrome density only: bars, buttons, selects, gaps, drawers, status/navigation chrome;
- document page, spreadsheet cell, slide, PDF page, text and EPUB content geometry/zoom remain unchanged except existing user-controlled content settings;
- Mobile stays visually close to the current touch-oriented interface;
- Desktop uses the same commands/order with smaller chrome and more usable content area;
- no backend, telemetry, account, or network dependency is introduced.

## Part C — Presentations functional corrections

### Text overflow

Text must not silently disappear because editable text content exceeds the nominal text-box boundary.

Required behavior:

- overflowing editable text remains visible when no supported shrink/autofit rule requires otherwise;
- supported PPTX autofit/shrink metadata remains respected where applicable;
- opening a file does not silently rewrite source text-box geometry;
- editing overflow does not delete text;
- export preserves underlying text even if browser rendering differs slightly from PowerPoint;
- broad PPTX renderer redesign is out of scope.

### Object mode vs text edit mode

Object manipulation must not depend on discovering a tiny move handle.

Required interaction:

- first click/tap selects the object/text box;
- dragging a selected editable object moves it;
- resize/rotate remain available;
- double-click on desktop or an equivalent deliberate second interaction on touch enters text editing;
- pointer gestures inside text-edit mode select/edit text instead of moving the object;
- Escape or clicking/tapping outside exits text-edit mode without losing edits;
- movement creates one coherent Undo/Redo history operation and refreshes thumbnails/model state;
- locked/imported-unmapped rules remain unless separately proven safe.

### Fidelity boundary

Not release-blocking by itself:

- small font metric differences;
- minor wrapping differences;
- subtle character-spacing differences;
- complex Gamma/AI-generated composite-layout differences;
- minor placement differences that neither hide content nor prevent editing.

Release-blocking:

- InkDOS hard clipping hides text;
- supported editable text boxes/objects cannot be selected/moved;
- text editing causes unintended movement or lost text;
- save/export data loss;
- regressions in basic presentation open/edit/save/undo.

## Verification

### CSV/TSV

Verify focused parser/serializer contracts plus Spreadsheet browser regression in Chromium, Firefox, and WebKit. Semicolon CSV must open into separate columns and save back with semicolon.

### Adaptive density

Verify Home plus all six workspaces in representative Desktop and Mobile conditions in Chromium, Firefox, and WebKit. Switching density must not reload or reset file/session/history/selection/zoom state, and internal content geometry must remain unchanged.

### Presentations

Verify in Chromium, Firefox, and WebKit:

- overflow remains visible/preserved;
- first interaction selects rather than immediately editing text;
- selected editable object can be dragged;
- deliberate text-edit entry works;
- text selection in edit mode does not move the object;
- exiting text edit restores object manipulation;
- move participates in Undo/Redo;
- thumbnail/model updates after movement;
- existing PPT/PPTX open/save/preservation regressions remain green.

## Completion / Goal 3 resume gate

The intervention is complete only when:

1. CSV/TSV preservation correction passes focused and browser tests;
2. adaptive density passes its acceptance criteria across Home + six workspaces;
3. Presentations overflow/movement behavior passes focused tests;
4. cross-workspace regression checks are green;
5. integrity/checksum metadata is refreshed at the coherent checkpoint;
6. a durable checkpoint records exact SHA, tests, blockers, and next action.

After that checkpoint, Goal 3 resumes automatically. Before resuming, refetch the branch and the completed diagnostic evidence from `6161eb20...`; use valid evidence but never reset away intervention commits.

## Autonomous coordination rule

Every development pass must inspect current branch/PR/CI/checkpoint state before mutation. If another pass has an exact-head run or meaningful mutation in progress, do not create competing changes to the same subsystem. Work on a separable item or preserve the running evidence.

The existing InkDOS continuity automations remain enabled and are part of the approved execution model. Once the intervention completion checkpoint exists, its temporary precedence ends automatically and normal Goal 3 → Goal 4 → final release development continues.