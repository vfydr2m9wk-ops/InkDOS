# InkDOS 2.4.0

InkDOS is a local-first productivity suite with six physically independent workspaces behind an optional Home launcher. The same client-side HTML/CSS/JavaScript application is distributed as a web/PWA edition and as installable Tauri desktop editions, with no application backend or telemetry service.

Version 2.4.0 promotes the completed 2.4 interface/localization work and the hardened CI/release pipeline to the stable line. It adds optional UI-only localization packages for Portuguese, Spanish, German, French, Simplified Chinese, Japanese and Russian; compact app-local Appearance / Interface / Language / Help settings; and first-open pointer/touch regression protection while preserving application logic, file-format semantics and local-first behavior. The release pipeline now validates the merge candidate before integration, separates read-only integrity validation from update-package application, performs signing preflight, records immutable build provenance and supports publish-only recovery from already validated artifacts.

## Desktop edition

The desktop edition uses Tauri v2 as a thin native host around the existing InkDOS workspaces. It uses native open/save dialogs and filesystem access where the desktop bridge is available, while preserving the browser/PWA fallback paths. Windows, macOS and Linux packaging are exercised by native CI runners, including package inspection, launchers, associations and multiwindow integration.

The desktop updater uses the signed Tauri updater path. It is hidden/inert in the web/PWA edition. On desktop, Check for updates is an explicit user action; when invoked, InkDOS compares the installed and latest versions and can present release notes. Installation remains a separate explicit action and can be cancelled. Signed metadata, artifacts and signatures are part of the updater trust boundary.

## Workspaces and format behavior

| Workspace | Primary editable format | Additional input / behavior |
| --- | --- | --- |
| Documents | DOCX | RTF imports into the editable document model. Legacy DOC opens through the local import-only reader and can be promoted by saving an editable DOCX copy; InkDOS does not write back to DOC. |
| Spreadsheets | XLSX | Legacy XLS workbooks can be imported locally and saved as editable XLSX copies. CSV/TSV delimited-text handling preserves the detected delimiter through the supported local workflow. |
| Presentations | PPTX | Legacy PPT presentations can be imported locally and promoted to editable PPTX copies; PPT write-back is not provided. |
| Plain Text | TXT | Local plain-text creation, editing and export. |
| EPUB Reader | EPUB | Local reading, navigation, themes and annotations, with compatibility fallbacks for supported ZIP/EPUB structures. |
| PDF Workspace | PDF | Local reading, annotations, page tools and PDF export; it is not a general-purpose existing-PDF text editor. |

Format support is intentionally narrower than Microsoft Office or LibreOffice. A file extension being accepted does not imply exhaustive preservation of every feature defined by that format.

## Architecture and optional Home

Each workspace retains app-local runtime, state, I/O, UI and view responsibilities under `apps/<workspace>/`. There is no shared mutable office-document engine and no workspace is permitted to load another workspace's source tree as an application dependency.

Home is an optional suite bridge. It launches workspaces with `suite=1`; each app-local frame exposes the Home action only in that suite context. A workspace opened directly or extracted independently does not require the Home launcher to operate.

Release validation checks standalone app isolation, cross-app reference boundaries and the root offline shell. InkDOS 2.4 keeps suite-wide adaptive interface density and localization as approved presentation-layer shared runtime while preserving the physical independence of the six workspaces.

## Localization and compact settings

English remains the native source interface. Optional locale packages change only visible labels and presentation/accessibility attributes (`title`, `aria-label`, `placeholder`) and fall back to the original English text when a translation is unavailable. Localization does not mutate IDs, command names, parser tokens, spreadsheet formulas, serialization keys, keyboard-command logic, document state or user content.

Each workspace exposes a compact app-local settings strip in the order Appearance / Interface / Language / Help. Language and density preferences remain workspace-local; appearance keeps the existing suite preference behavior.

## Save, Share and unsaved-work semantics

Save and Share are separate operations. Share sends the current export through the host Share Sheet when supported; it does not by itself prove persistent storage.

File-delivery code uses a single-flight / single-delivery contract to prevent overlapping Save actions from creating multiple host deliveries. Destructive Open/Home/leave flows use Save / Discard / Cancel guards. A Save path must reach the workspace's confirmed-delivery condition before the app clears dirty state or authorizes destructive navigation; failed, cancelled, stale or unconfirmed delivery keeps the work protected.

Those contracts are regression-tested, but exact host behavior can differ on iPad/iPhone-style WebKit containers. Real-device confirmation therefore remains authoritative for issues such as duplicate host downloads, Share Sheet behavior and host-specific file-picker fallbacks.

## Browser and device validation

The automated release gate covers repository contracts, deterministic assets, format-preservation round trips and browser regressions in Chromium, Firefox and WebKit. Passing that matrix means the tested browser paths are green; it is not a claim that every embedded WebKit host behaves identically to Playwright WebKit.

Real-device acceptance remains distinct from automated validation. Host-specific findings on iPad/XeOS and installed desktop packages are treated as higher-priority evidence when they differ from synthetic browser behavior. The signed installed updater end-to-end path is likewise a final release validation step rather than a repository-only claim.

## Appearance and offline behavior

Home supports Light, Dark and System appearance. Each workspace retains its own appearance controller while the installed suite can synchronize the selected mode through `inkdos2:appearance`.

The root service worker provides the validated application shell under HTTP(S). Direct `file://` execution remains subject to the host browser's local-file policy and does not provide the same PWA/service-worker guarantees.

## Release and control-state files

`VERSION.json`, `BUILD_INFO.json`, `SOURCE_MANIFEST.json` and `RELEASE_MANIFEST.json` describe the current 2.4.0 release identity after the integrity metadata refresh is completed.

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
desktop/
docs/
scripts/
tests/
```

See `docs/ARCHITECTURE.md`, `docs/PROJECT_STATUS.md`, `docs/KNOWN_LIMITATIONS.md`, and `docs/UPDATE_MODEL.md` for the current architecture, status, limitations and update model.
