# Adaptive Interface Density Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make InkDOS automatically use compact desktop frame/chrome on desktop-like environments while preserving the current touch-oriented mobile frame and allowing suite-wide Auto/Desktop/Mobile override.

**Architecture:** Add one shared static density authority loaded by Home and all six workspaces. It resolves/persists the suite-wide preference and applies `data-ui-density` at the root before frame initialization. Existing workspace CSS remains authoritative for content; density only overrides common frame variables and narrowly scoped chrome geometry.

**Tech Stack:** Static HTML/CSS/JavaScript, localStorage, matchMedia, existing InkDOS frame/token CSS, Playwright browser tests.

**Spec:** `docs/superpowers/specs/2026-09-13-adaptive-interface-density-design.md`

## Global Constraints

- User-approved pre-release intervention; execute after the CSV/TSV correction and before Presentations corrections.
- Auto default: Desktop only when viewport >= 900 CSS px AND `(hover: hover) and (pointer: fine)` matches; otherwise Mobile.
- Effective Auto mode stays stable for the page session; resize must not continuously flip modes.
- Manual override persists suite-wide and applies immediately without reload.
- Density changes frame/chrome only; internal document/cell/slide/PDF/text/EPUB geometry must not change.
- Mobile should stay visually close to current InkDOS.
- No backend, telemetry, account, or network request.

---

### Task 1: Add RED shared-density contract

**Files:**
- Create: `tests/test_ui_density_contract.py`
- Create later: `shared/ui-density.js`
- Create later: `shared/ui-density.css`

**Interfaces:**
- Produces required shared API `globalThis.InkDOSUiDensity` with `preference`, `effective`, `set()`, `apply()`, and `installControl()`.

- [ ] **Step 1: Write structural assertions**

Require a suite key such as `inkdos2:ui-density`, valid values `auto|desktop|mobile`, 900px threshold, fine-pointer/hover media query, root `data-ui-density`, and no network primitives.

- [ ] **Step 2: Add Node probe for resolution/persistence fallbacks**

Test pure resolution logic with synthetic width/media capability inputs so Auto deterministically returns Desktop or Mobile. Test invalid storage value falls back to Auto.

- [ ] **Step 3: Require all seven entry surfaces to load the shared density assets**

Check `index.html`, Documents, Spreadsheets, Presentations, PDF, Plain Text source/template, and EPUB entry points plus `service-worker.js` APP_SHELL.

- [ ] **Step 4: Run contract and confirm RED**

```bash
python tests/test_ui_density_contract.py
```

Expected: FAIL because shared density authority/assets do not exist.

- [ ] **Step 5: Commit RED test**

```bash
git add tests/test_ui_density_contract.py
git commit -m "test(ui): define adaptive density contract"
```

---

### Task 2: Implement shared density authority and early root application

**Files:**
- Create: `shared/ui-density.js`
- Create: `shared/ui-density.css`
- Modify: `index.html`
- Modify: `apps/documents/index.html`
- Modify: `apps/spreadsheets/index.html`
- Modify: `apps/presentations/index.html`
- Modify: `apps/pdf/index.html`
- Modify: `apps/epub/index.html`
- Modify: `apps/txt/page.template.html`
- Regenerate: `apps/txt/index.html`
- Modify: `service-worker.js`
- Test: `tests/test_ui_density_contract.py`

**Interfaces:**
- `InkDOSUiDensity.set('auto'|'desktop'|'mobile') -> effective mode`
- `InkDOSUiDensity.preference -> stored preference`
- `InkDOSUiDensity.effective -> desktop|mobile`
- `InkDOSUiDensity.installControl(host, options?)` binds the same preference UI without owning workspace editing state.

- [ ] **Step 1: Implement synchronous startup resolution**

On script load read `inkdos2:ui-density`; default to `auto`. For Auto, read `document.documentElement.clientWidth || innerWidth` once and evaluate `matchMedia('(hover: hover) and (pointer: fine)')`. Set `document.documentElement.dataset.uiDensity` immediately.

- [ ] **Step 2: Implement persistence and storage synchronization**

`set()` validates values, writes localStorage if available, applies immediately, emits a local custom event for current-page controls, and listens for `storage` changes from other tabs. Storage failure must not throw.

- [ ] **Step 3: Add generic control rendering**

`installControl(host)` renders three accessible choices (Auto/Desktop/Mobile), keeps Auto selected when it resolves to Desktop/Mobile, and updates `aria-pressed`/active state without reloading.

- [ ] **Step 4: Load assets before workspace bootstrap**

Reference shared JS/CSS in Home and each workspace. Plain Text source template must include the references and then regenerate its checked bundle using the existing build script.

- [ ] **Step 5: Cache shared assets offline**

Add `./shared/ui-density.js` and `./shared/ui-density.css` to the service worker shell.

- [ ] **Step 6: Run contract**

```bash
python tests/test_ui_density_contract.py
```

Expected: PASS for shared authority/loading; workspace geometry compaction comes next.

- [ ] **Step 7: Commit shared runtime**

```bash
git add shared/ui-density.js shared/ui-density.css index.html apps/*/index.html apps/txt/page.template.html service-worker.js tests/test_ui_density_contract.py
git commit -m "feat(ui): add suite-wide adaptive density authority"
```

---

### Task 3: Add Interface control to Home and workspace menus

**Files:**
- Modify: `index.html`
- Modify: `apps/documents/index.html`
- Modify: `apps/spreadsheets/index.html`
- Modify: `apps/presentations/index.html`
- Modify: `apps/pdf/index.html`
- Modify: `apps/epub/index.html`
- Modify: `apps/txt/page.template.html`
- Regenerate: `apps/txt/index.html`
- Test: `tests/test_ui_density_contract.py`

**Interfaces:**
- Consumes: `InkDOSUiDensity.installControl(host)`.
- Produces: user-visible `Interface: Auto / Desktop / Mobile` in each hamburger/settings surface.

- [ ] **Step 1: Add stable density-host containers**

Insert a `data-inkdos-density-host` host in each workspace hamburger drawer near Appearance. On Home, extend the existing top-right settings/appearance surface with an Interface section rather than adding a second floating control.

- [ ] **Step 2: Install controls through the shared authority**

Do not duplicate storage/detection logic in workspace apps. Each host only instantiates the shared control.

- [ ] **Step 3: Verify no workspace state reset**

The control must only alter root density/style state; it must not call workspace new/open/reload/history/zoom/session functions.

- [ ] **Step 4: Rebuild Plain Text bundle and run contracts**

```bash
python scripts/build_txt_bundle.py --check
python tests/test_ui_density_contract.py
```

Expected: PASS.

- [ ] **Step 5: Commit menu integration**

```bash
git add index.html apps/*/index.html apps/txt/page.template.html tests/test_ui_density_contract.py
git commit -m "feat(ui): expose Auto Desktop Mobile density control"
```

---

### Task 4: Compact frame tokens in Desktop mode only

**Files:**
- Modify: `shared/ui-density.css`
- Modify where needed: `apps/documents/runtime/tokens/base.css`
- Modify where needed: `apps/documents/runtime/frame/app-frame.css`
- Modify where needed: `apps/spreadsheets/runtime/tokens/base.css`
- Modify where needed: `apps/spreadsheets/runtime/frame/app-frame.css`
- Modify where needed: `apps/presentations/runtime/tokens/base.css`
- Modify where needed: `apps/presentations/runtime/frame/app-frame.css`
- Modify where needed: `apps/pdf/runtime/tokens/base.css`
- Modify where needed: `apps/pdf/runtime/frame/app-frame.css`
- Modify where needed: `apps/epub/runtime/tokens/base.css`
- Modify where needed: `apps/epub/runtime/frame/app-frame.css`
- Modify where needed: `apps/txt/runtime/tokens/base.css`
- Modify where needed: `apps/txt/runtime/frame/app-frame.css`
- Modify: `assets/home.css`

**Interfaces:**
- Consumes: root `data-ui-density="desktop|mobile"`.
- Produces: smaller desktop chrome without changing content model/zoom.

- [ ] **Step 1: Override common frame tokens**

Desktop target: `--control` about 30–32px, `--compact-control` about 28–30px, smaller frame padding/gaps/content chrome spacing. Mobile explicitly retains current 40–44px touch-oriented values so old `@media(pointer:fine)` rules cannot silently override forced Mobile.

- [ ] **Step 2: Compact fixed frame geometry that is not tokenized**

For selectors such as `.topbar`, `.statusbar`, `.drawer`, `.menu-item`, `.appearance-choice`, `.editbar`, and workspace navigation rails, add narrowly scoped `:root[data-ui-density="desktop"]` overrides. Do not change page/cell/slide/PDF/reader content dimensions.

- [ ] **Step 3: Keep Home compaction modest**

Reduce card/frame padding only enough for desktop proportionality; do not redesign the Home grid.

- [ ] **Step 4: Preserve forced modes over pointer media queries**

Ensure `data-ui-density` selectors have sufficient specificity/order so Desktop and Mobile manual overrides win over existing `@media(pointer:fine)` density shortcuts.

- [ ] **Step 5: Commit frame compaction**

```bash
git add shared/ui-density.css assets/home.css apps/*/runtime/tokens/base.css apps/*/runtime/frame/app-frame.css
git commit -m "feat(ui): compact InkDOS frame in desktop density"
```

---

### Task 5: Add cross-workspace browser regression for detection, overrides, and geometry

**Files:**
- Create: `tests/test_ui_density_browser.py`
- Modify if needed: `tests/test_cross_suite_stability_browser.py`

**Interfaces:**
- Consumes: seven entry surfaces and shared density authority.
- Produces: measurable proof that chrome changes while content geometry does not.

- [ ] **Step 1: Test Auto Desktop**

Launch 1360x900 page with fine pointer/hover context; assert `data-ui-density=desktop` and a representative frame control height is materially smaller than current Mobile target.

- [ ] **Step 2: Test Mobile/forced override**

Use narrow/touch context and assert Auto resolves Mobile. Force Desktop then Mobile through the visible control and assert localStorage + root attribute change without navigation.

- [ ] **Step 3: Test persistence across workspaces**

Set forced Mobile in Documents, navigate to Spreadsheets/Presentations and assert the same preference is selected/effective. Return Auto and verify automatic resolution again.

- [ ] **Step 4: Assert internal geometry stability**

For representative Documents, Spreadsheets, Presentations, PDF, TXT, and EPUB state, capture content geometry/zoom before and after Desktop↔Mobile switch; assert only frame/chrome dimensions change.

- [ ] **Step 5: Run browser matrix**

```bash
BROWSER=chromium python tests/test_ui_density_browser.py
BROWSER=firefox python tests/test_ui_density_browser.py
BROWSER=webkit python tests/test_ui_density_browser.py
```

Expected: PASS.

- [ ] **Step 6: Run cross-suite stability browser test**

```bash
BROWSER=chromium python tests/test_cross_suite_stability_browser.py
```

Repeat on Firefox/WebKit at the intervention checkpoint.

- [ ] **Step 7: Commit browser coverage**

```bash
git add tests/test_ui_density_browser.py tests/test_cross_suite_stability_browser.py
git commit -m "test(ui): cover adaptive density across workspaces"
```

---

### Task 6: Record green density checkpoint and advance to Presentations plan

- [ ] **Step 1: Re-run density contract + browser matrix on exact head**
- [ ] **Step 2: Confirm no unexpected network access and PWA shell contains shared assets**
- [ ] **Step 3: Record exact SHA/test evidence; do not perform the final intervention integrity refresh yet**
