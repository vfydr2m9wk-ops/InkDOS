# Release Criteria

## Blocking conditions

A release must not be tagged when:

- create/open/export is broken in any component;
- an exported synthetic fixture cannot be reopened;
- the quality gate fails;
- a known change can silently discard unrelated user content;
- the release documentation overstates compatibility;
- a required third-party notice is missing.

## Feature freeze

While a blocking regression exists, new format features should not be merged. Cleanup, tests, documentation and narrowly scoped bug fixes take priority.

## Versioning

- `0.x`: experimental, internal models can change;
- release candidate wording is avoided until repeatable browser tests exist;
- `1.0` requires defined core workflows, public regression fixtures and a documented compatibility baseline.
