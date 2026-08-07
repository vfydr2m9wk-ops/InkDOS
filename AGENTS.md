# InkDesk agent and contributor guardrails

These rules apply to AI-assisted and human changes in this repository. They are
intended to keep InkDesk local-first, build-free at runtime, modular, visually
consistent, and safe to refactor without silently changing behavior.

## 1. Scope first

- Make the smallest change that owns the behavior.
- Do not edit unrelated workspaces to solve a local defect.
- Do not combine a refactor with a feature addition unless the behavior change
  has its own regression test and its own clearly identified commit/package.
- During the 0.20.x refactoring sequence, moving code does **not** authorize a
  UI redesign, a new format, or a new editing command.

## 2. Behavioral preservation

Before extracting or moving runtime code:

1. identify the current user-visible behavior;
2. ensure a behavioral regression test exists for it;
3. perform the extraction;
4. rerun the same test and the full release gate;
5. treat any unexplained difference as a regression.

Open, Save/export, rename, dirty state, Undo/Redo, selection, recovery, Home,
presentation mode and offline launch are release-blocking behaviors.

## 3. Module ownership

Use feature-oriented modules rather than new catch-all files.

- `apps/<workspace>/` owns behavior specific to one workspace.
- `shared/` owns behavior genuinely reused by multiple workspaces.
- `modules/` owns application registration/loading metadata, not editor state.
- A workspace must not import runtime code from another workspace.
- Shared code must not depend on a workspace implementation.
- Avoid circular imports.

Prefer a small composition/controller entry point plus focused modules such as
`state/`, `ui/`, `editing/`, `io/`, or another name that describes a real
responsibility. Do not create empty abstraction layers or placeholder bridges.

## 4. File-size and readability ratchet

`architecture-policy.json` is enforced by
`scripts/check_architecture_guardrails.py`.

- New runtime JS/CSS files should stay at or below 500 physical lines.
- New/refactored runtime source should not contain physical lines over 240
  characters. Split generated-looking one-line functions into readable code.
- Existing oversized/compressed files are grandfathered only at their recorded
  baseline. They may shrink, but they may not grow beyond that baseline.
- Do not add a new exception merely to make CI green. A new exception requires
  an explicit architectural reason in documentation and review.

## 5. JavaScript style and object orientation

InkDesk does not require React or a framework migration. The runtime remains
plain HTML/CSS/JavaScript unless a future architecture decision explicitly
changes that.

Use classes when an object has meaningful state and lifecycle (for example a
document session, history manager, recovery store, renderer or controller).
Use small modules and pure functions for transformations and stateless logic.
Do not introduce inheritance or manager/factory classes only to claim OOP.

## 6. Visual contract

Preserve the established InkDesk visual system:

- native Apple/system font stack; no bundled font files;
- professional dark/light-capable desktop-style surfaces with rounded controls;
- 44 px shared title-bar baseline where the workspace uses the common shell;
- Documents blue, Spreadsheets green, Presentations orange, PDF red,
  EPUB purple and TXT yellow identities;
- existing button names, functions and application-specific controls;
- content-first default panel states documented in `docs/VISUAL_SYSTEM.md`.

Do not add decorative controls, invented operating-system window chrome, or
Microsoft/Apple proprietary assets. A refactor must not move controls unless the
task explicitly calls for a UI change.

## 7. Local-first and file safety

- User documents remain local unless a future explicit integration says
  otherwise.
- Do not introduce a backend, telemetry, automatic remote runtime dependency or
  mandatory build service.
- Preserve package-preserving OOXML behavior where supported.
- Never clear dirty state or recovery data before a save/export has succeeded.
- Failed replacement opens must leave the active document intact.

## 8. Tests are evidence

A button existing in HTML or having an event listener is not proof that it
works. Prefer behavioral tests that verify the resulting state or exported
file. Keep the functional acceptance matrix honest: unverified controls stay
scheduled rather than being assumed functional.

Every fixed regression receives a permanent test when technically feasible.
The release gate includes repository validation, architecture guardrails,
source audit, unit/package tests, browser regressions and checksums.

## 9. Update-package safety

Incremental update ZIPs must never create, modify or delete
`.github/workflows`. The stable workflow is bootstrapped separately. Preserve
transactional rollback, sequence checks and checksum verification.
