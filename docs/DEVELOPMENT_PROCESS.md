# InkDOS Development Process v1

## Why this process exists

InkDOS is a local-first suite with six workspaces and multiple delivery surfaces (browser/PWA plus Tauri desktop). A small visual or shell change can therefore affect layout, file handling, updater behavior, cache/version state, or a different WebKit/Chromium rendering path.

The development process must make regressions difficult to introduce and easy to isolate. Passing static string/structure contracts is necessary but is not sufficient evidence that the product still renders and behaves correctly.

## Failure modes this process removes

1. **Multiple writers on the same target.** Only one development controller may advance a given candidate at a time. Parallel autonomous workers must not independently mutate overlapping source or release state.
2. **Stale version-specific workers.** Automation instructions must derive the target from live repository state, not from a hard-coded historical version.
3. **Direct development on main.** Product changes are developed on a branch and enter main through a PR after exact-head CI.
4. **Product and release-control changes mixed together.** App/runtime changes must not modify release workflow, release authorization, release trigger, or desktop version surfaces in the same PR.
5. **Static-only confidence.** UI changes require rendered-browser evidence. Mobile/touch-sensitive changes require WebKit coverage before merge.
6. **Moving release candidates.** Once a release candidate is selected, its commit SHA is immutable. A failed gate creates a new candidate SHA; it does not silently redefine the old one.
7. **Release workflow surgery during publication.** Release infrastructure changes are developed and validated separately from a product release.
8. **Version-named CI.** Permanent CI describes capability, not a historical release number.

## Branch model

- `main`: deployable integration branch. No autonomous direct product edits.
- `fix/*`, `feat/*`, `refactor/*`: one scoped product change.
- `process/*`: CI, tests, developer tooling, and process changes only.
- `release/*`: release metadata only. No app/runtime behavior changes.
- `preview` (optional): movable pointer to an exact PR head for visual QA; never a release authority.

One PR should have one primary failure mode. Related files may change together when they are required to fix that failure mode, but unrelated workspace cleanup is deferred.

## Required evidence ladder

Every product change advances in this order:

1. **Reproduce** — record the exact failing behavior and environment. For UI regressions, capture the rendered state or a deterministic browser probe.
2. **RED regression test** — add a test that fails for the observed defect whenever practical. A visual defect must not be represented only by a source-string assertion.
3. **Smallest fix** — change the narrowest implementation surface that addresses the reproduced cause.
4. **Focused validation** — run the app/workspace-specific tests.
5. **Cross-workspace validation** — run suite contracts, app-isolation/privacy checks, and browser smoke.
6. **Browser matrix** — Chromium is required for all product PRs; WebKit is required for layout, touch, viewport, toolbar, rendering, file-picker, and Safari/iOS-relevant changes.
7. **Exact-head PR gate** — CI must be green on the exact commit that will merge.
8. **Visual QA when appearance changed** — preview must point to that exact head. Feedback creates a new commit and repeats the gate.
9. **Merge** — only the validated head enters main.

A passing earlier checkpoint never substitutes for validation of a later commit.

## Change-boundary rule

Product code and release control are separate transactions.

A PR that changes product/runtime files (`apps/**`, `shared/**`, or the desktop host bridge) must not also change:

- `.github/workflows/release.yml`
- `config/release-authorization.json`
- `config/release-trigger-*`
- `VERSION.json`
- `desktop/src-tauri/tauri.conf.json`
- `desktop/src-tauri/Cargo.toml`

Release/version changes happen only after the product change is merged and green on main. This prevents a product regression from being entangled with publication mechanics and prevents release fixes from changing the product candidate.

## Release process

Release is a separate state machine:

`MAIN_GREEN -> RC_SELECTED -> RC_VALIDATED -> BUILT -> BUNDLE_VALIDATED -> PUBLISHED -> POST_RELEASE_CHECK`

Rules:

- RC selection records one immutable commit SHA.
- Build and provenance always use that SHA.
- Any source, test, workflow, or metadata edit after RC selection invalidates that RC and requires a new SHA.
- Release workflow changes are never made inside an active product release attempt.
- All platform artifacts must originate from the same SHA and the same workflow run.
- Publication is the last mutation, after validation, signing, artifact inventory, hashes, updater manifest, and authorization.
- A failed publication must preserve already-built evidence and report the infrastructure failure without pretending the release exists.
- Post-release checks verify the public tag/release, asset inventory, `latest.json`, and updater target.

## Hotfix path

A hotfix is faster, not weaker:

1. reproduce the production defect;
2. add a targeted regression test in the affected engine/browser;
3. fix on `fix/*`;
4. run the same exact-head browser and contract gates;
5. merge;
6. make a separate release-metadata transaction;
7. publish from the frozen commit.

For a Safari/WebKit defect, WebKit is mandatory. For a desktop updater defect, desktop/updater contracts are mandatory.

## Automation model

Use **one development controller**, not three concurrent writers plus a guard.

The controller may:
- inspect live main, open PRs and CI;
- continue exactly one active implementation branch;
- create/update the PR;
- run/fix tests on that branch;
- merge only an exact-head green PR when the requested scope is complete.

The controller must not:
- push product changes directly to main;
- modify a release workflow while a release is active;
- advance a stale version-specific workspace;
- merge overlapping competing fixes;
- treat static contract PASS as rendered UI validation.

Release monitoring is a separate role and is enabled only for an explicitly authorized release.

## Definition of done

A change is done only when the original reproduction is no longer reproducible, the regression test is permanent, required Chromium/WebKit/desktop gates are green, the exact merged SHA is known, and no unrelated release-control mutation was bundled with it.
