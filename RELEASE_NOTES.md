# InkDesk v0.20.2.18 — Shared Workspace Contract Consolidation

Workspace module detection, persisted panel-preference resolution and the workspace-layout-ready notification now live with the existing `shared/ui/workspace-panel-controller.js`. `shared/ui/workspace-layout.js` keeps Documents ruler DOM synchronization and remains API-compatible while dropping below the normal 500-line ceiling. No visible or file-format behavior is intentionally changed. See `RELEASE_NOTES_0.20.2.18.md`.
