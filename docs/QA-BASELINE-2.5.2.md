# InkDOS 2.5.2 QA baseline

This file preserves the compact technical rationale for the stable 2.5.2 baseline so repository maintenance does not depend on retaining hundreds of historical GitHub Actions runs.

## Immutable product baseline

- Release: `v2.5.2`
- Product commit: `3470607f440d34b361aff4a790acec442d84fb56`
- Published: 2026-09-24
- The tag/release is the immutable fallback point. Later process/QA commits on `main` do not redefine this product baseline.

## Evidence retained

Before publication, the candidate passed:

- clean-snapshot release validation;
- application isolation, security/CSP, file-format and desktop contracts;
- Chromium/WebKit published-site visual matrix across Home + six workspaces, the 16:9 / 4:3 / 9:16 / 21:9 viewport set, light/dark/system appearance and auto/desktop/mobile density modes;
- final Chromium initial-control click sweep with zero click exceptions;
- stateful active-content control audit with zero JavaScript errors and zero surface failures after the Presentations and PDF hitbox repairs;
- cross-suite behavioral stability/soak validation;
- Tauri desktop validation;
- GitHub Pages deployment validation;
- signed Windows, macOS and Linux release builds;
- transactional GitHub Release publication.

The successful 2.5.2 release run is intentionally retained in Actions history. Repeated intermediate CI attempts, superseded audit workflows, failed release attempts and redundant Pages/Tauri runs may be removed after this baseline is recorded.

## Preservation rule

Deleting an Actions run does not authorize deleting or rewriting the corresponding product code, regression test, tag, release or frozen-legacy implementation. Stable product history is preserved by Git commits/tags/releases and permanent regression tests, not by retaining every transient CI execution.
