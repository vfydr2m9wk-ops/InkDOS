# Changelog

## Unreleased

Next version: 2.9.0 (owner: the project is still young, so 2.9 rather than 3.0); its identity lands in a separate
release PR (repository rule), and the Windows installer and tag follow once the owner has checked the web edition.

Plan (owner, 2026-10-09): InkDOS apps are the entry for every file; ONLYOFFICE (Documents, Spreadsheets,
Presentations) and BentoPDF (PDF) open only on request from a button left of the Settings (sun) button. Done in
controlled steps, each listed here.

Working method (owner, 2026-10-09): one controlled step at a time. Before every push,
`python3 scripts/check_before_push.py` (regenerates the Plain Text bundle and the offline snapshot, runs the CI
release validation and `scripts/smoke_ui.py` in one Chromium set up like an iPad); after the deploy, the smoke
check again on the published site, and the CI result on GitHub, before telling the owner.

CI fixes (2026-10-09): the CI had been red since the Plain Text wording change, whose generated bundle was not
rebuilt (`build_txt_bundle.py --check`); and the localization test took its snapshot before the Edit with
ONLYOFFICE button joined the header (it now waits for it).
CI, minor fixes (owner, 2026-10-10): a minor, low-risk fix may skip the full visual audit (candidate-distribution) on
its PR, with a line "Visual audit: skip" and the reason in the PR description; the audit now also runs on main after
every merge, so nothing goes unaudited.
CI speed (2026-10-09): the candidate-distribution job runs in Chromium only (Firefox and WebKit dropped for now) and
only after integration-validation passed, so a red run stops early; its optional performance benchmark is gone.

Step 10 · Edit PDF layer (owner report, 2026-10-10):
- The "Back to the PDF" button was light text on a light background in the dark theme (it used a colour the PDF
  workspace does not define); it now uses the workspace's control colours. `smoke_ui.py` checks its contrast in both
  themes.
- Scrolling on iPad: the BentoPDF frame now sits in a scrolling box that fills the rest of the screen, so the page
  scrolls even when Safari sizes the frame to its content.

Step 9 · Edit with ONLYOFFICE takes the document on screen (owner report, 2026-10-10):
- A document started in InkDOS did nothing on "Edit with ONLYOFFICE": the button only sent a file opened from the
  device (and then as it was opened, without the edits made here), and stayed disabled otherwise. Now the workspace
  writes what is on screen to DOCX / XLSX / PPTX with its own Save writers (nothing is saved or marked saved) and
  ONLYOFFICE opens that. Files InkDOS only views (.doc, OpenDocument) still go as they were opened.
- `smoke_ui.py`: new document → Edit with ONLYOFFICE, in all three office workspaces.

Step 8 · OCR, beta tools, cache promises, lock, EPUB (owner, 2026-10-09):
- OCR only in BentoPDF: the PDF workspace loses Page tools → Make searchable (OCR), its engine (Tesseract) and
  translations; the Home quick tools lose OCR; the offline cache no longer lists the OCR files or the PDF tools page.
- Beta tools: no mention left in the web edition (the PDF workspace's hidden Beta tools panel and its bridge, the
  Windows-only Beta tools entry in the sun, the "beta" badge and translations). The Windows app's beta channel
  (desktop/src-tauri/src/beta.rs, labs/pdf) goes in the next step, when the installer brings every tool with it.
- No cache-time promise: the Offline tools panel (engine site) no longer says "up to a year".
- Home: the download button does not appear in browsers that cannot keep pages offline (no service worker or Cache
  Storage).
- Security (lock): besides the recovery drafts (with password = encrypted on this device), the PDF workspace offers
  "Protect with password" and "Remove password", which open BentoPDF's page for it with the open PDF.
- EPUB: the page-animation list (Turn / Slide / Off) leaves the tool bar; only the two view symbols (pages, scroll)
  remain.

Step 7 · tool bars back to 2.8 (owner, 2026-10-09):
- PDF: the single 2.8 tool bar is back (the View · Annotate task bar is gone; the editing pencil is in the tool bar
  again). "Edit with BentoPDF" becomes "Edit PDF" ("Editar PDF") in the header, left of the sun, like Edit with
  ONLYOFFICE; it still opens BentoPDF's editing tools with the current PDF. Fill & sign (Beta tools) stays removed.
- Documents and Presentations: the Preview button added after 2.8 leaves the tool bar (with its modules and tests),
  so the bars match 2.8; the original layout is what Edit with ONLYOFFICE shows.
- Phones: Edit with ONLYOFFICE shows only the ONLYOFFICE mark, and the Presentations title gives way like the
  others, so nothing in the header covers the title (`smoke_ui.py` checks it).

Step 6 · PDF: Edit with BentoPDF:
- "Edit with BentoPDF" ("Editar com BentoPDF") is a header button left of the Settings (sun) button. It opens BentoPDF's
  editing tools over the workspace with the current PDF, as Edit PDF did.
- The task bar under the header keeps View and Annotate; the Edit PDF tab is gone.
- On phones the header buttons shorten ("BentoPDF", the ONLYOFFICE logo alone) and the document title gives way, so
  the sun, the lock and Share stay on screen; the buttons join the header together with the sun, so it never
  moves under a finger (the CI's first-tap test caught both).

Step 5 · Documents, Spreadsheets, Presentations: Edit with ONLYOFFICE:
- The button left of the sun reads "Edit with" / "Editar com" followed by the original ONLYOFFICE logo
  (`assets/icons/onlyoffice.svg`, light on the dark theme), in place of the small mark and plain text.

Step 4 · Settings (sun) and Security (lock), all six workspaces:
- The sun keeps only Appearance (light, dark, system), Interface (auto, desktop, smartphone) and Language.
- Full screen leaves the sun.
- Recovery drafts (keep, with password, none) move to a new lock button right of the sun, titled Security
  (translated in the seven languages).
- Still in the sun, only in the Windows app: the Beta tools entry, pending the owner's decision.

Step 3 · one entry point:
- Owner decision: everything goes through this repository and https://vfydr2m9wk-ops.github.io/InkDOS/. The site
  inkdos-tools.github.io is now only the hidden engine InkDOS calls (ONLYOFFICE, BentoPDF, the Offline tools
  panel): its Home and its copies of the InkDOS apps are gone (its own CHANGELOG.md). The Cloudflare mirror stays
  paused and isolated.
- README and third-party notices: no links to the inkdos-tools repositories, the engine site or Cloudflare; the
  upstream projects (ONLYOFFICE via ranuts/document, BentoPDF) stay credited with their licenses.

Step 1 · tools address and suite Home:
- The tools origin is back to https://inkdos-tools.github.io (CSP, postMessage targets, desktop host, tests): the
  Cloudflare mirror (https://inkdos-offic.pages.dev) is paused, its address and project kept for later.
- Suite Home (inkdos-tools.github.io repository): plain workspace cards, no OCR button, Offline tools as a download
  button left of the sun. See that repository's CHANGELOG.md.

Step 2 · InkDOS Home (the base):
- Header: a download button left of the Settings (sun) button opens the suite's Offline tools panel (Download all,
  Check for updates, per-tool status and warnings) over Home, in a frame of the suite's origin
  (`assets/tools-download.js`); Home and its theme stay as they are.
- Closing that panel no longer lets the same tap open the workspace card behind it (a short invisible shield).
- Footer: only "Powered by ONLYOFFICE" (logo in `assets/icons/onlyoffice.svg`) and "Source"; the GitHub,
  Desktop release and Limitations links are gone. "Powered by ONLYOFFICE" sits centered, "Source" on the right.

## 2.8.0 — 2026-10-06

Home:
- Advanced tools: a button on Home opens a central, searchable list of open-source tools that run in the browser (PDF toolkit, extract ZIP/RAR/7z, CyberChef, IT-Tools, Python terminal) inside an InkDOS panel with the same bar and theme as the workspaces, or in a full window.
- The workspace cards describe what each one opens now that legacy and LibreOffice/Apple files are view only.
- The browser extension link is gone (the extension is discontinued).

Documents, Spreadsheets, Presentations:
- Legacy .doc, .xls and .ppt open view only, without converting them.
- LibreOffice (.odt, .ods, .odp) and Apple (.pages, .numbers, .key) files open view only in the matching workspace, also straight from the computer when InkDOS is installed from the browser; nothing is uploaded or converted.

Spreadsheets:
- Large workbooks: editing a cell takes milliseconds instead of a pause (undo keeps only the touched cells); opening is faster, shows its progress and no longer freezes the window; scrolling back and forth reuses cells instead of rebuilding them.

Plain Text:
- Opening a very large file (4 MB or more) says so before the editor pauses, and opens faster.

Desktop (Windows):
- Closing the last window ends InkDOS: a file opened from Windows no longer leaves a hidden Home window running in the background (and holding memory); starting InkDOS again shows Home.
- Release builds produce only the Windows package.

Security:
- The advanced tools and viewers are served from their own origin (inkdos-tools.github.io), so their third-party code cannot reach InkDOS's storage, offline cache or windows; files are exchanged only with explicitly checked origins, and every tools page has a strict Content-Security-Policy (nothing is sent to other sites).
- The offline service worker serves a cached file only while it matches the release snapshot.
- PDF tools (beta) exchange documents only with the window that opened them.
- AGENTS.md and SECURITY.md state the origin-isolation rule; a release-validation test enforces it.

## 2.7.8 — 2026-10-05

PDF:
- Official OCR in the web edition: Page tools → Make searchable (OCR) adds an invisible text layer to scanned pages so they can be searched and copied. Poor scans get a second, cleaned-up reading and the more confident one is kept; signed PDFs are refused (a text layer would invalidate the signature); the 12 MB engine is downloaded on first use and then works offline. Not in the desktop app.
- PDF tools (beta) open from a new Beta tools button in the toolbar, in a panel on the same page: the open PDF is handed over and the result comes back into the workspace. The panel works offline after its first use; its OCR tab is hidden in the web edition, which has the official OCR.

Desktop:
- Beta tools receive the PDF open in the workspace and send their result back (needs this desktop release and the current beta tools bundle).
- A beta-tools download stops as soon as it passes the size limit.

Tests and CI:
- Release validation runs the 49 function-style test files that were never run; two stale checks were updated.
- The PPTX background fidelity test no longer fails intermittently.

## 2.7.7 — 2026-10-04

Desktop:
- Beta tools channel: Settings (☀) → Beta tools opens beta tools that are installed and updated separately from desktop releases. Packages are signed (minisign, pinned key) and checked before use.
- The desktop app no longer uses the web service worker, so after an update it no longer shows an older Home page (the earlier extension card disappears).
- Downloads from beta tools are saved and shown in their folder; external links open in the default browser; the app window cannot navigate to outside pages.
- Files opened from the system are limited to 256 MB; a host Content-Security-Policy is enforced.

PDF:
- PDF.js upgraded to 6.4.299 (closes CVE-2024-4367 exposure); eval stays disabled.
- Text can be selected and copied while reading.
- Page navigation, keyboard and scrollbar scrolls made while pages re-render are kept; search no longer uses stale page text.

PDF tools (beta):
- PAdES baseline signatures with AD-RB policy; the signature check now uses the ICP-Brasil trust list and points to the official ITI validator (2.7.6 said there was no trust-list check yet).
- Stricter check: the chain must be valid now, CA certificates and certificates without signing usage are refused, and a signature followed by changes is shown as changed.
- The visible-signature preview no longer mixes results from earlier renders.

Work safety:
- Recovery drafts are encrypted, kept for 7 days, can use an optional password and can be turned off.

Security:
- Documents and EPUB stop decompressing an archive entry once it passes its declared size.
- Presentations sets the unsaved-changes dialog message as text.
- Vendored-code inventory and advisory check; all GitHub Actions pinned to commit SHAs.

Home:
- Removed the empty 'Beta features' heading.

## 2.7.6 — 2026-10-04

Work safety (all editing workspaces):
- Documents, Spreadsheets and Presentations keep a recovery draft on this device while there are unsaved changes (every ~45 s of editing and when the page goes to the background or closes). Reopening the workspace offers Recover / Discard; recovered work stays unsaved.
- Persistent storage is requested so the browser does not evict drafts.
- A notice says when a new version is waiting; it is used once every InkDOS window is closed (open pages are never replaced).

PDF tools (beta, web edition only):
- Settings (☀) → Beta tools → PDF tools in every workspace; the PDF workspace hands over its open PDF and takes results back.
- OCR (Portuguese/English) makes scanned PDFs searchable, entirely in the browser.
- Visual signature: draw or choose an image and place it on a page.
- Digital signature with an A1 certificate (.pfx/.p12) as an incremental update (earlier signatures stay valid), with an optional visible box showing the signing date and time and an optional document lock (certification: later changes invalidate it).
- Signature check: integrity, signer, certificate dates, changes after signing (no ICP-Brasil trust-list check yet).

Home:
- The browser extension link moved to the footer (extension branch); 'PDF tools (beta)' link on the web edition.

## 2.7.5 — 2026-10-04

Measured against public Office files with PDF references (Word, Excel and PowerPoint exports) and level-1/2 acceptance tools (`scripts/*_acceptance.py`).

Documents:
- Saving an untouched DOCX keeps its text exactly: hyperlink paragraphs no longer make Save fail; footnotes, comments, table cells, text boxes, tabs and symbols are no longer rewritten.
- Tables taller than a page are no longer clipped; cell line breaks, tabs, pictures and content-control cells are shown.
- First-page headers/footers; continuous section breaks no longer start a page.
- DOC: footnotes, endnotes, comments, text boxes, header/footer and inline/floating pictures; field codes hidden.

Spreadsheets:
- The grid shows dates and formatted numbers (dates showed as serial numbers), accounting/section formats and XLSX custom formats.
- Opening keeps Excel's cached results; XLS 3-D references, array formulas and the full function table decode; XLSX shared formulas keep their formula; chart sheets keep their tab.

Presentations:
- Equations and 3-D models (compatibility fallbacks), picture-filled text boxes, translucent backgrounds, footer placeholders without body bullets.
- PPTX/DOCX with bytes after the archive end open.

Other:
- The browser extension moved to the `extension` branch; Home no longer links it.

## 2.7.4 — 2026-10-02

Interface (all workspaces):
- The hamburger menu is replaced by direct header actions: Home, Open and Save on the left; Settings (same options as Home: appearance, interface, language) and Share on the right; Help at the right end of the status bar. On narrow screens the file title fits between them.
- One zoom control everywhere: −/+ in 25% steps, an editable value (1–800%) and a preset menu with Fit page / Fit width.

Saving and export:
- Spreadsheets: Save opens options: overwrite the original (when the host provides a writable file, with a risk warning that recommends a copy), save an edited copy, or export XLSX, CSV or PDF.
- Spreadsheets: new in-app PDF export (orientation, margins, scale, pages per sheet, page range), built inside InkDOS without the print dialog.
- When a host blocks system sharing (NotAllowedError), Save/Share download the file instead and the status says so.

Fidelity:
- Spreadsheets: legacy XLS text boxes keep their borders; unwrapped text overflows into empty neighbours like Excel, stopping at cell borders; print gridlines follow the workbook setting.
- Presentations (PPTX): placeholder text inherits alignment, bullets, spacing, size, bold, font, colour and all-caps from layout and master; backgrounds fall back to layout/master, including theme picture backgrounds.
- Presentations (PPT): paragraph alignment is read from the file.

Fixes:
- Desktop (Windows): a DOCX opened by file association no longer stays on the Documents start screen.
- Spreadsheets: workbooks open again (the loading overlay was missing after the zoom change).
- PDF: text and pen properties appear only for their tool, with icon labels; pen and the review highlighter are no longer active at the same time.
- EPUB: the reading area fills the window, text margins are selectable (minimum, standard A4, large) and pages turn with an animation.

## 2.7.3 — 2026-09-29

Opening files (web / installed app hosts such as XeOS):
- Home declares every format of the suite and sends each launched file straight to its workspace page; when a host delivers the file to Home, Home shows nothing and hands the file over immediately. Opening Home without a file is unchanged (#292, #293).
- Each launched file opens in its own window; workspaces no longer ask hosts to focus an existing window (#290).

Printing:
- PDF: Print was blocked by the page security policy and printed nothing; it now prints every page of the document, without the app UI (#294).
- Presentations: the Print button is now in the toolbar and prints every slide, one per landscape page (#295).
- Spreadsheets: prints the whole active sheet (values, colours, borders, merged cells, charts, images) instead of the app UI and visible cells, in landscape and scaled to width when wide (#296).
- Plain Text: new Print button; the whole text is split into A4 pages with margins (#297).
- In these workspaces, printing from the browser menu uses the same path as the button.

Performance and fixes:
- Documents: an open document no longer redraws 60 times per second while idle (~35% of a CPU core → ~0%) (#298).
- Spreadsheets: the grid renders only the visible cells (click/arrow ~100 → ~12 ms, edit ~680 → ~85 ms on a 1,000-row file); every row of the file is shown (XLSX previously stopped at row ~600, CSV at row 100); cheaper undo snapshots (#299).
- Spreadsheets: formulas recalculate like Excel — only the formulas affected by an edit, each once (20,000-formula sheet: ~650 → ~55 ms per edit); results identical to the previous evaluator (#303).
- Plain Text: typing in large files no longer recounts the whole text on every key (~120 → ~38 ms per key on 1.7 MB) (#300).
- PDF: only the pages near the viewport are drawn at full resolution; on 2× screens the target page appears in ~0.2 s instead of 1–1.7 s and page jumps use ~60% less CPU (#301).
- Presentations: the unused Select button was removed (#302).

Timings are synthetic Chromium measurements; iPad behaviour has not yet been measured on device.

## 2.7.2 — 2026-09-27

- Spreadsheets: saving an opened XLSX is now linear in size and no longer rewrites untouched cells. Opening had resolved theme colours only on the working copy, so every cell compared as changed, and each patch looked its row up with a full scan. Measured (synthetic, Chromium): 2,000 rows 8.7 s → 0.12 s; 10,000 rows from minutes (tab frozen) → 0.7 s.
- No other application changes are part of this release.

## 2.7.1 — 2026-09-27

- Toolbar order aligned with Google Docs/Sheets/Slides, Word and LibreOffice conventions:
  - Documents: Alphabetic list sits with the other list types; the Document panel toggle moves to the view group at the end.
  - Spreadsheets: Sort ascending/descending precede Filter.
  - Presentations: Table joins the insert group (text box, image, shape, line); the slide-thumbnails toggle sits beside Notes.
- Maintenance: legacy release-candidate workflow retired, button audit and workflow-run pruning available on demand.
- No editor, file engine, storage or command behaviour changes are part of this release.

## 2.7.0 — 2026-09-27

- Unify the visual language of all six workspaces around one documented system (`docs/visual-system.md`): 44px frame and toolbar rows, 28px controls, 3px spacing, 10px radius, 18px stroke icons and a shared canonical icon set, each app keeping its own copy and accent colour.
- Replace text and glyph toolbar buttons with icons in Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB, keeping every former label as tooltip and accessible name; value pickers (style, font, alignment, spacing, number format, borders, shape, layout, transition…) render as compact icon controls, font size as a compact number and zoom as a plain percentage.
- Presentations: remove the 18px top-bar offset, stacked toolbar dividers and the ambiguous slide-move glyphs; PDF: 44px toolbar with compact zoom, page and property pickers; EPUB: icon flow switch; Plain Text: 44px frame and uniform spacing.
- Home: add a "Desktop release" link to the latest GitHub release next to the source and limitations links.
- Release process: disconnect the pre-publication physical Windows device-upgrade gate (maintainer decision); stabilise the conditional button audit for EPUB page turns and the Presentations table fixture.
- No editor, file engine, storage or command behaviour changes are part of this release.

## 2.6.2 Beta — 2026-09-24

- Harden XeOS 2.7.5 direct file launches by registering each workspace launchQueue bridge before deferred boot and declaring focus-existing launch handling while preserving each app's existing file handlers, PWA identity, scope and start URL.
- Bind native form controls to the InkDOS-resolved appearance so a dark operating-system theme no longer leaks into controls when a workspace is explicitly set to Light.
- Render modern DrawingML images anchored in DOCX headers and footers, including anchored/inline extents and positioning, while preserving existing VML handling.
- Publish beta tags as web/PWA/source-only GitHub prereleases with no EXE, DMG or AppImage assets; retain full native Tauri builds for stable tags only.
- Cache the pinned Tauri CLI, Cargo registry/index/git data and native target directory for stable builds, with a verified 2.11.4 installation fallback.

## 2.6.1 — 2026-09-24

- Promote the 2.6 line to the stable release channel after final direct-app/PWA validation.
- Give Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB stable workspace-specific manifest identities so separately installed workspaces cannot collapse into one PWA identity.
- Preserve each workspace's existing app-local scope, start URL, file handlers, editors and file engines; no functional editor rewrite is part of this patch.
- Refresh Home cache-busters, the verified offline snapshot, desktop package metadata and signed updater/release artifacts from one immutable 2.6.1 tag.
- Preserve `v2.6.0` as the historical beta checkpoint rather than moving or rewriting that tag.

## 2.6.0 — 2026-09-24

- Separate Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB into independently launchable app shells with app-local manifests, icons and direct URLs while keeping Home optional.
- Isolate appearance, language and interface-density preferences per workspace with conservative migration from the 2.5.2 suite-level keys.
- Add verified web file handling for supported formats through app-local file handlers, guarded launchQueue routing and File System Access opening with HTML-picker fallbacks; converted legacy imports remain copy-safe and opened source handles are never retained for write-back.
- Preserve confirmed-delivery semantics for Save/replace flows so picker cancellation, write failures, Web Share handoff and unverified downloads cannot silently clear unsaved state.
- Bind offline caches to a SHA-256 verified immutable source snapshot, reject incomplete candidate installs and retain the native service-worker waiting lifecycle so open editors are not switched across revisions.
- Validate the exact release candidate across Chromium, Firefox and WebKit with the full Home + six-app visual matrix, while keeping physical-device acceptance distinct from browser automation.

## 2.5.2 — 2026-09-23

- Hotfix Presentations on mobile after the 2.5.1 toolbar styling regression could leave the slide canvas and thumbnail strip visually empty while the presentation session remained loaded.
- Restore the known-stable 2.5.0 Presentations toolbar geometry while retaining the 2.5.1 fixes in the other workspaces.
- Add a regression contract that keeps the 2.5.1 Presentations override out of the release source.

## 2.5.1 — 2026-09-23

- Unify toolbar control boundaries and compact geometry across Presentations, PDF, Plain Text and EPUB while preserving command order and behavior.
- Normalize Plain Text Undo/Redo icons to the canonical Documents SVG geometry.
- Fix desktop Check for updates placement so Documents, Spreadsheets, Presentations, PDF, Plain Text and EPUB use their menu list instead of the oversized fixed-position fallback.
- Preserve the PDF unified-editor layout, mobile horizontal toolbar access, app isolation and local-first behavior.
- Add permanent 2.5.1 regression coverage for toolbar styling, canonical Undo/Redo geometry and updater drawer placement.

## 2.5.0 — Local preview — 2026-09-21

- Reorganize the PDF toolbar into explicit editing, navigation, view and document-action groups without removing existing PDF capabilities.
- Compact annotation commands to icon-first controls with tooltips and keep text/pen properties contextual to the active tool.
- Stabilize dynamic PDF toolbar injection by giving Reader and Page tools explicit host groups instead of relying on generic neighboring controls.
- Preserve the published 2.4.4 suite settings and presentation-rendering corrections in the local 2.5 development baseline.
- Keep GitHub/release publication disabled for this local development snapshot.

## 2.4.2 — 2026-09-17

- Replace partial selector-based localization with explicit translatable UI roots and a reusable parameterized translation API while continuing to exclude document/user content from localization.
- Complete Documents localization for the start screen, Help, advanced document tools, page layout, navigation/search metadata and status text, including dynamic messages and live language switching.
- Extend full Help localization across Spreadsheets, Presentations, PDF, EPUB and Plain Text, with aligned translation keysets for Portuguese, Spanish, German, French, Simplified Chinese, Japanese and Russian.
- Remove the Documents boot-time English start-copy overwrite that bypassed the locale dictionary and keep dynamically created panels inside the localization lifecycle.
- Rotate the desktop/source version, Home cache-busting routes and offline service-worker cache to 2.4.2 and add localization completeness to the permanent release/desktop validation gates.

## 2.4.0 — 2026-09-17

- Add an optional UI-only localization layer for Portuguese, Spanish, German, French, Simplified Chinese, Japanese and Russian while keeping English as the native source interface and preserving functional attributes, parser tokens, formulas, serialization keys and user content.
- Add compact app-local Appearance / Interface / Language / Help settings with workspace-local language/density persistence and English fallback for missing translations.
- Add regression coverage preventing hidden first-open layers from intercepting pointer/touch input across Documents, Spreadsheets, Presentations, PDF, EPUB and Plain Text.
- Centralize the approved shared-presentation-runtime policy and make the complete integrity gate run against pull-request merge candidates before integration.
- Separate read-only CI from manual update-package application and make native desktop/stability workflows path-aware without weakening the universal integrity gate.
- Harden the unified release pipeline with signing preflight, immutable build provenance, macOS app+dmg updater output, validated draft publication and publish-only recovery using previously validated artifacts.
- Promote Home routes, desktop package metadata and the offline cache from the 2.4 development line to the stable 2.4.0 release identity.

## 2.3.0 — 2026-09-14

- Preserve CSV/TSV delimiter and format behavior across spreadsheet open/edit/save workflows, including the completed semicolon-delimited CSV correction.
- Apply suite-wide adaptive interface density and retain the completed Presentations interaction/overflow and PDF Open work without discarding preserved Goal 3 changes.
- Add the desktop/Tauri-only manual updater path: web/PWA remains inert, there are no startup checks, polling, telemetry or background network requests, and update network access begins only after an explicit Check for updates action.
- Keep update installation separately explicit with current/latest state, release notes, Install/Cancel handling and signed Tauri v2 metadata/artifact/signature trust boundaries.
- Advance Windows MSI, Linux AppImage and macOS native packaging, associations, launchers, multiwindow and package-inspection contracts to the verified pre-release checkpoint.
- Promote release and offline cache identity to 2.3.0 while preserving local-first operation, no backend and no telemetry.
- The final signed installed-updater end-to-end validation remains a release-completion gate and is not claimed complete by this changelog entry.

## 2.2.0 — 2026-09-12

- Promote the unified InkDOS web/PWA and Tauri desktop distribution to the stable 2.2.0 release identity.
- Confirm the installable Windows desktop path on a real machine while retaining native CI packaging for Windows, macOS and Linux.
- Keep the existing client-side workspace engines unchanged; Tauri remains a thin native host that provides desktop open/save dialogs, filesystem delivery and OS integration.
- Synchronize Home cache-busting routes, offline cache identity, release manifests, source locks, desktop package metadata and repository checksums to 2.2.0.
- Preserve the existing browser/PWA edition and all release-validation contracts, including Chromium, Firefox, WebKit and format-preservation regressions.

## 2.1.0 — 2026-09-11

- Promote the current release identity to InkDOS 2.1.0 after the post-2.0.12 hardening cycle, while keeping historical freeze/audit records tied to the releases and commit anchors they actually describe.
- Replace ambiguous Home descriptions with format-specific behavior: DOCX/XLSX/PPTX are the primary editable office formats; legacy DOC/XLS/PPT are import/conversion paths rather than native write-back formats; PDF is described as a read/annotate/export workspace.
- Consolidate suite-wide unsaved-work handling so destructive Open/Home/leave flows use Save / Discard / Cancel and require confirmed delivery before clearing dirty state or authorizing navigation.
- Consolidate single-flight / single-delivery protections intended to prevent overlapping Save requests and fallback chains from producing more than one host delivery for one deliberate Save action.
- Extend legacy format handling with local DOC import and editable DOCX promotion, XLS-to-XLSX import/editing, and PPT-to-PPTX promotion with additional legacy presentation fidelity/clipping handling.
- Extend PDF and EPUB annotation workflows with persistent annotation modes and pending-draft protection.
- Harden EPUB package compatibility across WebKit/ZIP cases including local deflate fallback, URL/path normalization, Unicode/legacy ZIP names, rootfile/spine fallbacks and additional flow/SVG content projection cases.
- Keep automated repository, format-preservation and browser validation across Chromium, Firefox and WebKit; explicitly distinguish this synthetic matrix from real-device acceptance on iPad/XeOS for host-specific delivery and rendering behavior.
- Rotate Home cache-busting routes and the offline cache identity to the 2.1.0 release line.

## 2.0.12 — 2026-09-07

- Make the Home bridge optional in all six workspaces: Home launches apps with `suite=1`, while each app-local frame hides the Home control and removes its target when opened directly or extracted standalone.
- Add a standalone isolation release gate that copies every workspace into an isolated temporary directory, verifies entry resources stay inside the app root, and rejects cross-app/shared-runtime references.
- Refactor EPUB physically without intentionally changing reader algorithms: move package read/write to `io/`, book/content/annotation projection to `engine/`, annotation persistence to `state/`, rendering to `view/`, and start-state styling to `ui/`.
- Remove the old flattened EPUB module copies and require the new physical layout in release validation.
- Validate every service-worker `APP_SHELL` file and update the offline shell to the new EPUB module paths.
- Preserve format scope and existing functional contracts; this release does not claim broader LibreOffice-level fidelity.
- Rotate Home routes and the offline cache to the 2.0.12 / sequence 80 snapshot.

## 2.0.11 — 2026-09-07

- Fix duplicate Save delivery in Documents, Spreadsheets, Presentations, Plain Text and PDF when a host exposes a partially supported native file picker that creates a destination but fails during writable creation or writing.
- Treat a picker `write-failed` result as terminal after a destination handle exists; never fall through to Share or download and silently create a second file from the same Save action.
- Prefer one-shot system file sharing for Save on iPad/iPhone-style touch WebKit hosts when file-based Web Share is available, avoiding the partial File System Access path that produced an empty file plus a valid exported copy.
- Keep Share as a separate explicit operation and preserve each workspace's own file-delivery module; no shared mutable save runtime or cross-app dependency is introduced.
- Add release-level regression checks for the single-delivery invariant, rebuild the deterministic Plain Text bundle, version Home workspace routes and rotate the offline cache.

## 2.0.10 — 2026-09-07

- Make the PDF workspace use an exact local copy of the canonical PDF icon shown on Home, eliminating the previous visual mismatch while keeping the PDF app independently extractable.
- Align the PDF top frame with the established InkDOS app-frame pattern used by Plain Text: left-side navigation controls, a centered icon-and-title group, and the current PDF file name inside a framed pill.
- Preserve the existing `titleText` controller contract, dirty-state indicator, PDF engine, annotation layer, file I/O, Save/Share behavior and appearance controller unchanged.
- Add regression checks that require the PDF app icon to remain byte-identical to the Home icon and require the centered framed-title geometry to remain present.
- Version Home workspace routes and rotate the offline cache to the 2.0.10 sequence.

## 2.0.9 — 2026-09-07

- Add full Light/Dark/System appearance support to Home with a compact sun control and a contextual appearance menu.
- Introduce horizontal appearance preference communication through `inkdos2:appearance`: a choice made in Home or any workspace becomes the suite preference.
- Preserve every workspace's existing appearance UI, CSS and app-private theme engine; only each local appearance controller publishes and consumes the shared preference value.
- Keep each workspace independently functional when extracted from the suite by retaining its own app-specific preference key and local fallback behavior.
- Preserve dynamic `System` behavior through each app's existing `prefers-color-scheme` handling and synchronize already-open pages through the browser `storage` event.
- Add regression checks for the Home dark theme, Home appearance control, local appearance keys and the absence of a shared runtime root.
- Rotate the offline cache to the 2.0.9 sequence.

## 2.0.8 — 2026-09-07

- Make PDF and Spreadsheets Save controls disabled in the initial HTML before app JavaScript runs, so the empty-workspace contract is fail-safe rather than visually/runtime dependent.
- Add explicit disabled styling to PDF and Spreadsheets file-menu actions so Edge/WebKit visibly distinguish unavailable Save/Share actions.
- Keep existing app-local runtime guards: PDF still keys off `session.active`, and Spreadsheets still keys off `session.book.loaded`.
- Version all Home workspace routes with `v=2.0.8` to reduce stale browser navigation ambiguity after releases.
- Add regression checks for initial disabled markup, disabled visual styling and release-versioned Home routes.
- Rotate the offline cache to the 2.0.8 sequence.

## 2.0.7 — 2026-09-07

- Standardize the empty-workspace file-action contract across all six independent apps: Save and Share remain unavailable until a real document, workbook, presentation, text file, book or PDF is active.
- Make Presentations start with a true empty session (`sourceKind: none`, zero slides) instead of constructing a hidden blank presentation; New creates the first slide and Open activates the session only after a successful commit.
- Gate Presentations editing, slideshow, Save and Share commands on an active presentation while preserving legacy PPT read-only behavior.
- Make Plain Text start unloaded until New, a successful Open, or a valid local recovery checkpoint activates a document; Save and Share now follow the same loaded-state contract.
- Align Spreadsheets and PDF Save controls with their existing Share/controller active-state guards.
- Add a suite-level regression contract for empty-state Save/Share behavior without introducing any cross-app runtime dependency.
- Rotate the offline application cache so WebKit/XeOS receives the corrected state behavior.

## 2.0.6 — 2026-09-07

- Remove the production Plain Text global runtime-error banner so opaque host/WebKit `Script error.` events no longer surface as a false app failure.
- Normalize the existing Home bridge and first-open integration into the modular Plain Text template and deterministic bundle.
- Add a deterministic Plain Text bundle builder and a byte-for-byte release validation check so `apps/txt/index.html` must remain derivable from its modular sources.
- Preserve Plain Text editor/runtime modules, TXT file I/O, Share behavior and the other five workspace runtimes unchanged.
- Rotate the offline application cache so WebKit/XeOS receives the corrected Plain Text distribution.

## 2.0.5 — 2026-09-07

- Restore WebKit/PWA standalone installation metadata removed during the 2.0 Home refactor.
- Restore `mobile-web-app-capable`, `apple-mobile-web-app-capable` and Apple standalone status-bar metadata on the Home entry point.
- Restore the manifest identity to `./index.html`, language/categories metadata and `any maskable` purpose for the primary PNG icon.
- Preserve all six workspace runtimes and the 2.0.4 Share implementation unchanged.
- Rotate the offline application cache so WebKit/XeOS receives the refreshed Home and manifest metadata.

## 2.0.4 — 2026-09-07

- Standardize an explicit Share action across all six workspaces; Plain Text and EPUB keep their existing behavior while Documents, Spreadsheets, Presentations and PDF gain matching app-local actions.
- Share exports the current DOCX, XLSX, PPTX or PDF state through the system Share Sheet when Web Share file delivery is available.
- Keep Share separate from Save/Save copy: sharing does not mark unsaved edits as persistently saved.
- Keep legacy PPT read-only, with both Save and Share disabled for that source type.
- Add a six-app Share contract to suite validation and refresh integrated source locks/checksums for the new app-local code.

## 2.0.3 — 2026-09-07

- Install the physically modular PDF P4.2 app; enable Home ↔ PDF navigation and EPUB-style Open PDF card.
- Preserve all five existing app source trees byte-for-byte.
- Exclude internal PDF inspection hooks, fixtures and sample documents.
- Update six-app release locks and offline cache; correct the existing stale Presentations icon cache URL.
- Retain all release contracts as validation tooling, with no internal tests directory in the update payload.

## 2.0.2 — 2026-09-07

- Fixed the Presentations first-open gate so the app no longer exposes the pre-created blank slide before the user chooses New or Open.
- Kept the presentation engine, parser, writer, state and editing controllers frozen; the correction is confined to the presentation entry index.
- Versioned the Home → Presentations route to force a fresh Safari/WebKit navigation after the update.

## 2.0.1 — 2026-09-07

- Standardized first-open cards to the Spreadsheets interaction pattern.
- Documents, Presentations and Plain Text now offer New/Open from the central card.
- EPUB uses the same card with one centered Open action.
- Spreadsheets remains the unchanged visual baseline; PDF remains Coming soon.

## 2.0.0 — 2026-09-07

- Clean-tree consolidation of the five frozen 2.0 apps.
- New Home workspace selector with 3×2 wide layout and single-column phone layout.
- Added one Home bridge to each app entry page; no other app runtime file changed.
- PDF runtime intentionally absent; Home shows a Coming soon placeholder.
- Removed dependency on the 1.x suite shell, recent-files runtime, module launcher and shared application runtime.
- Added clean 2.0 release metadata, integrity locks, service worker and transactional updater.
