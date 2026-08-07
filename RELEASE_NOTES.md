# InkDesk v0.20.2.17 — Documents Ruler Interaction Decomposition

The Documents ruler pointer-drag lifecycle now lives in `shared/ui/document-ruler-drag-controller.js`; `shared/ui/workspace-layout.js` retains ruler DOM synchronization/rendering and observer wiring, while `shared/ui/document-ruler-model.js` continues to own pure geometry and indent-state calculations. No visible or file-format behavior is intentionally changed. See `RELEASE_NOTES_0.20.2.17.md`.
