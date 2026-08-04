# Compatibility Policy

## Meaning of support

A feature is "supported" only when its basic workflow is implemented and covered by a reproducible test. Support does not mean pixel-identical rendering with Microsoft Office.

## Compatibility levels

- **Core:** part of the focused MVP and covered by release criteria.
- **Best effort:** parsed or rendered when possible, but not guaranteed across producers.
- **Unsupported:** intentionally outside the current scope.

## File producers

OOXML files can differ depending on the application and version that created them. Bug reports should include the producer, approximate version, host browser, operating system and whether the project ran over `https://` or `file://`.

## Failure behavior

Unsupported content should be reported, skipped without corrupting unrelated content, or cause a clear error. Silent data loss is considered a high-priority bug.

## Export behavior

Saving produces a new copy. Users should retain the original file and verify the exported result before relying on it.


## Legacy Excel import policy

Direct `.xls` support is an import-and-convert path, not a binary round-trip claim. Supported BIFF8 content is decoded locally and saved only as `.xlsx`. The application must warn whenever formulas or unsupported legacy objects can only be represented by cached values or omitted during conversion.
