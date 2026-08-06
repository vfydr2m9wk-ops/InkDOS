# Update workflow observability

Development sequence `0.19.4.10` improves the incremental update workflow after
two rolled-back attempts. Neither attempt consumed sequence 10, and the
repository remained at sequence 9 after each transaction.

## First reverted attempt

The first failure was
`test_index_loads_helper_before_application`. The test required the literal
`app.js?v=0.19.4.6` after a package advanced the PDF script version.

The test was changed to verify script order without pinning a query-string
version.

## Second reverted attempt

The second failure was
`test_only_synthetic_fixtures_are_bundled`.

The package had copied:

```text
tests/fixtures/patch-manifest-0.19.4.10.json
```

The repository deliberately restricts `tests/fixtures` to seven synthetic
Office and PDF documents. Package metadata and workflow observations do not
belong in that directory.

The JSON fixture has been removed. The observation remains in the root
`patch-manifest.json` and in this document.

## Workflow failure summary

Future workflow runs capture the complete updater output, retain the updater
exit code, and add a failure summary containing:

- package label and sequence;
- explicit rollback confirmation;
- repository sequence after rollback;
- the updater's transaction error;
- the last transaction log lines;
- automatic recognition of stale exact asset-version assertions;
- automatic recognition of forbidden update metadata in `tests/fixtures`;
- clarification that a missing `generate_release_metadata.py` line may come
  from the intentional rollback test rather than the final failure.

The permanent updater writes a JSON failure report when possible. A failed run
remains failed in GitHub Actions, while the summary explains which error caused
the rollback and confirms that no sequence was consumed.

## Activating the improved diagnostics before sequence 10

GitHub Actions executes the workflow definition that existed when the run
started. A workflow copied by an update package cannot change the behavior of
that same running job.

For the enhanced summary to be active during the next attempt, replace
`.github/workflows/apply-inkdesk-update.yml` with the standalone workflow
provided alongside the corrected ZIP before triggering the Action.

That workflow prefers `files/scripts/apply_update_package.py` from the selected
ZIP. This allows the package's failure-report support to be used immediately,
while retaining the repository updater as a fallback for packages that do not
include one.
