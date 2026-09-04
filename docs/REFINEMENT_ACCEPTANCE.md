# InkDOS refinement acceptance matrix — checkpoint 1

Baseline: `f7574135d8c24b6ba9ee017f4f49e963f74fffc7` (`1.0.0-beta.5`, sequence 61).
Checkpoint target: `1.0.0-beta.5`, sequence 62.

This checkpoint intentionally freezes the verified navigation/Home/Launcher/AppHome work before the remaining editor-responsiveness, global-theme and final QA phases. PASS means evidence exists; PARCIAL means later phases still own part of the criterion.

| # | Criterion | State | Evidence / scope |
|---:|---|---|---|
| 1 | Home has no visible giant app catalog | PASS | Runtime Home removes the legacy catalog before interaction; Chromium refinement test. |
| 2 | Home is centered on Recent files | PASS | Runtime Home makes Recent the primary content. |
| 3 | Recent filters remain usable | PASS | Registry-derived All + six app filters; Chromium refinement test. |
| 4 | Clear Recent disappears when empty | PASS | Empty/populated/clear states covered. |
| 5 | Global Open/Create do not dominate Home | PASS | Legacy hero is removed at runtime; only discreet empty-state Open remains. |
| 6 | Real grid app launcher exists | PASS | Registry-derived six-app grid; desktop/mobile keyboard QA. |
| 7 | Launcher and Settings are separate | PASS | Separate app grid and Settings surface. |
| 8 | Theme is global | PARCIAL | Shared preference/state exists; complete editor token unification belongs to Phase 7. |
| 9 | No cramped native theme select in active UI | PASS | Settings uses radio/segmented choices; legacy sidebar is removed before interaction. |
| 10 | Launcher is available in apps | PASS | Shared shell injects launcher trigger into all six app pages. |
| 11 | Mobile AppHome is a normal page | PASS | Shared AppHome, tested portrait and landscape. |
| 12 | Desktop AppHome uses available width | PASS | Shared AppHome uses up to 1180 CSS px. |
| 13 | AppHome never exceeds viewport | PARCIAL | Verified at representative mobile/landscape/desktop sizes; full mandated width matrix remains Phase 6/8. |
| 14 | Editors never exceed viewport | NÃO TESTADO | Phase 6. |
| 15 | Toolbars have dedicated mobile composition | NÃO TESTADO | Phase 6. |
| 16 | Long titles do not break toolbars | PARCIAL | Existing ellipsis behavior remains; full editor matrix is Phase 6. |
| 17 | File picker stays native/local | PASS | Existing native file inputs are retained. |
| 18 | Apps limit file formats appropriately | PASS | `accept` derives from the central module registry. |
| 19 | Incompatible formats are handled without crash | PARCIAL | Registry/router rejects mismatches; cross-app offer belongs to Phase 5 continuation. |
| 20 | Recent files route to correct module | PARCIAL | Recent metadata owns `appId`; end-to-end page handoff remains Phase 5 continuation. |
| 21 | Read-only apps do not invent creation | PASS | PDF/EPUB capabilities expose Open only. |
| 22 | Bottom sheets respect safe area | PASS | Launcher mobile sheet uses safe-area bottom inset. |
| 23 | Dynamic viewport is used appropriately | PARCIAL | Shared Launcher/AppHome use `dvh`; editor-wide verification is Phase 6. |
| 24 | Institutional links do not occupy active mobile Home | PASS | Active Home removes the footer links; they live in Settings. |
| 25 | No unnecessary duplicate navigation | PARCIAL | Active UI has Home + Launcher + AppHome roles; legacy static fallback markup remains in this checkpoint for compatibility and will be sanitized later. |
| 26 | Desktop remains primary experience | PASS | Desktop layouts are preserved as reference. |
| 27 | Mobile is not merely compressed desktop | PARCIAL | Home/Launcher/AppHome have mobile compositions; editor toolbars remain Phase 6. |
| 28 | Dirty state is not discarded silently | PASS | Existing lifecycle/recovery guards remain unchanged. |
| 29 | Light/dark share structure | PARCIAL | Shared shell structure is theme-invariant; full editor tokens are Phase 7. |
| 30 | Application remains usable offline | PASS | New shared shell assets are added to service-worker precache. |

## Checkpoint gates

- Prior Phase 4 candidate: 386/386 unit tests PASS; repository validation PASS; source audit PASS; architecture guardrails PASS; legacy/branding scan PASS.
- Chromium refinement regressions for Home, Launcher and AppHome: PASS in the prior candidate.
- This ZIP is a checkpoint that intentionally excludes unfinished Phase 5 cross-page handoff work and all Phase 6–8 work.
- GitHub Actions remains the independent final gate when the package is applied.
