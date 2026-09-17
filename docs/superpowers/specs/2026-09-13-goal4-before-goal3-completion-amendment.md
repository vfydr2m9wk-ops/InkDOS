# InkDOS 2.3 Goal 4 Order Amendment

**Status:** USER-APPROVED — 2026-09-13

## Decision

The user explicitly reordered the remaining InkDOS 2.3 work so the manual desktop updater is implemented before Goal 3 native packaging is fully closed.

Goal 3 is paused at checkpoint `c68566ee53010784f63aa915ef1eea575c9762b0`. All Goal 3 work at and before that checkpoint must be preserved. An already-running exact-head native checkpoint may finish and its evidence may be retained, but no additional Goal 3 packaging, launcher, association, or installer fixes are to be made while Goal 4 implementation is active.

## Temporary execution order

1. Preserve Goal 3 at `c68566ee53010784f63aa915ef1eea575c9762b0`.
2. Implement Goal 4 manual desktop updater to the strongest valid pre-packaging checkpoint.
3. Return automatically to Goal 3 without resetting away Goal 4 commits.
4. Finish Windows, Linux, and macOS native packages and package inspection.
5. Run installed end-to-end updater validation using the finalized Goal 3 desktop packages.
6. Refresh integrity metadata and complete final InkDOS 2.3 validation/release.

## Goal 4 invariants

- Desktop/Tauri only. Web and PWA remain updater-free.
- No startup update check, timer, polling loop, background network request, automatic download, or automatic install.
- Network access for update discovery occurs only after an explicit `Check for updates` user action.
- Installation occurs only after an explicit `Install` confirmation.
- The UI reports installed and available versions, release notes when an update exists, and a clear current-version state when no update exists.
- The implementation uses the official Tauri v2 updater path where compatible with the existing static-web/Tauri architecture.
- Update metadata, downloaded artifacts, and signatures remain inside a fail-closed trust boundary.
- Signing private material must never be committed. Public verification material may be embedded in the application.
- GitHub release automation must produce updater artifacts and static update metadata from the same tagged source used for native installers.
- The existing local-first, no-backend, no-telemetry architecture remains unchanged.

## Validation boundary

Goal 4 may be declared **IMPLEMENTATION COMPLETE — PRE-PACKAGING VERIFIED** once its code, desktop-only UI behavior, updater configuration, trust-boundary tests, release metadata generation, and non-installed integration tests are green.

It must not be declared **END-TO-END VERIFIED** until Goal 3 resumes, final native packages are produced, and an installed older version successfully discovers, verifies, installs, and transitions to the newer signed version through the manual updater flow.