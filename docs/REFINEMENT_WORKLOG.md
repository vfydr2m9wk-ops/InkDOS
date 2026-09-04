# InkDOS refinement worklog — checkpoint 1

## Baseline

- Source commit: `f7574135d8c24b6ba9ee017f4f49e963f74fffc7`.
- Source package: `1.0.0-beta.5`.
- Source sequence: `61`.

## Included in checkpoint 1

- Centralized production app identity/actions/extensions in module manifests and module runtime.
- Added central metadata-only RecentFilesService with deduplication, filtering, clear/remove and optional local handle persistence.
- Added shared App Launcher and separate Settings surface.
- Converted active Home to Recent-first layout with registry-derived filters and empty/list states.
- Added shared AppHome renderer for all six apps; PDF and EPUB remain Open-only.
- Added shared launcher/AppHome responsive surfaces with safe-area and reduced-motion handling.
- Added new shared assets to service-worker precache.
- Preserved existing dirty-state/recovery behavior and native file inputs.

## Deliberately excluded

- Unfinished cross-page handoff and incompatible-format offer from Phase 5.
- Editor-wide overflow/mobile-toolbar work from Phase 6.
- Complete editor theme-token unification from Phase 7.
- Final required viewport matrix and release packaging QA from Phase 8.

## Evidence carried into this checkpoint

- Phase 4 full unit suite: 386/386 PASS.
- Repository validation: PASS.
- Source audit: PASS.
- Architecture guardrails: PASS.
- Legacy/branding scan: PASS.
- Home, Launcher and AppHome Chromium refinement regressions: PASS.

The checkpoint ZIP SHA-256 is recorded outside this file after deterministic packaging.
