# Prompt 2 Presentations Toolbar Regrouping — Design

## Status and scope

This is the approved Stage-B Presentations toolbar/iconography subproject from Prompt 2. It is intentionally isolated from legacy-PPT clipping and PPT→PPTX fidelity fixes even though it remains on the same canonical Stage-B integration trail.

The change is a UI organization and affordance improvement only. It must not add presentation features, alter file-format behavior, change the presentation model, broaden Office parity claims, or weaken read-only legacy-PPT policy.

## Problem

The current toolbar mixes navigation, slide lifecycle, insertion, text formatting, object styling and view actions across a base toolbar plus a dynamically injected `pptP1Tools` group. The dynamic color controls use raw `A`, `●` and `○` glyphs next to native color inputs. This makes the editing hierarchy look provisional and does not communicate text color, fill and border/stroke roles as clearly as semantic controls do.

## Design goals

1. Preserve every existing command and command ID so controller wiring and keyboard behavior continue to work.
2. Present controls in functional groups that can be scanned without learning implementation phases such as P1/P2.
3. Replace raw color-dot affordances with original InkDOS semantic SVG iconography plus an explicit current-color indicator.
4. Preserve horizontal toolbar scrolling, touch-safe targets, light/dark appearance, disabled states and the legacy-PPT read-only boundary.
5. Keep the implementation local to Presentations and avoid proprietary assets or visual copying.

## Target toolbar organization

The toolbar remains one horizontally scrollable strip. Existing controls are reorganized into the following semantic groups, separated by the existing divider treatment:

- **History and navigation:** Undo, Redo, thumbnail-panel toggle, Previous slide, Next slide.
- **Slides:** New slide, Duplicate slide, Delete slide, Layout.
- **Insert:** Text box, Image, Shape.
- **Text formatting:** Font size, Bold, Italic, Alignment, Bullets, Text color.
- **Object style:** Fill color, Border/stroke color.
- **View and presentation:** Zoom, Present.

This design does not introduce arrange, animation, transition, theme, font-family or other new editing commands. Existing table/P2 controls retain their current behavior and should not be pulled into this change unless a test proves that their insertion order is broken by the regrouping.

## Semantic color controls

`ppt-p1-tools.js` continues to use the native `<input type="color">` as the value source and interaction mechanism. The surrounding control becomes an icon-button-like labeled control with:

- a semantic inline SVG, authored for InkDOS and marked `aria-hidden="true"`;
- an explicit current-color swatch/bar whose visual value is synchronized to the input value;
- the existing `title` and `aria-label` (`Text color`, `Fill color`, `Border color`);
- the existing input IDs `pptP1TextColor`, `pptP1Fill`, and `pptP1Border` so no command/controller API changes are needed.

Icons communicate meaning rather than merely displaying color:

- **Text color:** letter A with an underline/current-color bar.
- **Fill color:** simple paint-bucket/fill symbol with a current-color bar.
- **Border color:** outlined shape/stroke symbol with a current-color bar.

The current-color indicator is presentation state, not decoration: it updates when the native color input changes and when `sync()` reflects a selected object's applicable color. Disabled/read-only controls retain the existing disabled semantics.

## Dynamic group integration

The existing `pptP1Tools` construction remains responsible for Image, Shape, Bullets, Layout and the three color inputs. It should attach each control to the appropriate semantic group rather than exposing one implementation-facing `Object editing` block. The base markup may provide stable group hosts in `index.html`; dynamic code fills those hosts while preserving all existing control IDs and event handlers.

If a semantic host is unavailable for any reason, initialization should fail safely without duplicating controls. Repeated install/build calls must remain idempotent.

## Responsive and accessibility requirements

- Do not remove the toolbar's horizontal scroll behavior.
- Interactive controls must keep the repository's existing touch-target conventions; icon controls remain at least the existing tool-button target size.
- Groups use `role="group"` and descriptive `aria-label` values matching the semantic organization above.
- SVGs are decorative inside already-labeled controls and use `aria-hidden="true"`.
- Native color inputs remain keyboard/focus capable; styling must not make them unreachable.
- Light/dark mode must use existing tokens/currentColor where possible and avoid hard-coded theme-specific chrome.
- Legacy `.ppt` read-only sessions must not gain enabled editing controls.

## Files expected to change

- `apps/presentations/index.html` — stable semantic toolbar group hosts and ordering.
- `apps/presentations/ui/ppt-p1-tools.js` — dynamic insertion into semantic hosts and semantic color-control DOM/current-color synchronization.
- `apps/presentations/ui/editor.css` — toolbar group/color-icon/current-swatch presentation.
- Focused Presentations contract/browser tests only as needed.

No presentation writer/parser/model files belong to this subproject.

## Verification contract

A focused regression must be written before production edits and must fail on the current toolbar. It should verify at minimum:

1. semantic group hosts exist with stable accessible labels;
2. the dynamic P1 controls are assigned to Slides/Insert/Text formatting/Object style rather than one monolithic implementation group;
3. text/fill/border controls contain semantic SVG icon structure and a current-color indicator, with no `●`/`○` raw-glyph affordance;
4. existing command/input IDs remain present exactly once;
5. read-only enable/disable logic is still wired through `sync()`;
6. repeated initialization does not duplicate controls.

After GREEN on the focused contract, run Presentations app-local tests, format-preservation tests where the shared Stage-B candidate includes format fixes, and Chromium/Firefox/WebKit stability + feature gates. Repository/integrity metadata must be current on the exact candidate head before integration. `preview` moves only to a launchable, basically sane verified candidate.

## Privacy and non-goals

Use only synthetic/private-safe fixtures. Do not commit screenshots, user filenames, user document content, credentials or telemetry. This subproject does not attempt to reproduce proprietary Office UI, and it does not resolve the separate real-device legacy-PPT clipping finding.