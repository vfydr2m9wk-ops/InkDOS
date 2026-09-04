# InkDOS v1.0.0-beta.2 — 1.0 Beta 2

This maintenance beta establishes the permanent InkDOS incremental-update
contract while preserving the feature-frozen application baseline.

## Update infrastructure

- The stable workflow is `.github/workflows/apply-inkdos-update.yml`.
- Root packages use `InkDOS-update-v*.zip`.
- Package manifests identify `product: InkDOS`.
- Update sequence 59 follows the successful permanent-updater bootstrap at sequence 58.
- Packages remain unable to create, modify or delete GitHub workflow files.
- The updater performs archive/path checks, SHA-256 payload verification,
  sequence/version guards, disposable-candidate validation and transactional
  application with rollback.
- `scripts/build_update_package.py` provides deterministic package creation for
  future incremental updates.

## Identity cleanup

- Package metadata now uses the `inkdos` package name.
- MIT attribution is updated to InkDOS contributors.
- The obsolete root `InkDesk.html` redirect is removed.

## Scope

No new editor feature is introduced by this maintenance release. DOCX,
XLS/XLSX, PPTX, PDF, TXT and EPUB support remains within the documented 1.0
beta compatibility envelope.

Current archived note: [`docs/releases/RELEASE_NOTES_1.0.0-beta.2.md`](docs/releases/RELEASE_NOTES_1.0.0-beta.2.md)

Full historical notes: [`docs/releases/`](docs/releases/)
