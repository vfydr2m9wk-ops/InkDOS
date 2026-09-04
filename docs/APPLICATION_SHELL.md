# Application shell

`shared/office-shell.js` is the small composition entry used by the workspaces. It loads the shared UI runtime, layout controllers, document-session controller and the canonical shared styles.

The shell does not implement workspace editing logic. It exposes readiness through `InkDOSUIReady` and `InkDOSDocumentSessionReady` and leaves format-specific behavior inside each workspace.

Shared styles load in this order:

1. `design-tokens.css`
2. `components.css`
3. `workspace-layout.css`
4. `visual-foundation.css`
5. `visual.css`
6. `content.css`
7. `workspace.css`
8. `polish.css`

The four semantic late layers replace version-named correction files. Each stays below the architecture size ceiling; new visual work should modify the responsible semantic layer instead of adding another patch stylesheet.
