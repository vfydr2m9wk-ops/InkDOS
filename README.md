# InkDOS 2.5.0 — Local Preview
> Development snapshot. This 2.5.0 package is a local preview and is not a published GitHub release. GitHub publication remains frozen until explicit authorization.

InkDOS is a local-first productivity suite with six workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB and PDF. The browser/PWA edition and the Tauri desktop editions use the same application source. InkDOS has no application backend or telemetry service.

## Resource efficiency

In some informal local tests, InkDOS showed substantially lower application-attributed RAM usage than conventional desktop applications when opening comparable PDF and DOCX workloads. These observations are not standardized benchmarks and may vary depending on the operating system, runtime, document complexity and how background processes are accounted for. They nevertheless suggest that InkDOS's lightweight, local-first architecture has the potential to reduce memory overhead for common document workflows.

## Runtime

The application runtime is intentionally small and explicit:

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest` provide the optional Home/PWA shell.
- `apps/<workspace>/` contains each workspace's functional code, state, I/O, UI and local vendor dependencies.
- `shared/` is limited to the approved presentation-layer localization and interface-density helpers.
- `desktop/` contains the Tauri host, native packaging, signing and updater support.

`VERSION.json` is the authoritative product version for the web and desktop editions.

## Desktop builds and updates

Windows, macOS and Linux packages are built with Tauri v2. The supported installer set is NSIS/EXE for Windows, DMG for macOS and AppImage for Linux. The signed desktop updater uses GitHub Releases and the generated `latest.json` manifest. Update checking is explicit in the installed desktop application; installation remains a separate user action.

The GitHub Actions surface is intentionally limited to:

- `.github/workflows/desktop-tauri.yml` — desktop metadata, staging and contract validation only.
- `.github/workflows/release.yml` — the single tag-triggered path for release validation, signed native builds, updater manifest generation and release publication.

A release build starts only when an immutable tag matching `vX.Y.Z` is pushed. There is no separate promotion workflow or manual artifact-reuse publication path.

See `docs/UPDATE_MODEL.md` for the current updater path.

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

## Maintenance and regression checks

Maintenance validation lives in `scripts/` and `tests/`. The release validation entry point is `scripts/run_release_validation.py`; it checks runtime structure, app isolation, key format contracts, desktop release plumbing and repository privacy.

The current tree does not intentionally contain real user documents or private QA material. `scripts/audit_source.py` rejects local/container paths and email-shaped values in source text, while `tests/test_repository_privacy_contract.py` rejects committed user-document/media/archive formats, private QA paths, credential-like material and public user-upload attachment URLs.

## Privacy

Do not commit real user files, screenshots, recordings, private filenames, medical information, educational records or other identifying source material. Use synthetic fixtures and minimal anonymized reproductions only. The repository `.gitignore`, `SECURITY.md` and bug-report template reinforce this rule.

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

See `docs/ARCHITECTURE.md`, `docs/KNOWN_LIMITATIONS.md` and `docs/UPDATE_MODEL.md`.
