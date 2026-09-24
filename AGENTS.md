# InkDOS AI maintenance rules

InkDOS is maintained with AI-written code and human audit. Optimize for correctness, small diffs, reproducibility and low-context maintenance.

## Read order

For ordinary work, do not reconstruct the whole project.

1. Read this file.
2. Run `python scripts/agent_context.py <component>`.
3. Inspect only the files and symbols needed for the task.
4. Read broader architecture/history only when the task actually crosses those boundaries.

The component map in `config/components.json` is the machine-readable source for normal component scope.

## Preservation-first rules

- Preserve working code unless a reproduced defect or explicit requirement requires a change.
- Do not refactor for aesthetics, modernization, deduplication or style alone.
- Do not rename stable functions, commands, storage contracts or files without a functional reason.
- Do not perform opportunistic cleanup while fixing an unrelated issue.
- Prefer disconnecting or hiding temporarily unnecessary behavior over deleting working implementation.
- Deliberate local duplication is acceptable when it reduces cross-application coupling.
- Never change a sibling application merely to make implementations look consistent.
- Do not edit vendor/minified files unless the defect concerns that dependency.
- Search for a symbol or narrow range before reading a large file in full.
- Historical plans and release archaeology are not required for an ordinary component-local repair.

## Component isolation

The normal unit of work is one component: `hub`, `documents`, `spreadsheets`, `presentations`, `txt`, `epub` or `pdf`.

A component-local task should normally modify only:
- that component's owned paths;
- regression tests matching that component;
- explicitly authorized extra paths.

Cross-component edits require a demonstrated technical dependency and should be called out in the task result.

A workspace must remain usable without depending on another workspace. The Hub may launch workspaces, but editor/runtime state must remain app-owned.

## Frozen legacy

`INKDOS:FROZEN-LEGACY` means deliberately preserved code that is not part of the preferred current flow.

Frozen legacy:
- is not dead-code cleanup material;
- must not be deleted, renamed, modernized or refactored incidentally;
- may remain physically in place to preserve proven work and future reactivation options;
- may be changed only when the task explicitly authorizes the relevant frozen-legacy ID.

Registry: `config/frozen-legacy.json`.

Do not mark large areas as frozen merely to avoid maintenance. Freeze only deliberate compatibility or temporarily inactive integration surfaces.

## Minimal workflow

For a component repair:

```text
python scripts/agent_context.py <component>
# reproduce the problem
# make the smallest correct change
python scripts/agent_test.py <component>
python scripts/agent_verify.py <component> --base main
```

Use `--browser` when the change affects rendered/interactive behavior and the local environment supports browser tests.

`scripts/run_release_validation.py` remains the full integration/release gate. Do not run or reinterpret the entire release suite after every small edit unless the task requires it.

## Version and release discipline

- `VERSION.json` is the global product-version authority.
- Do not bump versions on ordinary repair branches.
- Do not rewrite changelogs repeatedly during intermediate repair work.
- Stable baselines belong in immutable tags/releases, not permanent release branches.
- Branches are temporary work surfaces and should be removed after their work is integrated.
- A global version may contain a change to only one application; unchanged applications should remain byte-stable whenever practical.

## Task result format

Finish implementation work with a compact audit record:

```text
Component:
Baseline:
Files modified:
Reason:
Regression test:
Component tests:
Isolation/scope:
Sibling apps modified:
Frozen legacy modified:
Manual audit still needed:
Known remaining issue:
```

The human maintainer audits the result. Make the audit easy: report what changed, not a long narrative of everything inspected.
