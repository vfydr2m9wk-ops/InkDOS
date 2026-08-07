# InkDesk 0.20.2.7 — Update Flow Hardening

## Purpose

Harden the incremental-update and validation path before continuing the
Presentations runtime decomposition. This release intentionally avoids editor
UI, file-format, save and recovery behavior changes.

## Changes

- Dry-run now builds a disposable candidate repository, applies the update there
  and runs the declared validation profile before reporting success. The source
  checkout is never modified by dry-run.
- Dry-run failure reports distinguish an untouched source checkout from a real
  transaction rollback.
- Updater reports now include the package SHA-256 so the tested artifact can be
  matched to the delivered package.
- Added `scripts/update_checksums_incrementally.py`, which preserves every
  undeclared checksum entry and changes only explicitly named files/deletions.
- Split slideshow/presentation-mode browser behavior into
  `revalidate_presentations_slideshow.py`, a fresh browser process/context that
  establishes its own Home/View/Present state.
- The Chromium release gate now runs thirteen independent browser scripts.
- Added permanent tests for candidate dry-run behavior, dry-run failure safety,
  incremental checksum preservation and slideshow-harness isolation.

## Preserved

- All current Documents, Spreadsheets, Presentations, PDF, TXT and EPUB runtime
  behavior.
- Existing Presentations Inspector, thumbnails, presenter notes,
  selection/history and slideshow controllers.
- The stable GitHub Actions workflow. The update ZIP contains no workflow file.
- Local-first/offline architecture and package-preserving Office export policy.

## Next bounded step

Presentations I/O/save/recovery decomposition, after this update-flow hardening
passes the hosted release gate.
