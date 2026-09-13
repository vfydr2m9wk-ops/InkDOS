# Update model

The 2.0 migration package uses `mode: full-snapshot`.

The updater creates a candidate tree from the package payload only. It does not copy any 1.x runtime file into the candidate. The sole inherited repository path is `.github/workflows/`, because the currently installed workflow is the protected bootloader that applies the package and is forbidden from being modified by an update ZIP.

The candidate is fully validated before the real checkout is changed. On apply, every old repository file not present in the 2.0 snapshot is removed, except `.git`, `.github/workflows/`, and the root update ZIP that the workflow itself removes after a successful transaction.

Future packages may use `mode: incremental` and must still provide `files/scripts/apply_update_package.py` because the protected workflow extracts the updater from the package before execution.

## 2.0.3 PDF package

Incremental update: previous sequence 70 / version 2.0.2 → sequence 71 / version 2.0.3. The payload includes the unchanged transactional updater and updated six-app validation contracts. It does not modify workflows or permission controls. The old tests/test_suite_integration.py moves to scripts/validate_suite_contracts.py, retaining its release checks with PDF now active. No PDF test fixtures are installed.
