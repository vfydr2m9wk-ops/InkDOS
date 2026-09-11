# InkDOS 2.1.0

InkDOS is a local-first, static browser productivity suite with six physically independent workspaces behind an optional Home launcher. It runs entirely client-side, requires no application backend or telemetry service, and keeps document processing in the browser.

Version 2.1.0 is the post-hardening release that consolidates the stability work performed after the 2.0.12 structural baseline. The current development focus is real-device acceptance: automated repository, format-preservation and browser regressions are part of the release gate, while host-specific behavior on iPad/XeOS still requires direct user confirmation where synthetic browsers cannot prove the full file-delivery or WebKit-host interaction path.

## Workspaces and format behavior

| Workspace | Primary editable format | Additional input / behavior |
| --- | --- | --- |
| Documents | DOCX | RTF imports into the editable document model. Legacy DOC opens through the local import-only reader and can be promoted by saving an editable DOCX copy; InkDOS does not write back to DOC. |
| Spreadsheets | XLSX | Legacy XLS workbooks can be imported locally and saved as editable XLSX copies. |
| Presentations | PPTX | Legacy PPT presentations can be imported locally and promoted to editable PPTX copies; PPT write-back is not provided. |
| Plain Text | TXT | Local plain-text creation, editing and export. |
| EPUB Reader | EPUB | Local reading, navigation, themes and annotations, with compatibility fallbacks for supported ZIP/EPUB structures. |
| PDF Workspace | PDF | Local reading, annotations, page tools and PDF export; it is not a general-purpose existing-PDF text editor. |

Format support is intentionally narrower than Microsoft Office or LibreOffice. A file extension being accepted does not imply exhaustive preservation of every feature defined by that format.

## Architecture and optional Home

Each workspace retains app-local runtime, state, I/O, UI and view responsibilities under `apps/<workspace>/`. There is no shared mutable office-document engine and no workspace is permitted to load another workspace's source tree as an application dependency.

Home is an optional suite bridge. It launches workspaces with `suite=1`; each app-local frame exposes the Home action only in that suite context. A workspace opened directly or extracted independently does not require the Home launcher to operate.

Release validation checks standalone app isolation, cross-app reference boundaries and the root offline shell.

## Save, Share and unsaved-work semantics

Save and Share are separate operations. Share sends the current export through the host Share Sheet when supported; it does not by itself prove persistent storage.

File-delivery code uses a single-flight / single-delivery contract to prevent overlapping Save actions from creating multiple host deliveries. Destructive Open/Home/leave flows use Save / Discard / Cancel guards. A Save path must reach the workspace's confirmed-delivery condition before the app clears dirty state or authorizes destructive navigation; failed, cancelled, stale or unconfirmed delivery keeps the work protected.

Those contracts are regression-tested, but exact host behavior can differ on iPad/iPhone-style WebKit containers. Real-device confirmation therefore remains authoritative for issues such as duplicate host downloads, Share Sheet behavior and host-specific file-picker fallbacks.

## Browser and device validation

The automated release gate covers repository contracts, deterministic assets, format-preservation round trips and browser regressions in Chromium, Firefox and WebKit. Passing that matrix means the tested browser paths are green; it is not a claim that every embedded WebKit host behaves identically to Playwright WebKit.

The current real-device acceptance cycle concentrates on iPad/XeOS behavior, especially file delivery, legacy PPT fidelity, EPUB compatibility and PDF host integration. Confirmed device findings are treated as higher-priority evidence when they differ from synthetic browser behavior.

## Appearance and offline behavior

Home supports Light, Dark and System appearance. Each workspace retains its own appearance controller while the installed suite can synchronize the selected mode through `inkdos2:appearance`.

The root service worker provides the validated application shell under HTTP(S). Direct `file://` execution remains subject to the host browser's local-file policy and does not provide the same PWA/service-worker guarantees.

## Release and control-state files

`VERSION.json`, `BUILD_INFO.json`, `SOURCE_MANIFEST.json` and `RELEASE_MANIFEST.json` describe the current 2.1.0 release identity.

`DEVELOPMENT_STATE.json` has a different purpose: it records the last transactional update-package sequence accepted by the updater. Its sequence/package label can therefore remain tied to an earlier package even when the public release identity has advanced through validated repository integration. Historical stability/freeze documents likewise retain the versions and commit anchors that were true when those records were produced.

## Repository layout

```text
index.html
assets/
apps/
  documents/
  spreadsheets/
  presentations/
  txt/
  epub/
  pdf/
docs/
scripts/
tests/
```

See `docs/ARCHITECTURE.md`, `docs/PROJECT_STATUS.md`, `docs/KNOWN_LIMITATIONS.md`, and `docs/UPDATE_MODEL.md` for the current architecture, status, limitations and update model.
