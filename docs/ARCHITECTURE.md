# InkDOS architecture contract

InkDOS is a local-first suite composed of six physically independent workspaces: Documents, Spreadsheets, Presentations, PDF Workspace, Plain Text and EPUB Reader. Home is a launcher and optional navigation bridge; it is not a functional runtime, editor engine or file router.

## Physical ownership

Each workspace owns its complete functional stack below `apps/<workspace>/`, including its engine/model, state, I/O, UI, view code and any third-party vendor dependencies it requires. A workspace must remain usable when extracted with its own files and served independently. Functional modules must not be placed in repository-level `shared/`, `runtime/` or `vendor/` trees.

Deliberate duplication between apps is acceptable and preferred when it preserves failure isolation. Two workspaces needing equivalent behavior does not justify a shared functional engine.

## Cross-workspace boundary

Runtime references from one `apps/<workspace>/` tree into a sibling `apps/<other>/` tree are forbidden. The only suite-level relationship normally permitted from an extracted app is the optional Home navigation target. Appearance may exchange a preference value, but the implementation and fallback behavior remain app-local.

External libraries must have compatible licenses, preserve required notices, work entirely client-side/offline, avoid telemetry and live inside the app that consumes them.

## Functional-cycle rule

Only one workspace may receive functional changes in a development cycle. The active workspace and phase are recorded in `FUNCTIONAL_STATE.json`. During that cycle:

- functional code changes are limited to `apps/<active-workspace>/**`;
- sibling workspace trees are frozen unless an objective regression explicitly reopens a prior baseline;
- Home (`index.html`, root `assets/` and launcher presentation) is frozen;
- global changes are limited to tests, validation/workflow infrastructure, documentation, integrity metadata and the service-worker shell when required to expose app-local resources offline;
- aesthetics are not redesigned as part of a functional increment.

The phase-scope validator compares the branch against `main` and rejects sibling-app edits, shared functional/runtime roots and Home changes.

## UI contract

Functional additions must reuse the existing workspace frame and interaction hierarchy: existing toolbar first, then toolbar popover/menu, then contextual side panel, and the hamburger menu only for global functions. New permanent bars or cross-app UI frameworks are not introduced during functional cycles.

## Local-first and save integrity

No functional workspace requires a backend or telemetry service. Open, edit, search, conversion and supported save/export paths execute client-side. Generated modern formats must be validated by format-aware tests where practical, and supported edit flows must include open → edit → save → reopen coverage before a baseline is frozen.

The service-worker application shell may enumerate resources from all six apps, but this is distribution metadata rather than a shared runtime. Each enumerated resource remains physically owned by its workspace.

## Transition gate

Before a phase may be integrated or the next phase may start, the pre-phase architecture audit must pass. It performs:

1. diff hygiene against `main`;
2. one-workspace phase-scope enforcement;
3. clean-snapshot repository, source, checksum, service-worker, suite-contract and physical-isolation validation;
4. browser round-trips for frozen authoring baselines that have executable regression fixtures.

A failing transition audit blocks phase advancement. The correction cycle is audit → isolate cause → minimal app-local correction → regression tests → full transition audit → freeze.

## State and historical package metadata

`DEVELOPMENT_STATE.json` and historical package/version metadata describe the earlier packaged release lineage and are not used as the functional-roadmap source of truth. `FUNCTIONAL_STATE.json` tracks the staged home-use roadmap and the active workspace. `SOURCE_LOCK.json` and `CHECKSUMS.sha256` continue to provide integrity evidence for the current repository snapshot.

## Freeze discipline

Frozen baselines are recorded in `docs/FROZEN_BASELINES.md`. A frozen workspace receives no new functional work outside its scheduled phase unless a reproducible regression requires reopening it. The final objective is stable domestic coverage with physical modularity and predictable round-trip behavior, not maximum feature count.
