# InkDesk v0.20.2.19 — TXT Editor Interaction Decomposition

## Scope

- Extracts TXT Undo/Redo snapshot-history ownership to `apps/txt/history-controller.js`.
- Extracts TXT Find bar/search interaction to `apps/txt/find-controller.js`.
- Keeps file open/save, UTF-8/UTF-16 decoding, line-ending preservation, title/dirty lifecycle, counts, wrap and text-size controls in `apps/txt/app.js`.

## Architecture result

`apps/txt/app.js` falls from 591 to 457 physical lines and leaves `grandfatheredDebt`. Both new controllers remain well below the normal 500-line ceiling. The new scripts load deterministically before `app.js` and are included in the offline shell cache.

## Behavior contract

No visible UI, TXT encoding, line-ending, Save, dirty-state, Undo/Redo, Find, keyboard-shortcut or workflow behavior is intentionally changed.
