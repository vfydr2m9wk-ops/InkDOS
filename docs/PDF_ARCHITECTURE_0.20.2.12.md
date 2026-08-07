# PDF architecture delta — v0.20.2.12

The PDF workspace continues the behavior-neutral decomposition begun in v0.20.2.10.

## Runtime ownership

- `app.js`: document lifecycle, zoom/direction, unified Save, fullscreen and composition.
- `viewer/page-renderer.js`: page virtualization, canvas/text/AcroForm rendering and resize rerender.
- `viewer/navigation-controller.js`: page navigation, thumbnails, outline, bookmarks and sidebar tabs.
- `review/review-controller.js`: review persistence, text-selection review tools, comments, tool state and Undo.
- `review/annotation-layer.js`: visual annotation segments and free marker/text pointer placement.

## Ratchet

`apps/pdf/app.js` is reduced to the v0.20.2.12 baseline and may shrink further but must not grow beyond that baseline during the stabilization refactor. Both new review files are below the 500-line new-file ceiling and contain no physical lines over 240 characters.

## Next boundary

The remaining large PDF responsibility is unified Save / flattened annotated export coordination. That will be isolated separately so review behavior and save behavior are never refactored in the same package.
