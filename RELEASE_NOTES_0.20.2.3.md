# InkDesk v0.20.2.3 — Presentations Inspector Decomposition

This patch starts the runtime decomposition protected by the v0.20.2.2
architecture guardrails. It intentionally changes code ownership, not product
behavior.

## Extracted component

`apps/presentations/ui/inspector-controller.js` now owns:

- the Format-panel open/closed state and `aria-expanded` synchronization;
- compact-width Escape closing;
- X/Y/width/height, opacity, fill and rotation controls;
- image crop controls and crop reset;
- the existing fill-color palette.

`apps/presentations/app.js` remains the orchestration entry point and supplies
the selected-object, dirty-state, render, relayout and history callbacks.

## Regression protection

- The new component is loaded before `app.js` and is included in the offline
  application shell.
- Browser harnesses that load scripts manually now load the Inspector component
  explicitly before the Presentations entry point.
- Static tests verify component ownership, DOM contracts, source limits and the
  reduced `app.js` architecture ratchet.
- Existing Presentations behavior tests remain the authority for open/hide/
  reopen, compact drawer state, formatting mutations and presenter controls.

No React migration, visual redesign, new command or file-format change is part
of this patch.
