# InkDesk v0.20.2.18 — Shared Workspace Contract Consolidation

## Scope

- Consolidates shared workspace module detection into `shared/ui/workspace-panel-controller.js`.
- Consolidates session-backed panel preference resolution and the workspace-layout-ready notification with the same controller.
- Keeps `InkDeskWorkspaceLayout.defaults`, `moduleId()` and `resolvedPreference()` as compatibility delegates.
- Keeps Documents ruler DOM synchronization, rendering, observers, pure geometry and drag behavior unchanged.

## Architecture result

`shared/ui/workspace-layout.js` falls from 541 to 492 physical lines and leaves `grandfatheredDebt`; `shared/ui/workspace-panel-controller.js` remains below the normal 500-line ceiling. No new runtime file or workflow file is introduced.

## Behavior contract

No visible UI, panel default, ruler interaction, file open/save path, recovery behavior or file-format behavior is intentionally changed.
