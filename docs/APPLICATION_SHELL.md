# InkDesk application shell

Development sequence `0.19.4.3` establishes a shared interface foundation
for Documents, Spreadsheets, Presentations, and PDF without rewriting their
internal editors.

## Loading model

Every existing workspace already loads `shared/office-shell.js`. That file
is now a compatibility bootstrap which:

1. loads the central design tokens;
2. loads the shared component stylesheet;
3. loads `shared/ui/application-shell.js`;
4. exposes the readiness promise as `window.InkDeskUIReady`;
5. preserves the existing `office-product-ready` behavior.

All URLs are resolved from the bootstrap script itself, so the same
mechanism works on static hosting and during direct `file://` opening.

## Runtime API

After initialization:

```text
window.InkDeskUI
window.InkDeskUIReady
window.InkDeskShell
```

`InkDeskShell` contains:

- `moduleId`;
- detected interface `regions`;
- the `panels` controller;
- the `commands` registry;
- `announce(message)`;
- `setStatus(message)`;
- `setFileState(state)`.

The API does not replace program-specific logic. It supplies a stable
contract so later packages can move controls and change default panel
states without duplicating infrastructure in every workspace.

## Shared regions

The current DOM is annotated rather than restructured. Elements receive
`data-inkdesk-shell-region` values for:

- title bar;
- command categories;
- command bars;
- primary workspace;
- status bar.

This avoids changing IDs or moving elements in the first shell milestone.

## Panels

Existing sidebars are discovered and registered with a stable ID and side.

```text
InkDeskShell.panels.isOpen(id)
InkDeskShell.panels.setOpen(id, true or false)
InkDeskShell.panels.toggle(id)
InkDeskShell.panels.list()
```

Closing a registered panel applies the shared
`inkdesk-panel-collapsed` class. This capability is installed now, but
default states are deliberately unchanged until `0.19.4.4`.

## Commands

Modules may register commands without placing implementation details in the
application shell:

```javascript
InkDeskShell.commands.register(
  "documents.open",
  () => document.getElementById("fileInput").click(),
  { label: "Open document" }
);
```

This prepares future TXT and EPUB modules to use the same command surface.

## Visual scope

This package centralizes dimensions, spacing, surfaces, focus colors,
module accents, panel behavior, touch targets, and reduced-motion rules.
It does not yet perform the final office-workspace rearrangement. That
controlled migration belongs to `0.19.4.4`.

InkDesk retains its own identity and local assets.
