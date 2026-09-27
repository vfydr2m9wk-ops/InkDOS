# InkDOS visual system

Reference specification for the visual alignment of the InkDOS workspaces. Documents is the reference implementation. Every other workspace adopts this specification in its own, separate change.

Visual preview of the icon set: [`visual-system-icons.html`](visual-system-icons.html).

## 1. Scope rules

This is a presentation-only specification.

Allowed:
- CSS values (sizes, radius, borders, gaps, colors that already exist in the app);
- replacing a button's visible text or glyph with an inline SVG icon from section 4;
- adding `title` / `aria-label` where they are missing.

Not allowed:
- changing behaviour, handlers, commands, shortcuts, storage or file I/O;
- changing element IDs, `data-*` command attributes, classes read by JavaScript, or button order;
- changing menus, drawers, context panels, dialogs, frames or window structure;
- editing `vendor/`, `engine/`, `io/`, `state/` or minified files;
- converting `<select>` value pickers (style, font, size, number format, spacing, zoom presets) into icons.

Isolation (AGENTS.md): each workspace carries its **own copy** of the icons and token values it needs. Do not import files from another workspace and do not add a new shared file for this work. Deliberate local duplication is intended here.

## 2. Reference tokens (measured from Documents, desktop pointer, compact density)

These are the values Documents renders today at 1440×900 with `pointer:fine`. `shared/ui-density.css` already produces most of the frame values for every app; a workspace only needs local CSS where it deviates.

| Token | Value | Notes |
|---|---|---|
| Top bar height | 44px | `header.topbar`, starts at `top: 0` |
| Toolbar height | 44px | one row, horizontally scrollable, rail arrows at both ends |
| Toolbar padding | 2px block, 16px inline start | end padding leaves room for the rail arrow |
| Toolbar gap | 3px | between controls |
| Group separator | 1px × 24px, `var(--line)`, 3px side margin | between command groups |
| Control height | `var(--compact-control)` = 28px (38px touch) | buttons and selects |
| Icon-only button | 28×28px square, `padding: 0`, grid-centred | class `icon-only` in Documents |
| Text/typographic button | 28px high, `padding: 0 9px` | only for B / I / U / S and numeric labels (e.g. zoom `100%`) |
| Control radius | 10px | buttons, selects, title input uses 11px |
| Control border | 1px `var(--line)` | always visible, not borderless text links |
| Control background | `var(--panel)` | |
| Hover / focus-visible | background `var(--accent-soft)`, no outline | |
| Pressed / active | `var(--accent-soft)` bg, border mixed 70% `var(--accent)`, text `var(--accent)` | `aria-pressed="true"` or `.is-active` |
| Disabled | `opacity: .35`, default cursor | |
| Icon glyph | 18×18px, `fill:none`, `stroke:currentColor`, `stroke-width:1.75`, round caps/joins | |
| Status bar | 26px, 11px text, `var(--muted)`, 1px top border | |
| Start card | 430px max, 28px padding, radius 22px, 68px app icon **centred**, two 44px buttons | primary button uses `var(--accent)` |

Colour tokens stay per app. Only the accent differs:

| Workspace | `--accent` (existing) |
|---|---|
| Documents | `#2f6fed` |
| Spreadsheets | `#267a45` |
| Presentations | `#df542c` |
| PDF | `#d34a42` |
| Plain Text | `#d2a514` |
| EPUB | `#7655c7` |

Light and dark themes: use only the existing `--bg`, `--chrome`, `--panel`, `--text`, `--muted`, `--line`, `--accent`, `--accent-soft` variables. Icons use `currentColor`, so they follow the theme automatically.

## 3. Current deviations (baseline at 2.6.2)

| Workspace | Deviation to fix in its own change |
|---|---|
| Documents | Glyph buttons (`▧`, `Aa`, `☐≡`, `•≡`, `1≡`, `⇤`, `⇥`, `A≡`, `▦`, `▦↧`, `▦↦`, `Page`) — fixed by the reference change. |
| Spreadsheets | Text buttons `Print`, `Paint`, `$`, `%`, `.0←`, `→.00`, `A■`, `Fill■`; bottom shell 44px instead of a 26px status bar (sheet tabs live there — keep the tabs, align only styling). |
| Presentations | Borderless text buttons (`Slide`, `Format painter`, `Text`, `Image`, `Shape`, `Line`, `Comment`, `Background`, `Layout`, `Theme`, transition select, `Table`, `Duplicate`); top bar starts at 18px instead of 0; status bar shows no text. |
| PDF | Toolbar row 56px instead of 44px; `Edit` text button; lighter/smaller controls. |
| Plain Text | Top bar 54px (`framebar`, 8px top padding) instead of 44px; `TXT` text button; start-card icon left-aligned instead of centred. |
| EPUB | Close to reference; check `Aa` (→ `reader-settings`) and the empty-looking TOC button width. `Pages`/`Scroll` segmented control stays. |
| Hub | No toolbar. Keep; only align card radius/shadow if a later change asks for it. |

## 4. Canonical icon set

All icons use `viewBox="0 0 24 24"` and are drawn for the glyph rules in section 2. Frame and edit icons are the ones Documents already shipped; copy them verbatim. The same action must use the same icon in every workspace.

Typographic buttons stay as letters on purpose: **B**, *I*, <u>U</u>, S (strikethrough). They are universally understood and already consistent.

| Name | Group | Default label | SVG |
|---|---|---|---|
| `menu` | frame | Menu | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>` |
| `home` | frame | Home | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 11.5 12 4l8.5 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-6h5v6"/></svg>` |
| `close` | frame | Close | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>` |
| `new` | frame | New | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>` |
| `open` | frame | Open | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 7h6l2 2h9v9.5A1.5 1.5 0 0 1 19 20H5a1.5 1.5 0 0 1-1.5-1.5z"/><path d="M3.5 10h17"/></svg>` |
| `save` | frame | Save copy | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 4h12l2 2v14H5z"/><path d="M8 4v6h8V4M8 20v-6h8v6"/></svg>` |
| `undo` | edit | Undo | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7 4 12l5 5"/><path d="M5 12h8a6 6 0 0 1 6 6"/></svg>` |
| `redo` | edit | Redo | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 7 5 5-5 5"/><path d="M19 12h-8a6 6 0 0 0-6 6"/></svg>` |
| `print` | edit | Print | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 9V4h10v5"/><path d="M7 18H5a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M7 14h10v6H7z"/></svg>` |
| `format-painter` | edit | Format painter | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h12v6H4z"/><path d="M16 7h3v5h-7v8"/><path d="M10 20h4"/></svg>` |
| `panel` | edit | Side panel / context panel | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 4v16"/></svg>` |
| `zoom` | edit | Zoom | `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="5.5"/><path d="m15 15 5 5"/></svg>` |
| `search` | edit | Search / find | `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/></svg>` |
| `duplicate` | edit | Duplicate / copy | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>` |
| `paste` | edit | Paste | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4.5" width="14" height="16" rx="2"/><path d="M9 4.5V3h6v1.5"/><path d="M9 10h6M9 14h6"/></svg>` |
| `delete` | edit | Delete | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16"/><path d="M9 7V4.5h6V7"/><path d="M6.5 7l1 13h9l1-13"/><path d="M10 11v5M14 11v5"/></svg>` |
| `edit` | edit | Edit / annotate | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/></svg>` |
| `tools` | edit | More tools | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h7M15 18h5"/><circle cx="16" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="13" cy="18" r="2"/></svg>` |
| `select` | edit | Select objects | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5.5 3.5 18 10l-5.5 1.5L10 17z"/><path d="m12.5 11.5 5 5"/></svg>` |
| `notes` | slides | Speaker notes | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="11" rx="2"/><path d="M7 18h10M7 21h6"/></svg>` |
| `fullscreen` | edit | Fullscreen / focus | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/></svg>` |
| `text-color` | text | Text color and highlight | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 16 6-12 6 12"/><path d="M8.5 11h7"/><path d="M4 20h16"/></svg>` |
| `highlight` | text | Highlight | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 15 7.5-7.5-3-3L6 12l-1 4z"/><path d="M4 20h16"/></svg>` |
| `link` | text | Hyperlink | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"/><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1"/></svg>` |
| `comment` | text | Comment | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h14v11H9l-4 4z"/><path d="M8 9h8M8 12h5"/></svg>` |
| `clear-format` | text | Clear formatting | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 20 7-7"/><path d="m14 4 6 6-8 8H6l-2-2 10-12Z"/><path d="M13 20h7"/></svg>` |
| `font-size-up` | text | Increase font size | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 18 5-12 5 12"/><path d="M5 13.5h6"/><path d="M18 8v6M15 11h6"/></svg>` |
| `font-size-down` | text | Decrease font size | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 18 5-12 5 12"/><path d="M5 13.5h6"/><path d="M15 11h6"/></svg>` |
| `word-wrap` | text | Word wrap | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h13a3 3 0 0 1 0 6h-4"/><path d="m15 16-2 2 2 2"/><path d="M4 18h5"/></svg>` |
| `text-box` | text | Text box | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 6.5V5h14v1.5"/><path d="M12 5v14"/><path d="M9.5 19h5"/></svg>` |
| `align` | paragraph | Alignment | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 10h10M4 14h16M4 18h10"/></svg>` |
| `bullet-list` | paragraph | Bulleted list | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/></svg>` |
| `numbered-list` | paragraph | Numbered list | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 6h10M10 12h10M10 18h10"/><path d="M4 4.5h1.5V9"/><path d="M4 9h3"/><path d="M4 14.5a1.5 1.5 0 0 1 3 0c0 1.3-3 2-3 4h3"/></svg>` |
| `alpha-list` | paragraph | Alphabetic list | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 6h9M11 12h9M11 18h9"/><path d="m3.5 9.5 2-6 2 6"/><path d="M4.2 7.7h2.6"/><path d="M4 13.5h2a1.3 1.3 0 0 1 0 2.6H4zm0 2.6h2.4a1.45 1.45 0 0 1 0 2.9H4z"/></svg>` |
| `checklist` | paragraph | Checklist | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4" width="5.5" height="5.5" rx="1"/><rect x="3.5" y="14.5" width="5.5" height="5.5" rx="1"/><path d="m4.8 17.3 1.3 1.3 2-2.6"/><path d="M12 6.8h8.5M12 17.2h8.5"/></svg>` |
| `outdent` | paragraph | Decrease indent | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M11 10h9M11 14h9M4 19h16"/><path d="M8 9.5 5.5 12 8 14.5"/></svg>` |
| `indent` | paragraph | Increase indent | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16M11 10h9M11 14h9M4 19h16"/><path d="m5 9.5 2.5 2.5L5 14.5"/></svg>` |
| `image` | insert | Insert image | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="9.5" r="1.5"/><path d="m20.5 16-5-5-8.5 8.5"/></svg>` |
| `table` | insert | Insert table | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 4.5v15M14.5 4.5v15"/></svg>` |
| `add-row` | insert | Add row | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="11" rx="2"/><path d="M3.5 9h17M9 3.5v11M15 3.5v11"/><path d="M12 17v5M9.5 19.5h5"/></svg>` |
| `add-column` | insert | Add column | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="11" height="17" rx="2"/><path d="M3.5 9h11M3.5 15h11M9 3.5v17"/><path d="M19.5 9.5v5M17 12h5"/></svg>` |
| `shape` | insert | Shape | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="10.5" width="10" height="10" rx="1.5"/><circle cx="15.5" cy="8.5" r="5"/></svg>` |
| `line` | insert | Line | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5"/><circle cx="5" cy="19" r="1.5"/><circle cx="19" cy="5" r="1.5"/></svg>` |
| `page-layout` | insert | Page layout | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3.5" width="14" height="17" rx="1.5"/><rect x="8.5" y="7" width="7" height="10" rx=".5"/></svg>` |
| `currency` | sheet | Currency format | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5v17"/><path d="M16.5 7.5c-.7-1.3-2.3-2-4.5-2-2.6 0-4.3 1.3-4.3 3.1 0 4.4 9 2.4 9 6.8 0 1.9-1.9 3.1-4.7 3.1-2.3 0-4-.8-4.8-2.2"/></svg>` |
| `percent` | sheet | Percent format | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/></svg>` |
| `fill` | sheet | Fill color | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 7-7 7 7-7 7z"/><path d="M5 12h14"/><path d="M20 16.5s1.5 1.8 1.5 2.8a1.5 1.5 0 0 1-3 0c0-1 1.5-2.8 1.5-2.8z"/></svg>` |
| `borders` | sheet | Borders | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="1"/><path d="M12 4v16M4 12h16" stroke-dasharray="2 2"/></svg>` |
| `function` | sheet | Functions | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 4.5c-2 0-3 1-3.4 3L9.5 17c-.4 2-1.4 3-3.5 3"/><path d="M8 10h7"/><path d="m15 13 5 6M20 13l-5 6"/></svg>` |
| `merge` | sheet | Merge cells | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M7 12h3M17 12h-3M8.5 10l1.5 2-1.5 2M15.5 10 14 12l1.5 2"/></svg>` |
| `chart` | sheet | Insert chart | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4v16h16"/><path d="M8.5 16v-4M12.5 16V8M16.5 16v-6"/></svg>` |
| `filter` | sheet | Filter | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16l-6 7.5V19l-4-2v-4.5z"/></svg>` |
| `sort-asc` | sheet | Sort ascending | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 20V4M4 7l3-3 3 3"/><path d="M13 7h3M13 12h5M13 17h7"/></svg>` |
| `sort-desc` | sheet | Sort descending | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4v16M4 17l3 3 3-3"/><path d="M13 7h7M13 12h5M13 17h3"/></svg>` |
| `delete-row` | sheet | Delete rows | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="11" rx="2"/><path d="M3.5 9h17M9 3.5v11M15 3.5v11"/><path d="M9.5 19.5h5"/></svg>` |
| `delete-column` | sheet | Delete columns | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="11" height="17" rx="2"/><path d="M3.5 9h11M3.5 15h11M9 3.5v17"/><path d="M17 12h5"/></svg>` |
| `eraser` | sheet | Clear cells | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 20-3.5-3.5a1.5 1.5 0 0 1 0-2.1l9.9-9.9a1.5 1.5 0 0 1 2.1 0l4 4a1.5 1.5 0 0 1 0 2.1L11 20z"/><path d="M7 20h13"/><path d="m9 11 5 5"/></svg>` |
| `add-sheet` | sheet | Add sheet | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>` |
| `new-slide` | slides | New slide | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="13" rx="2"/><path d="M12 8.5v6M9 11.5h6"/></svg>` |
| `background` | slides | Background | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 12 11 4.5M6 19.5 20.5 5M13.5 19.5l7-7"/></svg>` |
| `layout` | slides | Layout | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M10 9.5v10"/></svg>` |
| `theme` | slides | Theme | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.2 0 1.8-.8 1.8-1.7 0-1.4-1.1-1.6-1.1-2.8 0-1 .8-1.7 1.8-1.7H17a3.5 3.5 0 0 0 3.5-3.5c0-4.1-3.8-7.3-8.5-7.3z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7.5" r="1"/><circle cx="14.5" cy="7.5" r="1"/></svg>` |
| `transition` | slides | Transition | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="10" height="12" rx="1.5"/><path d="M16 8h2.5a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H16"/><path d="m8 10 2 2-2 2"/></svg>` |
| `slideshow` | slides | Play slideshow | `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="m10.5 8 4 2.5-4 2.5z"/><path d="M12 17v3M8.5 20h7"/></svg>` |
| `prev` | navigation | Previous | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>` |
| `next` | navigation | Next | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>` |
| `rotate` | navigation | Rotate | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 5v6h-6"/></svg>` |
| `toc` | navigation | Table of contents | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6h1M4 12h1M4 18h1"/></svg>` |
| `bookmark` | navigation | Bookmark | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 4h11v16L12 16l-5.5 4z"/></svg>` |
| `reader-settings` | navigation | Reading settings | `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 18 7.5 6 12 18"/><path d="M4.7 13.5h5.6"/><path d="M14 18v-5.5a2.75 2.75 0 0 1 5.5 0V18"/><path d="M14 15h5.5"/></svg>` |

## 5. Conversion rules

1. Replace only the visible content of the button with the SVG. Keep the element, its ID, classes, `data-*` attributes and position.
2. The old visible text becomes (or stays) the `title` and `aria-label`, **character for character**, so tooltips, screen readers, localisation (`shared/localization` translates `title` and `aria-label`) and existing tests keep working. If the button already has a longer `title`, keep it and put the short label in `aria-label`.
3. Add the app's icon-only class (Documents: `icon-only`) so the button becomes a 28px square.
4. Buttons created in JavaScript follow the same rule: set `innerHTML` to the SVG and `className` to include the icon-only class, keeping `title`, `aria-label` and ID unchanged.
5. If a test asserts a removed glyph, update only that assertion to check the button ID plus its preserved `title`/`aria-label`. Never weaken the command-wiring part of the test.
6. Use a text button only when no icon in section 4 is unambiguous. Add a new icon to this document first instead of inventing one locally.

## 6. Per-workspace checklist

```text
python scripts/agent_context.py <app>
# screenshot /apps/<app>/ at 1440x900: start state + after "New", light and dark
# apply section 2 tokens where the app deviates (section 3)
# convert text/glyph buttons per section 5 using section 4 icons
python scripts/agent_test.py <app> --browser
python scripts/agent_verify.py <app> --base main
# screenshot again and compare with Documents
```

Report the AGENTS.md audit record and list every converted button as `id: old label → icon name`.

## 7. Label → icon map for the remaining workspaces

| Workspace | Visible label today | Icon |
|---|---|---|
| Spreadsheets | Print | `print` |
| Spreadsheets | Paint | `format-painter` |
| Spreadsheets | $ | `currency` |
| Spreadsheets | % | `percent` |
| Spreadsheets | A (text colour swatch) | `text-color` (keep the colour swatch element) |
| Spreadsheets | Fill (swatch) | `fill` (keep the colour swatch element) |
| Spreadsheets | + / − sheet | `add-sheet` / keep `−` or use `delete` |
| Presentations | Slide | `new-slide` |
| Presentations | Format painter | `format-painter` |
| Presentations | Text | `text-box` |
| Presentations | Image | `image` |
| Presentations | Shape | `shape` (keep the adjoining select) |
| Presentations | Line | `line` |
| Presentations | Comment | `comment` |
| Presentations | Background | `background` |
| Presentations | Layout | `layout` (keep the adjoining select) |
| Presentations | Theme | `theme` |
| Presentations | Table | `table` |
| Presentations | Duplicate | `duplicate` |
| PDF | Edit | `edit` |
| Plain Text | TXT (`#textToolsBtn`, "Text file tools") | `tools` |
| EPUB | Aa | `reader-settings` |

`.0←` / `→.00` (decimal places) and numeric labels such as zoom `100%` stay as text: they are values, not actions with a clear pictogram.
