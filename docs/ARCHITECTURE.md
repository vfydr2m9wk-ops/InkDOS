# InkDOS architecture

InkDOS is a static browser application: source files are served directly with no mandatory runtime build step.

## Entry points

`index.html` is the suite hub. The six workspaces live under `apps/documents`, `apps/spreadsheets`, `apps/presentations`, `apps/pdf`, `apps/txt` and `apps/epub`. Root format launchers remain small direct compatibility entry points where they still provide user value.

## Shared runtime

- `shared/office-runtime.js`: safe file/package primitives and download lifecycle.
- `shared/file-router.js`: suite-to-workspace file routing.
- `shared/local-recovery.js`: private IndexedDB recovery for editable Office workspaces.
- `shared/office-shell.js`: lightweight composition/bootstrap for shared UI modules.
- `shared/ui/`: reusable shell, layout, session and visual components.
- `modules/`: declarative workspace registry and loader.

## UI layering

The active shared cascade uses design tokens, components, workspace layout, the base visual foundation and four bounded semantic late layers: `visual.css`, `content.css`, `workspace.css` and `polish.css`. Version-named corrective overlays are not part of the current architecture.

## Boundaries

Parsers/writers own format semantics. Workspace controllers own user interaction. Shared modules must not silently take ownership of format-specific data. Imported content is untrusted and network access is not required for core editing/reading.

## Engineering rule

Architecture is allowed to change when a smaller implementation preserves or improves the tested product contract. Git stores superseded designs; the runtime does not.
