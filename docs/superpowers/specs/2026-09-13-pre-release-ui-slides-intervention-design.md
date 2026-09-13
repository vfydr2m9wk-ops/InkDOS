# InkDOS 2.3 Pre-release UI and Presentations Intervention

## Status

**NEEDS USER REVIEW — RUNTIME DEVELOPMENT FROZEN**

This specification supersedes the earlier chronological sequence only for this temporary pre-release intervention. It does not discard completed Goal 1, Goal 2, or Goal 3 work.

## Current development state

InkDOS 2.3 had already advanced into Goal 3 when this intervention was requested.

The preserved Goal 3 freeze checkpoint is:

`6161eb20f7b5d8d7e58214c38c7c65202abe24c1` — `chore(goal3): narrow package diagnostics to failing bundles`

Any Goal 3 diagnostic already running from that checkpoint may finish and its evidence may be retained. No new Goal 3 runtime/package mutation is allowed while this intervention is active.

The intervention is implemented on top of the existing feature branch. Goal 3 work is not reverted or abandoned.

## Product priority

For InkDOS 2.3, the priority is:

1. functional editing behavior and data preservation;
2. comfortable use on the actual device class;
3. visual fidelity/refinement.

The current mobile-oriented visual design is already satisfactory enough. Desktop changes should reclaim frame space for content rather than redesign the product.

For Presentations, usable editing behavior is more important than pixel-perfect reproduction of complex PowerPoint/Gamma layouts.

## Intervention order

The temporary intervention is executed in this exact order:

1. Adaptive interface density — Auto / Desktop / Mobile.
2. Presentations functional corrections — text overflow and object/text-box movement/selection.
3. Focused and cross-workspace verification plus integrity refresh.
4. Mark the intervention complete.
5. Automatically resume Goal 3 from the preserved work, incorporating completed diagnostic evidence without reverting the intervention.
6. Continue Goal 3, then Goal 4, then final InkDOS 2.3 validation/release.

No new approval is required between intervention completion and resumption of Goal 3.

---

# Part A — Adaptive interface density

The detailed density design remains defined by:

`docs/superpowers/specs/2026-09-13-adaptive-interface-density-design.md`

This intervention fixes its chronological context: density work now temporarily interrupts Goal 3 rather than occurring before Goal 2.

## Required behavior

One suite-wide local preference:

- `Auto` — default
- `Desktop`
- `Mobile`

`Auto` resolves at workspace startup:

- Desktop when usable viewport width is at least 900 CSS px and `(hover: hover) and (pointer: fine)` matches;
- Mobile otherwise.

Manual override is available through the hamburger/settings UI and persists locally across workspaces.

The mode affects **frame/chrome density only**:

- top bars;
- editing toolbars;
- buttons;
- dropdowns/selects;
- frame padding/gaps;
- hamburger/drawer controls;
- status bars;
- navigation chrome such as thumbnail rails when appropriate.

It must not change internal content geometry or zoom:

- document page dimensions;
- spreadsheet cell dimensions;
- slide dimensions;
- PDF page geometry;
- text/EPUB content scaling except user-controlled content settings.

Mobile stays visually close to the current InkDOS UI. Desktop uses the same controls and ordering with smaller frame dimensions and more content space.

No backend, telemetry, account, or network dependency is introduced.

---

# Part B — Presentations functional corrections

## Scope principle

Do not reopen broad PPTX fidelity work for InkDOS 2.3 unless a narrowly identified fix is low risk and directly supports usability or preservation.

Complex presentations produced by Gamma or similar tools may not render pixel-perfect even in PowerPoint itself. Minor visual discrepancies are not a 2.3 release blocker once the editor is functionally usable and preservation remains safe.

## 1. Text overflow must not disappear silently

Current behavior can clip text at the text-box boundary. This is unacceptable as an editing default because content appears to vanish.

Required behavior:

- content beyond the nominal text-box height must remain visible during editing when the presentation does not explicitly require a supported shrink/autofit behavior;
- existing supported PPTX autofit/shrink metadata should continue to be respected when applicable;
- merely opening a file must not silently rewrite the source text-box geometry;
- editing text must not silently delete text because it exceeds the box;
- export must preserve the underlying text content even when the browser presentation view cannot perfectly reproduce PowerPoint layout.

The implementation should remove hard clipping from the editable text-content path rather than automatically enlarging every imported box on load.

## 2. Text boxes and objects must be easy to move

The user must not need to discover a tiny dedicated move handle to reorganize a slide.

Required interaction model:

### Object mode

- first click/tap selects the text box/object;
- dragging a selected object moves it;
- resize and rotate handles remain available where the object is editable;
- movement updates the model and participates in Undo/Redo.

### Text edit mode

- double-click on desktop, or an equivalent deliberate second interaction on touch, enters text editing for a text box;
- while text is being edited, pointer gestures inside the text edit surface manipulate/select text rather than moving the whole object;
- `Escape`, clicking/tapping outside, or another clear exit interaction leaves text-edit mode and returns to object mode without losing edits.

The implementation must avoid accidental object movement while the user is selecting text.

## 3. Mouse, trackpad, and touch

The same conceptual model must work for:

- desktop mouse;
- desktop trackpad;
- touch/mobile/tablet.

Touch targets remain usable in Mobile density. Desktop density may use smaller chrome controls, but slide-object manipulation itself must remain practical.

## 4. Geometry and preservation

Moving/resizing/rotating an editable object must:

- update the presentation model deterministically;
- remain within existing slide-boundary rules unless the current model explicitly supports off-slide geometry;
- create one coherent history operation per gesture;
- refresh the slide thumbnail after the gesture completes;
- preserve unrelated text/style/PPTX metadata.

Existing locked/imported-unmapped object rules remain in force unless a specific safe support path is added with tests.

## 5. Fidelity boundary for 2.3

Not release-blocking by itself:

- small font metric differences;
- minor line-wrap differences;
- subtle character spacing differences;
- highly complex Gamma/AI-generated composite layouts;
- minor object placement differences that do not hide content or prevent editing.

Release-blocking:

- text content hidden by InkDOS hard clipping;
- inability to select/move supported editable text boxes/objects;
- editing interaction that causes unintended moves or lost text;
- save/export data loss;
- regressions in basic presentation open/edit/save/undo behavior.

---

# Verification

## Adaptive density

Verify Home plus all six workspaces in representative Desktop and Mobile conditions.

Required browsers:

- Chromium
- Firefox
- WebKit

Verify Auto detection, overrides, persistence, no reload/session loss, and unchanged internal content geometry.

## Presentations

Add focused regression coverage for:

- overflowing text remains present/visible in the editable surface;
- first interaction selects object without immediately forcing text edit;
- selected text box/object can be dragged;
- text edit mode can be entered deliberately;
- dragging/selecting text in edit mode does not move the object;
- exit from text mode restores object manipulation;
- move participates in Undo/Redo;
- thumbnail/model updates after move;
- existing PPT/PPTX open/save and preservation regressions remain green.

Run the relevant Presentations browser matrix in Chromium, Firefox, and WebKit plus the cross-workspace stability suite before closing the intervention.

## Goal 3 resume gate

The intervention is complete only when:

1. density behavior passes its acceptance criteria;
2. Presentations overflow and movement behavior passes focused tests;
3. cross-workspace regression checks are green;
4. integrity/checksum metadata is refreshed at the coherent checkpoint;
5. a durable completion checkpoint records exact SHA and validation evidence.

After that checkpoint, development automatically resumes Goal 3.

Before resuming, refetch the branch and the completed Goal 3 diagnostic from `6161eb20...`. Use any valid diagnostic evidence, but do not reset the branch to the freeze SHA and do not discard intervention commits.

## Coordination rule for autonomous development

Every development pass must first inspect current branch/PR/CI/checkpoint state before mutation.

If another pass has an exact-head CI run or meaningful mutation in progress, do not create competing changes to the same subsystem. Preserve the current evidence or work on an explicitly separable task.

The temporary intervention takes precedence over Goal 3 until its completion checkpoint exists. Once completed, the temporary precedence ends automatically and the normal Goal 3 → Goal 4 → final release sequence resumes.
