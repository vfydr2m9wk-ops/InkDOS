# InkDesk v0.20.3.0 — Visual Foundation

Date: 2026-08-08

## Purpose

Move from structural hardening to visible UX work without reopening the stabilized document engines. v0.20.2.31 is the structural baseline; v0.20.3.0 adds a reversible shared visual layer.

## User-visible changes

- Reworked launcher hierarchy and workspace cards with consistent app identities.
- Unified titlebar, toolbar, focus, selected, pressed and disabled states.
- Unified start cards and primary/secondary actions across workspaces.
- Improved compact spacing and touch targets for narrow/coarse-pointer devices.
- Dark-mode tokens remain system-driven; no external fonts or network assets are introduced.

## Safety boundary

This package does not refactor parsers, writers, formula evaluation, recovery semantics, Undo/Redo, or export logic. Existing runtime modules receive only release-identity/cache-version updates where the validation contract requires synchronization.

## Validation target

- Full Python/unit/package suite passes on the hosted checkout.
- 18/18 Chromium regression scripts pass, including the new visual foundation contract.
- Checksum integrity passes against the hosted PDF.js vendor files.
- No workflow files are shipped in the update ZIP.
