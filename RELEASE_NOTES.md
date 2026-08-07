# InkDesk v0.20.2.14 — Shared Document Session Decomposition

The existing cross-workspace document-session adapter now lives in `shared/ui/document-session-controller.js`. Filename normalization, dirty-state bridging, discard protection and download-name rewriting are unchanged; `shared/office-shell.js` is reduced to bootstrap/composition and no longer needs an inherited architecture-debt exemption. See `RELEASE_NOTES_0.20.2.14.md`.
