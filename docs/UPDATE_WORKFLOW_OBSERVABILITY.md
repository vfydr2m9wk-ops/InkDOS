# Update workflow observability

InkDOS keeps update diagnostics in the permanent incremental workflow rather
than in one-off package workflows.

## Failure reporting

The workflow captures updater output and writes an Actions summary containing:

- package label and sequence;
- validation status;
- package SHA-256;
- applied commit when one was produced;
- copied/replaced/deleted path counts;
- transaction errors and relevant log tails on failure;
- Pages rebuild status after a successful update commit.

The updater also writes a JSON report when `--report` is supplied.

## Workflow immutability

GitHub Actions executes the workflow definition that existed when the run
started. Update packages therefore cannot safely self-modify workflow behavior.
The stable policy is stricter: packages are permanently forbidden from creating,
modifying or deleting `.github/workflows/`.

Workflow changes are installed as a one-time manual bootstrap through a normal
repository commit. The permanent workflow is:

```text
.github/workflows/apply-inkdos-update.yml
```

The workflow extracts `files/scripts/apply_update_package.py` from the selected
ZIP before applying it, allowing updater improvements to travel with a package
without granting the package permission to modify workflow definitions.
