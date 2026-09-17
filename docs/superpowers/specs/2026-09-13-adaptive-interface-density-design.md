# InkDOS 2.3 Adaptive Interface Density Design

## Status

**USER-APPROVED — 2026-09-13**

Chronology is governed by `docs/superpowers/specs/2026-09-13-pre-release-ui-slides-intervention-design.md`. This density work is the second item in the temporary pre-release intervention, after the CSV/TSV preservation correction and before Presentations functional corrections.

## Purpose

InkDOS already has a satisfactory mobile/touch visual design. On desktop, the same touch-friendly frame consumes more space than necessary. The goal is not a second desktop UI or an Office clone; it is the current InkDOS interface at desktop-appropriate density so more screen area belongs to the actual document, spreadsheet, slide, PDF, text, or EPUB content.

Product priority remains: functionality/data preservation first, comfortable device use second, visual refinement third.

## Scope

Applies globally to Home, Documents, Spreadsheets, Presentations, PDF, Plain Text, and EPUB.

Density may change only frame/chrome such as:

- top/edit/status bars;
- toolbar buttons and icons;
- selects/dropdowns;
- gaps and padding;
- hamburger/drawer controls;
- navigation chrome such as thumbnail rails where appropriate.

It must not change internal content scale or editing geometry:

- document page dimensions/zoom;
- spreadsheet cells/zoom;
- slide dimensions/zoom;
- PDF page geometry/zoom;
- EPUB or Plain Text content size except existing user-controlled content settings;
- parsing, saving, history, preservation, or editing semantics.

## User-facing modes

One suite-wide local preference:

- `Auto` — default
- `Desktop`
- `Mobile`

The preference is shared across workspaces and stored locally only.

### Auto resolution

Resolve at workspace startup:

- **Desktop** when usable viewport width is at least **900 CSS px** and `matchMedia('(hover: hover) and (pointer: fine)')` matches;
- **Mobile** otherwise.

Use capabilities and available width, not operating-system names. The effective mode remains stable for that page session; resizing does not continuously flip modes. A new workspace/page load resolves Auto again.

### Manual override

Desktop and Mobile force their respective density until changed. Manual override persists locally across workspaces. Returning to Auto restores automatic resolution.

## Visual behavior

### Mobile

Preserve current InkDOS appearance and touch comfort as closely as practical. Keep touch targets around the existing 40–44 px scale where needed.

### Desktop

Keep the same structure, commands, ordering, and icons, but compact chrome. Typical targets are controls around 28–32 px high, icons around 15–17 px, smaller gaps/padding, narrower readable selects, and thinner bars/navigation chrome.

The content itself does not become smaller. The gain goes to usable editor area.

Home participates in the same preference but receives only modest compaction; the main benefit is inside workspaces.

## Architecture

A small static shared client-side density authority owns:

- stored preference: `auto | desktop | mobile`;
- effective mode: `desktop | mobile`;
- local persistence;
- Auto resolution;
- root attribute application such as `data-ui-density="desktop"` / `mobile`;
- immediate current-page updates when a manual mode changes.

CSS consumes the root density attribute through shared variables/narrow selectors. Existing command wiring and editor semantics should remain untouched unless styling alone cannot safely compact a control.

No backend, telemetry, account, or network dependency is introduced. It must remain offline/PWA/Tauri safe.

## Menu behavior

Each workspace hamburger menu exposes the same Interface selector: Auto / Desktop / Mobile. Home exposes the same options through its existing settings control.

Changing the setting must:

1. persist the suite-wide preference locally;
2. apply the new effective density immediately;
3. update selected menu state;
4. avoid workspace reload;
5. preserve active file/session, dirty state, selection, history, and zoom.

If localStorage is unavailable, fall back to Auto for that session without blocking startup.

## Accessibility

Both modes preserve keyboard navigation, focus visibility, accessible labels, menu semantics, reduced-motion behavior, theme behavior, and mobile safe areas. Desktop compaction must remain comfortable for mouse/trackpad; Mobile must preserve touch-friendly targeting.

## Testing / acceptance

Verify in Chromium, Firefox, and WebKit:

- first run defaults to Auto;
- >=900 CSS px + fine pointer + hover resolves Desktop;
- narrower/coarse/non-hover resolves Mobile;
- Desktop/Mobile overrides persist across workspaces/reloads;
- returning to Auto restores automatic resolution;
- storage failure does not block startup;
- Home + six workspaces apply density without noticeable startup flash;
- switching modes does not reload or lose session/history/selection/dirty/zoom state;
- Desktop visibly reduces frame footprint;
- Mobile remains close to current touch UI;
- document/cell/slide/PDF/content geometry remains unchanged;
- no network/backend/telemetry is introduced.

One real desktop browser visual review is required before 2.3 release.

The user approved this design on 2026-09-13.