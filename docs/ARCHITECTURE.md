# InkDOS architecture

InkDOS is a local-first suite composed of six workspaces: Documents, Spreadsheets, Presentations, Plain Text, EPUB and PDF. Home is an optional launcher and navigation bridge; it is not an editor engine or file router.

## Workspace ownership

Each workspace owns its functional stack under `apps/<workspace>/`: model/engine code, state, I/O, UI, view code and any vendor libraries it requires. Runtime references from one workspace into a sibling workspace are forbidden.

Deliberate duplication is acceptable when it preserves workspace isolation. Functional document engines do not belong in a repository-level shared runtime.

## Approved shared presentation layer

`shared/` is restricted by `config/shared-runtime-policy.json`. It contains only the approved localization and interface-density presentation helpers. IDs, command names, parsers, spreadsheet formulas, serialization keys and user content remain app-owned.

`scripts/shared_runtime_policy.py`, `scripts/check_no_legacy_runtime.py`, `scripts/validate_app_isolation.py` and `scripts/validate_suite_contracts.py` enforce this boundary.

## Local-first behavior

Supported open, edit, conversion and save/export paths execute locally. There is no application backend or telemetry service. The root service worker provides the HTTP(S) offline shell; direct `file://` behavior remains subject to the host browser.

## Desktop host

`desktop/` is a thin Tauri v2 host around the web runtime. It adds native file dialogs/filesystem access, native windows, platform packaging and the signed Tauri updater while preserving browser/PWA fallbacks.

`VERSION.json` is the version authority. `desktop/scripts/release_version.py` verifies the Tauri configuration against it.

## Maintenance gates

`scripts/run_release_validation.py` is the non-publishing release-validation entry point used by the release workflow. It executes focused structural and format contracts, app-isolation checks, privacy checks and desktop release-pipeline checks.

The repository no longer uses historical phase/freeze ledgers, source-lock snapshots, repository update ZIPs or generated whole-tree checksum ledgers as active maintenance control planes. Git history, focused regression tests, release provenance and signed updater artifacts are the maintained trust boundaries.

## Privacy boundary

Real user documents and private QA material must not be committed. `scripts/audit_source.py` and `tests/test_repository_privacy_contract.py` enforce source/privacy rules. Public bug reports must use synthetic material.
