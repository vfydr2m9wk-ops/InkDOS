# InkDesk v0.20.2.25 — Local Recovery Source Continuity Hardening

This maintenance release hardens private IndexedDB recovery for users who continue editing after creating a saved copy.

## What changed

- Save-copy cleanup now removes stale recovery snapshots while retaining the active source package for the current editing session.
- Subsequent edits can therefore create recovery snapshots that still have the original OOXML package available during Restore.
- Recovery inspection removes orphaned source packages from previously clean sessions, preventing unbounded storage accumulation.
- The local-recovery browser regression now covers **save → continue editing → recovery → restore → re-export** and verifies that modern XLSX package features remain preserved.
- No UI, formula syntax, workbook editing command or file-format capability is intentionally changed.

## Stability rationale

Previously, `markClean()` deleted both snapshots and the source package immediately after a Save-copy request. If the same workbook was then edited again, a later recovery snapshot no longer had its OOXML source. A restore could therefore fall back to a blank package reconstruction and lose preservation-only parts such as charts, tables, drawings or media. v0.20.2.25 keeps that source available until the document is replaced/discarded, while cleaning it on the next recovery inspection when no snapshot references it.

## Validation target

The hosted release gate remains the authoritative full unit/checksum suite plus **17/17 Chromium regression scripts**.
