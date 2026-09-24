# InkDOS 2.5.2

> **Current stable release:** InkDOS 2.5.2. The immutable product baseline is tag `v2.5.2`, with signed desktop packages for Windows, macOS and Linux and a signed updater manifest for installed desktop editions.

InkDOS is a lightweight, local-first productivity suite with six focused applications: **Documents, Spreadsheets, Presentations, Plain Text, EPUB and PDF**. The browser/PWA edition and Tauri desktop editions use the same application source. There is no application backend and no telemetry service.

## Open the web edition

- **InkDOS Home:** https://vfydr2m9wk-ops.github.io/InkDOS/
- **Documents:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/documents/
- **Spreadsheets:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/spreadsheets/
- **Presentations:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/presentations/
- **Plain Text:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/txt/
- **EPUB:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/epub/
- **PDF:** https://vfydr2m9wk-ops.github.io/InkDOS/apps/pdf/

Each workspace can be opened directly. Home is a convenient suite entry point, not a prerequisite for using a workspace.

## Current release

InkDOS 2.5.2 is the stable fallback point. Windows users can install or update with the signed NSIS installer (`InkDOS_2.5.2_x64-setup.exe`). macOS uses DMG and Linux uses AppImage. The desktop updater consumes the release `latest.json` manifest and matching signatures from GitHub Releases.

Release page: https://github.com/vfydr2m9wk-ops/InkDOS/releases/tag/v2.5.2

Stable releases are tied to immutable `vX.Y.Z` tags so source, installers, signatures and updater metadata remain attributable to one versioned commit. See `docs/QA-BASELINE-2.5.2.md` for the compact validation record retained for the current baseline.

## Workspaces

| Workspace | Primary format | Additional behavior |
| --- | --- | --- |
| Documents | DOCX | Imports RTF and legacy DOC into the editable DOCX path. |
| Spreadsheets | XLSX | Imports legacy XLS; supports local CSV/TSV workflows. |
| Presentations | PPTX | Imports legacy PPT into an editable PPTX copy. |
| Plain Text | TXT | Local plain-text creation, editing and export. |
| EPUB | EPUB | Local reading, navigation, themes and annotations. |
| PDF | PDF | Local reading, annotations, page tools and export. |

Support is intentionally narrower than Microsoft Office, LibreOffice or Acrobat. Accepting an extension does not imply exhaustive preservation of every construct in that format.

## Architecture

The runtime is intentionally explicit:

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest` provide the Home/PWA shell.
- `apps/<workspace>/` contains each workspace's functional code, state, I/O, UI and local vendor dependencies.
- `shared/` contains the currently approved shared presentation-layer localization and interface-density helpers.
- `desktop/` contains the Tauri host, native packaging, signing and updater support.
- `VERSION.json` is the authoritative product-version source.

The project is maintained with a **preservation-first** policy: prefer the smallest correct change, avoid opportunistic refactoring, keep component-local repairs local, and preserve working legacy implementation when it is deliberately frozen rather than deleting it for cosmetic cleanup. AI maintenance rules are recorded in `AGENTS.md`.

See `docs/ARCHITECTURE.md` for runtime boundaries and `docs/KNOWN_LIMITATIONS.md` for format/application limits.

## Validation

The maintained GitHub Actions surface is intentionally small:

- `.github/workflows/ci.yml` — integration, regression and behavioral-stability validation;
- `.github/workflows/audit-online.yml` — manual published-site visual/stateful audit;
- `.github/workflows/desktop-tauri.yml` — desktop metadata, staging and native-host contracts;
- `.github/workflows/release.yml` — tag-triggered signed native release publication.

The aggregate release gate is `scripts/run_release_validation.py`. Component-local development should use the smaller context/test/verify commands documented in `AGENTS.md`.

GitHub Actions history is treated as operational evidence, not as the source of product history. Stable product history is preserved by Git commits, immutable tags/releases, permanent regression tests and compact QA baselines.

## Resource efficiency

In some informal local tests, InkDOS showed substantially lower application-attributed RAM usage than conventional desktop applications when opening comparable PDF and DOCX workloads. These observations are not standardized benchmarks and may vary with operating system, runtime, document complexity and background-process accounting. They are included only as an indication of the potential resource benefit of the lightweight local-first design.

## Privacy

The current tree does not intentionally contain real user documents or private QA material. Do not commit real user files, screenshots, recordings, private filenames, medical information, educational records or other identifying source material. Use synthetic fixtures and minimal anonymized reproductions only.

`scripts/audit_source.py` rejects local/container paths and email-shaped values in source text, while `tests/test_repository_privacy_contract.py` rejects committed user-document/media/archive formats, private QA paths, credential-like material and public user-upload attachment URLs.

## Repository layout

```text
.github/
apps/
assets/
config/
desktop/
docs/
licenses/
scripts/
shared/
tests/
index.html
manifest.webmanifest
service-worker.js
VERSION.json
```

Further documentation:
- `docs/ARCHITECTURE.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/UPDATE_MODEL.md`
- `docs/QA-BASELINE-2.5.2.md`

InkDOS is distributed under the MIT License.
