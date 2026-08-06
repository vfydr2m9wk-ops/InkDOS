# Documents ruler asset-delivery hotfix

Package `0.19.4.7.1` fixes delivery of the page-aware ruler introduced in
`0.19.4.7`. It does not replace the ruler geometry.

## Symptom

The browser can display the legacy fixed-width ruler even after sequence 7 is
successfully applied. The visible signs are a short ruler centered in the
application and the old number string spilling to the left, especially at high
zoom.

## Cause

The Documents entry page still referenced `office-shell.js` with its old
`0.19.0-beta` query. The shared shell then requested `workspace-layout.css` and
`workspace-layout.js` without a version query. GitHub Pages or the browser HTTP
cache could therefore reuse pre-0.19.4 assets while the repository itself was
already current.

## Correction

- Documents requests the current ruler stylesheet and runtime explicitly with
  `v=0.19.4.7.1`.
- The shared shell versions every dynamically loaded UI asset and replaces a
  stale existing node.
- The service worker treats query-versioned shell assets as their canonical
  unversioned cache entry and refreshes them with `cache: no-store`.
- Documents local CSS disables the retired pseudo-element number string as a
  safe fallback.

The ruler feature version remains `0.19.4.7`; `0.19.4.7.1` is a delivery
hotfix applied as repository sequence 8.
