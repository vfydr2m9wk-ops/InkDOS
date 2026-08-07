# InkDesk v0.20.2.15 — Shared Workspace Panel Decomposition

This behavior-neutral architecture patch moves shared workspace panel visibility, persistence and accessibility synchronization from `shared/ui/workspace-layout.js` into `shared/ui/workspace-panel-controller.js`.

## What moved

- Documents navigation-sidebar open/closed state and session persistence.
- Presentations thumbnail, Format-panel and presenter-notes visibility state.
- PDF navigation-sidebar open/closed state, accessibility attributes and resize hint.
- Spreadsheet formula-bar/status-layout semantic markers.

The Documents page ruler remains owned by `workspace-layout.js`; the extraction intentionally does not change ruler geometry, zoom, file behavior, visible controls or panel defaults.

## Architecture result

- `shared/ui/workspace-layout.js`: reduced from 1,270 to 1,009 physical lines.
- `shared/ui/workspace-panel-controller.js`: 327 physical lines, below the normal 500-line ceiling.
- `shared/office-shell.js`: remains below the normal 500-line ceiling and now composes the panel controller before the workspace layout runtime.

## Validation contract

The existing full unit/package gate plus all 17 Chromium regression scripts remain authoritative. The new modularization tests additionally lock controller ownership, bootstrap ordering, offline precache and the tightened architecture ratchet.
