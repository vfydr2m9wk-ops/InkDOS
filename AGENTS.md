# InkDOS engineering policy

These rules apply to human and AI-assisted changes.

## Current-state first

Git and GitHub own project history. The active tree should contain only code, tests and documentation that serve the current product. Do not keep obsolete wrappers, aliases, migration notes, dormant features or version-specific patch layers merely because they existed before.

When a rewrite is smaller, clearer or safer than preserving inherited implementation, rewrite it. Compatibility means preserving supported user behavior, file fidelity and recoverable local data — not preserving internal names or architecture.

## Optimize for value per complexity

Prefer solutions that increase useful format coverage, reliability, accessibility or interaction quality while reducing files, requests, duplicate logic and special cases. One authoritative implementation is better than several correction overlays. New abstraction is justified only when it removes more complexity than it adds.

## Patch policy

Prefer fewer, broader fixes that remove root causes and adjacent debt. Every substantial patch must be exercised first against a disposable candidate tree. The publication workflow is the final independent gate, not the primary debugging environment.

A patch may refactor aggressively when validation covers the affected behavior. Do not mix speculative features into a stabilization change.

## Product invariants

- local-first, offline-capable and private by design;
- no telemetry, account or cloud dependency for core workflows;
- imported files are untrusted input;
- supported DOCX/XLS/XLSX/PPT/PPTX/PDF/TXT/EPUB behavior must not regress silently;
- saving must not silently overwrite a selected source;
- recoverable unsaved work and transactional document replacement take precedence over convenience;
- UI must remain visually coherent, keyboard-accessible and predictable across supported viewport classes;
- runtime stays build-free: source is directly serveable as static files.

## Tests

Tests should express current behavior and safety contracts. Remove tests that only freeze historical implementation details, and replace them with direct behavior or architecture assertions. Keep browser regressions for interactions that cannot be proved statically.

## Documentation

Document the current product. Historical rationale belongs in Git commits, pull requests and releases. Avoid duplicating the same contract across several documents.
