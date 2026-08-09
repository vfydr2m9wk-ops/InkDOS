# InkDesk v1.0.0-beta.1 — 1.0 Beta 1

This release consolidates the validated 0.20.x engineering train into the first
feature-frozen beta on the 1.0 line. The goal is not feature parity with
Microsoft Office; it is a stable, explicit contract for InkDesk's supported
local-first workflows.

## What is consolidated

- Documents: focused DOCX editing, pagination, images, headers/footers, ruler, recovery and package-preserving copy export within the supported subset.
- Spreadsheets: XLS BIFF8 import, XLSX editing/export, multiple worksheets, safe worksheet add/delete, supported formulas, recovery and error propagation.
- Presentations: focused PPTX editing, backgrounds, thumbnails, notes, slideshow and preservation-aware export.
- PDF: local viewing, navigation, review/annotations and unified save behavior within the supported subset.
- Plain Text and EPUB: focused local editing/reading workspaces.
- Shared shell: local-first lifecycle, recovery isolation, offline app shell, responsive landscape-first workspace geometry and regression guardrails.

## Deliberate simplification

The Launcher no longer exposes **Open a supported file**. That generic handoff
duplicated the explicit Open controls in each workspace and created additional
routing, temporary-storage and browser-state paths for little practical gain.
Choose a workspace first, then open the file there.

No editor feature replaces the removed Launcher handoff.

## Versioning cleanup

The numerous 0.20.2.x and 0.20.3.x identifiers remain as development history.
They are not promoted into a matching set of GitHub Releases. Public releases
now use semantic prerelease versions (`1.0.0-beta.1`, later beta/RC builds),
while the monotonically increasing internal sequence remains an update-order
guard only.

## Release packaging integrity

- Public SBOM and release identity are synchronized from `VERSION.json`.
- Generated `tests/browser/results/` artifacts are never included in release ZIPs.
- Release archives remain deterministic when built repeatedly from the same clean tree.

## Release gate

Before publication, the repository must pass checksum verification, repository
validation, source audit, architecture guardrails, the complete unit/package
suite and Chromium regression suite. Firefox/WebKit matrix and native iPadOS
remain additional evidence rather than inferred from Chromium.

## Known limits

Office compatibility remains intentionally partial. Advanced Office features,
exact typography/layout fidelity, encrypted files and unsupported legacy formats
remain outside the beta contract. See [`COMPATIBILITY.md`](COMPATIBILITY.md) and
[`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).

Current archived note: [`docs/releases/RELEASE_NOTES_1.0.0-beta.1.md`](docs/releases/RELEASE_NOTES_1.0.0-beta.1.md)

Full historical notes: [`docs/releases/`](docs/releases/)
