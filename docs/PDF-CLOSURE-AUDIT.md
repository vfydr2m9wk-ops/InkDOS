# PDF closure and integration audit — 2.0.3

Status: **FUNCTIONAL BASELINE FROZEN / DISTRIBUTION INTEGRATED**.

Baseline: user accepted P4.2 as working perfectly. This closure preserves the accepted editor/IO/engine bytes and adds only the requested entry UI plus distribution cleanup. New browser/device testing of the Home/start-card integration was not available; automated entry-behavior and release-contract checks cover its wiring. This status does not claim independent security certification.

## Confirmed scope

- Physical separation: PDF runtime, viewport adapter, engine/session, UI, IO, view, PDF.js adapters and extensions exist as separate files under apps/pdf. Each owns the responsibilities documented in ARCHITECTURE.md.
- Independent operation: all PDF script/style/icon/worker resources are local to apps/pdf. No required sibling-app or Home runtime import. Home is an ordinary return link, not a dependency of PDF opening, annotation or saving.
- Privacy: no user file, screenshot, source-document content, synthetic PDF fixture or internal test directory enters the update payload. Only theme preference is persisted by first-party PDF code; source documents remain local in memory. No first-party document upload or analytics path was found. Vendor notices remain intact.
- Cleanup: the __inkdosPdfP4 global inspection hook is removed from the distribution. Constructors required for app composition remain in the app-local namespace; no live document/session instance is exported through the test hook.
- Integration: Home's existing disabled PDF card becomes an anchor, and the PDF header gains the same house SVG/Home route as EPUB. First-open state uses a centered card and red Open PDF button. The app's own file input performs opening.
- Integrity: no editor, save, worker, policy, page layer, extension, toolbar or appearance module changes from accepted P4.2. Prior native save/reopen and lifecycle checks are preserved as audit evidence outside the distribution.
- Lock: SOURCE_LOCK.json adds the PDF source and integrated digests; hashes for every other app are unchanged. The five-app prohibition is replaced by explicit six-app expectations, not disabled validation. Protected workflow bytes remain unchanged.
- Packaging: incremental transactional format with SHA-256 declarations, exact base version/sequence, full validation profile and deletion list. No shared legacy runtime is introduced.

## Evidence and limitations

Executed: JavaScript syntax for PDF sources and inline entry script; entry-state behavior (initial/cancel/failure/success); PDF dependency closure; full release validation and checksums; transactional dry-run and application to a scratch copy; unchanged hashes for five sibling apps and all unchanged PDF functional modules. See the accompanying package validation record.

The accepted P4.2 audit exercised actual native PDF serialization/reopening for forms and all five annotation types, repeat export, undo-all export and source-byte prefix protection. Device acceptance is user-reported. No PDF was loaded from a user library or screenshot to construct the app. Automatic dependency advisory lookup was not completed in this environment; PDF.js remains pinned with isEvalSupported:false and form scripting disabled. No claim of comprehensive vulnerability clearance is made.
