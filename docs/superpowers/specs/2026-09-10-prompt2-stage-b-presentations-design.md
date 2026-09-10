# Prompt 2 Stage B — Presentations Fidelity and Toolbar Design

## Scope

Stage B addresses only the Presentations workspace on the verified Prompt-2 trail. The immutable regression reference remains InkDOS 2.0.12 at `1986ae0fd81c94fa8202c10d9dea6fcd11d807af`; live `main` may advance only after evidence-backed verification.

Included work:

1. Legacy `.ppt` read-only text clipping: reproduce with privacy-safe synthetic content, trace importer → normalized model → renderer, and patch only a confirmed root cause.
2. Thumbnail fidelity: thumbnails must preserve each slide's own aspect ratio and map object geometry into the actual rendered thumbnail viewport without crop caused by a hard-coded internal width.
3. Legacy `.ppt` → editable `.pptx` fidelity: trace slide size, object geometry, text metrics, wrapping, margins, images and shapes through importer → model → PPTX writer. Patch only individually reproduced divergences.
4. Presentations toolbar quality: retain current commands and keyboard semantics while regrouping controls by File/History, Slides, Insert, Text/Object formatting and View/Present. Replace raw/prototype-like color affordances with semantic fill/text/line controls and accessible labels; use original InkDOS iconography only.

## Non-goals

No Office-parity expansion, new animation/transition engine, broad presentation-model rewrite, unrelated refactor, release/version change, or private user fixture. Real iPad/WKWebView/XeOS-only symptoms that cannot be reproduced synthetically remain `NEEDS REAL DEVICE CONFIRMATION`.

## Design boundaries

### Rendering and thumbnails

The full slide renderer remains authoritative for object geometry. Thumbnail rendering must derive its scale from the thumbnail paper's actual rendered dimensions (or from a single explicit logical thumbnail viewport that is guaranteed to match the CSS viewport) rather than an unrelated hard-coded pixel width. The paper keeps `aspect-ratio = slide.widthEmu / slide.heightEmu`.

Text containers must not be globally changed to visible overflow merely to hide clipping. Any clipping fix must preserve slide bounds and arise from corrected text metrics, line spacing, margins, wrapping or box geometry proven by a regression.

### Legacy conversion

The conversion path remains local-first and synthetic-testable. Geometry values must retain the same slide-relative ratios across source import and generated PPTX. Text fidelity checks compare normalized object bounds, font size, line spacing, margins, wrapping and paragraph/run properties before and after conversion where the format exposes them.

### Toolbar

Toolbar work is a presentation-only UI reorganization over existing semantic commands. Command IDs remain the behavior boundary; visual controls must invoke the registry rather than duplicate business logic. Color controls expose semantic accessible names and current-color state. The toolbar must remain usable at iPad landscape widths and degrade through wrapping/overflow without hiding core Save/Open/Present actions.

## Verification

Each confirmed defect gets a distinct `INKBUG-*` allocation from the canonical audit state and a focused failing regression before production code where practical. Minimum verification for a production candidate:

- affected Presentations regression(s);
- Presentations command/control contract;
- format-preservation round-trip gates relevant to PPT/PPTX;
- Chromium, Firefox and WebKit feature/stability coverage when CI supports it;
- repository/integrity gates;
- exact reproduction re-check after the fix;
- no promotion of `preview` until the branch is launchable and basically sane.

Automation/browser-emulation evidence must be labeled separately from physical iPad/WKWebView/XeOS confirmation.
