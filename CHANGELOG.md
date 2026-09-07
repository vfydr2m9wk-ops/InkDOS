# Changelog

## 2.0.7 — 2026-09-07

- Standardize the empty-workspace file-action contract across all six independent apps: Save and Share remain unavailable until a real document, workbook, presentation, text file, book or PDF is active.
- Make Presentations start with a true empty session (`sourceKind: none`, zero slides) instead of constructing a hidden blank presentation; New creates the first slide and Open activates the session only after a successful commit.
- Gate Presentations editing, slideshow, Save and Share commands on an active presentation while preserving legacy PPT read-only behavior.
- Make Plain Text start unloaded until New, a successful Open, or a valid local recovery checkpoint activates a document; Save and Share now follow the same loaded-state contract.
- Align Spreadsheets and PDF Save controls with their existing Share/controller active-state guards.
- Add a suite-level regression contract for empty-state Save/Share behavior without introducing any cross-app runtime dependency.
- Rotate the offline application cache so WebKit/XeOS receives the corrected state behavior.

## 2.0.6 — 2026-09-07

- Remove the production Plain Text global runtime-error banner so opaque host/WebKit `Script error.` events no longer surface as a false app failure.
- Normalize the existing Home bridge and first-open card integration back into the physical Plain Text template/styles source; the published behavior remains unchanged.
- Add a deterministic Plain Text bundle builder and a byte-for-byte release validation check so `apps/txt/index.html` must remain derivable from its modular template, styles and JavaScript sources.
- Preserve Plain Text editor/runtime modules, TXT file I/O, Share behavior and the other five workspace runtimes unchanged.
- Rotate the offline application cache so WebKit/XeOS receives the corrected Plain Text distribution.

## 2.0.5 — 2026-09-07

- Restore WebKit/PWA installation compatibility metadata removed during the 2.0 Home refactor.
- Restore `mobile-web-app-capable`, `apple-mobile-web-app-capable` and Apple standalone status-bar metadata on the Home entry point.
- Restore the manifest identity to `./index.html`, language/categories metadata and `any maskable` purpose for the primary PNG icon.
- Preserve all six workspace runtimes and the 2.0.4 Share implementation unchanged.
- Rotate the offline application cache so WebKit/XeOS receives the refreshed Home and manifest metadata.

## 2.0.4 — 2026-09-07

- Standardize an explicit Share action across all six workspaces; Plain Text and EPUB keep their existing behavior while Documents, Spreadsheets, Presentations and PDF gain matching app-local actions.
- Share exports the current DOCX, XLSX, PPTX or PDF state through the system Share Sheet when Web Share file delivery is available.
- Keep Share separate from Save/Save copy: sharing does not mark unsaved edits as persistently saved.
- Keep legacy PPT read-only, with both Save and Share disabled for that source type.
- Add a six-app Share contract to suite validation and refresh integrated source locks/checksums for the new app-local code.

## 2.0.3 — 2026-09-07

- Install the physically modular PDF P4.2 app; enable Home ↔ PDF navigation and EPUB-style Open PDF card.
- Preserve all five existing app source trees byte-for-byte.
- Exclude internal PDF inspection hooks, fixtures and sample documents.
- Update six-app release locks and offline cache; correct the existing stale Presentations icon cache URL.
- Retain all release contracts as validation tooling, with no internal tests directory in the update payload.

## 2.0.2 — 2026-09-07

- Fixed the Presentations first-open gate so the app no longer exposes the pre-created blank slide before the user chooses New or Open.
- Kept the presentation engine, parser, writer, state and editing controllers frozen; the correction is confined to the presentation entry index.
- Versioned the Home → Presentations route to force a fresh Safari/WebKit navigation after the update.

## 2.0.1 — 2026-09-07

- Standardized first-open cards to the Spreadsheets interaction pattern.
- Documents, Presentations and Plain Text now offer New/Open from the central card.
- EPUB uses the same card with one centered Open action.
- Spreadsheets remains the unchanged visual baseline; PDF remains Coming soon.


## 2.0.0 — 2026-09-07

- Clean-tree consolidation of the five frozen 2.0 apps.
- New Home workspace selector with 3×2 wide layout and single-column phone layout.
- Added one Home bridge to each app entry page; no other app runtime file changed.
- PDF runtime intentionally absent; Home shows a Coming soon placeholder.
- Removed dependency on the 1.x suite shell, recent-files runtime, module launcher and shared application runtime.
- Added clean 2.0 release metadata, integrity locks, service worker and transactional updater.
