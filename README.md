# InkDOS 2.5.2

> **Current stable release:** InkDOS 2.5.2. The immutable stable baseline is tag `v2.5.2`; signed desktop packages are published for Windows, macOS and Linux.

**Live web/PWA:** https://vfydr2m9wk-ops.github.io/InkDOS/  
**Latest release:** https://github.com/vfydr2m9wk-ops/InkDOS/releases/latest  
**Source:** https://github.com/vfydr2m9wk-ops/InkDOS

InkDOS is a local-first productivity suite with six workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB and PDF. The browser/PWA edition and the Tauri desktop editions use the same application source. InkDOS has no application backend or telemetry service.

## Direct web apps

Each workspace can be opened directly; Home is a launcher rather than a required runtime dependency.

| Workspace | Direct link | Primary formats |
| --- | --- | --- |
| Documents | https://vfydr2m9wk-ops.github.io/InkDOS/apps/documents/ | DOC / DOCX / RTF |
| Spreadsheets | https://vfydr2m9wk-ops.github.io/InkDOS/apps/spreadsheets/ | XLS / XLSX |
| Presentations | https://vfydr2m9wk-ops.github.io/InkDOS/apps/presentations/ | PPT / PPTX |
| Plain Text | https://vfydr2m9wk-ops.github.io/InkDOS/apps/txt/ | TXT |
| EPUB | https://vfydr2m9wk-ops.github.io/InkDOS/apps/epub/ | EPUB |
| PDF | https://vfydr2m9wk-ops.github.io/InkDOS/apps/pdf/ | PDF |

Support is intentionally narrower than Microsoft Office, LibreOffice or Acrobat. Accepting an extension does not imply exhaustive preservation of every construct in that format.

## Stable baseline

InkDOS 2.5.2 is the current stable release. Windows users can install or update with the signed NSIS installer. macOS uses the signed DMG/application bundle and Linux uses AppImage. The desktop updater consumes the release `latest.json` manifest and matching signatures from GitHub Releases.

The release tag is the stable product checkpoint. `main` may contain later documentation, CI or development-process improvements without rewriting the published 2.5.2 baseline.

See `docs/QA-BASELINE-2.5.2.md` for the final verification summary.

## Resource efficiency

In some informal local tests, InkDOS showed substantially lower application-attributed RAM usage than conventional desktop applications when opening comparable PDF and DOCX workloads. These observations are not standardized benchmarks and may vary depending on the operating system, runtime, document complexity and how background processes are accounted for. They nevertheless suggest that InkDOS's lightweight, local-first architecture has the potential to reduce memory overhead for common document workflows.

## Runtime

The application runtime is intentionally small and explicit:

- `index.html`, `assets/`, `service-worker.js` and `manifest.webmanifest` provide the optional Home/PWA shell.
- `apps/<workspace>/` contains each workspace's functional code, state, I/O, UI and local vendor dependencies.
- `shared/` is currently limited to approved presentation-layer localization and interface-density helpers.
- `desktop/` contains the Tauri host, native packaging, signing and updater support.

`VERSION.json` is the authoritative product version for web and desktop editions.

## Maintenance model

InkDOS is maintained with AI-assisted implementation and human audit. Repository rules intentionally favor:

- small, component-local changes;
- preservation of working code over cosmetic refactoring;
- no opportunistic rewrites during unrelated fixes;
- regression tests before integration;
- explicit protection for deliberately preserved frozen legacy;
- independent workspace ownership so a repair to one app does not require rewriting its siblings.

The current post-2.5.2 development direction is conservative isolation: reduce unnecessary cross-app state and dependencies while retaining proven APIs, names and legacy structures unless there is a concrete reason to change them.

See `AGENTS.md` for the operational maintenance rules and `config/components.json` for machine-readable component ownership.

## Desktop builds and updates

Windows, macOS and Linux packages are built with Tauri v2. The supported installer set is NSIS/EXE for Windows, DMG for macOS and AppImage for Linux. Update checking is explicit in the installed desktop application; installation remains a separate user action.

The permanent GitHub Actions surface is intentionally small:

- `.github/workflows/ci.yml` — integration and regression validation;
- `.github/workflows/audit-online.yml` — manual online visual/stateful auditing;
- `.github/workflows/desktop-tauri.yml` — desktop metadata and staging contracts;
- `.github/workflows/release.yml` — immutable tag-driven signed release publication.

Normal releases are built from immutable `vX.Y.Z` tags so source, installers, signatures and updater metadata remain tied to one versioned commit.

See `docs/UPDATE_MODEL.md` for the updater path.

## Maintenance and regression checks

The release-validation entry point is `scripts/run_release_validation.py`. Component-local AI work uses `scripts/agent_context.py`, `scripts/agent_test.py` and `scripts/agent_verify.py` so ordinary fixes do not need to rediscover or retest the whole repository unnecessarily.

The online visual matrix and active-control audit are preserved as manual tools instead of version-specific temporary workflows. The behavioral stability gate remains part of normal CI.

The current tree does not intentionally contain real user documents or private QA material. `scripts/audit_source.py` and `tests/test_repository_privacy_contract.py` enforce the repository privacy boundary.

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

See `docs/ARCHITECTURE.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/QA-BASELINE-2.5.2.md` and `docs/UPDATE_MODEL.md`.
