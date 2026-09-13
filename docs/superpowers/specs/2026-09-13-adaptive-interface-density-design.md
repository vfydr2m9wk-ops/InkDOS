# InkDOS 2.3 Adaptive Interface Density Design

## Status

Approved product direction for InkDOS 2.3. This work is inserted before continuing Goal 2 (Presentations usability/fidelity).

## Purpose

InkDOS already has a visually satisfactory interface for mobile and touch-oriented use. On desktop, however, the application frame consumes more space than necessary because the same touch-friendly control sizing is stretched across a larger screen.

The goal is **not** to create a second desktop interface, redesign the editors, or imitate Microsoft Office / Google Docs. The goal is to make the existing InkDOS frame more compact on desktop so that more space is available for the actual document, spreadsheet, slide, PDF, text, or EPUB content.

Product priority remains:

1. functionality and data preservation;
2. comfortable use on the current device;
3. visual fidelity/refinement.

## Scope

This change applies globally to:

- Home
- Documents
- Spreadsheets
- Presentations
- PDF
- Plain Text
- EPUB

It changes **frame density only**:

- top bars;
- editing toolbars;
- buttons;
- selects/dropdowns;
- toolbar gaps and padding;
- hamburger/drawer controls;
- status bars;
- slide thumbnail rails or similar navigation chrome where appropriate.

It does **not** change the internal content scale or editing model:

- document page dimensions and zoom;
- spreadsheet cell dimensions and zoom;
- slide dimensions and zoom;
- PDF page dimensions and zoom;
- EPUB/text content scale except where the user explicitly changes content/font settings;
- file parsing, saving, preservation, history, or editing semantics.

## User-facing modes

The hamburger menu exposes one global control:

**Interface**

- Auto (default)
- Desktop
- Mobile

The selected preference is shared across the suite and persisted locally. No account, backend, telemetry, or network access is involved.

### Auto

`Auto` resolves to an effective density at workspace startup.

The initial deterministic rule is:

- use **Desktop** when the usable viewport width is at least **900 CSS px** and `matchMedia('(hover: hover) and (pointer: fine)')` matches;
- otherwise use **Mobile**.

The rule intentionally uses interaction capability and available width rather than operating-system names. The 900 px threshold may only be changed later as an explicit product adjustment backed by browser/device testing, not silently during implementation.

The effective mode is chosen when the workspace loads and remains stable for that page session. Resizing a window does not continuously flip between Desktop and Mobile because spontaneous layout changes during editing would be disruptive.

A new workspace/page load resolves Auto again from the current environment.

### Desktop override

Forces compact frame density regardless of automatic detection.

### Mobile override

Forces the current touch-oriented frame density regardless of automatic detection.

Manual overrides persist locally until changed by the user.

## Visual behavior

### Mobile density

Mobile preserves the current InkDOS design as closely as practical.

Typical targets:

- controls around 40–44 px where touch comfort currently depends on that size;
- existing toolbar spacing;
- existing mobile/tablet scrolling behavior;
- no intentional reduction of touch hit targets.

### Desktop density

Desktop uses the same structure, commands, icons, ordering, and menus with reduced chrome dimensions.

Typical targets, subject to per-workspace testing:

- controls around 28–32 px high;
- icons around 15–17 px where currently larger;
- reduced horizontal/vertical padding;
- reduced gaps between adjacent toolbar controls;
- narrower selects when labels remain readable;
- thinner top/edit/status bars;
- denser navigation rails where this increases content area without harming usability.

The intended visual result is **the current InkDOS interface at desktop-appropriate density**, not a new ribbon, not an Office clone, and not a desktop-only command layout.

## Home screen

Home participates in the same global preference so the behavior is coherent across the suite, but it receives only modest desktop compaction.

Home exposes Auto / Desktop / Mobile through its existing settings control and writes the same suite-wide preference used by all workspaces.

The main value of Desktop density is inside workspaces, where vertical and horizontal pixels directly affect editing space.

## Architecture

A small shared, client-side density authority owns:

- preference values: `auto`, `desktop`, `mobile`;
- local persistence;
- environment detection for Auto;
- effective-mode resolution;
- applying the effective mode as a root document attribute, e.g. `data-ui-density="desktop"` or `data-ui-density="mobile"`;
- notifying the current page when the user manually changes the preference.

The preferred implementation is a shared local runtime module used by Home and all six workspaces. It must remain static/offline-safe and must not introduce any network dependency.

CSS consumes the root density attribute through variables or narrowly scoped selectors. Existing workspace HTML and command wiring remain unchanged unless a control cannot be compacted safely through styling alone.

The implementation favors shared density tokens for common frame dimensions while allowing small workspace-specific adjustments where a toolbar or navigation rail has unique geometry.

## Persistence

Use one suite-wide local preference key.

Conceptually:

- stored preference: `auto | desktop | mobile`;
- effective mode: `desktop | mobile`.

The stored preference and effective mode are distinct. `Auto` remains visible as the selected menu option even when it currently resolves to Desktop or Mobile.

If local storage is unavailable, the application falls back to `auto` for that session without blocking startup.

## Menu behavior

Each workspace hamburger menu exposes the same three-option Interface selector.

Changing the setting must:

1. save the suite-wide preference locally;
2. resolve/apply the new effective density immediately on the current page;
3. update the menu selection state;
4. avoid reloading the document or workspace;
5. avoid resetting selection, history, zoom, dirty state, or file session state.

Home exposes the same three options through its existing settings control.

## Accessibility and interaction constraints

Desktop compaction must not make controls difficult to target with a mouse/trackpad. Mobile density must preserve touch-friendly targets.

Both modes preserve:

- keyboard navigation;
- focus visibility;
- accessible labels;
- menu semantics;
- reduced-motion behavior;
- color/theme behavior;
- safe-area behavior on mobile.

## Offline/local-first constraints

The feature must:

- make no network requests;
- require no backend;
- require no telemetry;
- work in the PWA/offline shell;
- work in the Tauri desktop build;
- persist only the non-sensitive UI preference locally.

## Testing requirements

### Detection and persistence

Verify:

- first run defaults to Auto;
- viewport >= 900 CSS px plus fine pointer + hover resolves to Desktop;
- a narrower viewport or coarse/non-hover primary pointer resolves to Mobile;
- Desktop override persists across workspaces and reloads;
- Mobile override persists across workspaces and reloads;
- returning to Auto removes the forced override behavior;
- unavailable localStorage does not block startup.

### Cross-workspace behavior

For all six workspaces plus Home:

- mode is applied before or immediately at frame initialization to avoid noticeable layout flash;
- manual switching does not reload or lose the active file/session;
- Desktop mode reduces frame footprint;
- Mobile mode preserves the existing touch-oriented footprint;
- internal content geometry/zoom remains unchanged.

### Browser coverage

Validate in Chromium, Firefox, and WebKit.

Include at least representative desktop and narrow/touch viewport tests. Device emulation is acceptable for automated layout contracts, but one real desktop browser review should be done before 2.3 release.

## Acceptance criteria

The feature is complete when:

1. `Auto` is the default suite-wide mode.
2. A desktop-like environment (>= 900 CSS px, fine pointer, hover) opens workspaces with compact Desktop frame density without user action.
3. Other environments open with Mobile density without user action.
4. The hamburger/settings control provides Auto / Desktop / Mobile manual override.
5. The preference is shared across InkDOS workspaces and saved locally.
6. Desktop density visibly increases usable editor space without changing document/cell/slide/page content scale.
7. Mobile remains visually and functionally close to the current interface.
8. Switching density does not reset file state, history, selection, dirty state, or zoom.
9. No new network dependency, telemetry, or backend is introduced.
10. Cross-browser regression tests pass before Goal 2 resumes.

## Sequence in InkDOS 2.3

The development sequence becomes:

1. Goal 1 — format expansion / preservation checkpoint
2. **Adaptive Interface Density — Auto/Desktop/Mobile**
3. Goal 2 — Presentations functionality first (text overflow, object selection/movement, mouse/touch behavior; fidelity refinements only where low-risk)
4. Goal 3 — desktop file integration
5. Goal 4 — manual desktop updater
6. Final validation and InkDOS 2.3.0 release

Goal 2 remains frozen while the adaptive density layer is implemented and validated. After this layer is stable, Goal 2 resumes from its existing branch state rather than being redesigned from scratch.
