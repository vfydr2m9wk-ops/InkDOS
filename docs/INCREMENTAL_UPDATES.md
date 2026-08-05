# Incremental InkDesk updates

InkDesk 0.19.4 is developed as an ordered sequence of small update packages. The packages modify only the files required by one milestone and are applied by a manually triggered GitHub Actions workflow.

## Why the package label has four numbers

Development packages use labels such as `0.19.4.1`, `0.19.4.2`, and `0.19.4.3` to preserve their required order. These labels are update-sequence identifiers, not published application versions. The public application version remains unchanged during the sequence and becomes `0.19.4` only after final consolidation and validation.

The current sequence is recorded in `DEVELOPMENT_STATE.json`.

## First installation

The first package bootstraps the permanent updater. Add these two files to the repository:

1. `.github/workflows/apply-inkdesk-update.yml`
2. `InkDesk-update-v0.19.4.1.zip` in the repository root

Then open **Actions**, choose **Apply InkDesk update package**, select **Run workflow**, and leave `package_name` empty when the root contains only one matching update ZIP.

The workflow removes the committed update ZIP after application, validates the repository, and creates a new commit containing only the applied changes and regenerated metadata.

## Later packages

For `0.19.4.2` and later, upload only the new root ZIP and run the existing workflow. Packages must be applied in sequence. A skipped or repeated package is rejected before repository files are changed.

## Package format

```text
InkDesk-update-v0.19.4.N.zip
├── patch-manifest.json
├── files/
│   └── repository-relative files to add or replace
└── DELETE.txt                 # optional
```

`DELETE.txt` contains one repository-relative path per line. Empty lines and lines beginning with `#` are ignored.

## Transaction and rollback

The updater performs these operations:

1. validates the ZIP structure, paths, limits, manifest, base version, and sequence;
2. stages the package in a temporary directory;
3. backs up every file or directory that may change;
4. copies declared payload files and applies explicit deletions;
5. updates `DEVELOPMENT_STATE.json`;
6. runs the selected validation profile;
7. restores the prior repository files if validation fails.

The GitHub runner also uses a clean checkout, so a failed run never pushes partial changes.

## Safety rules

The updater rejects:

- absolute paths and path traversal;
- backslash-based paths;
- symbolic links;
- duplicate or case-colliding entries;
- `.git` modification;
- excessive entry counts or expanded sizes;
- suspicious compression ratios;
- unsupported application versions;
- missing or out-of-order sequence numbers;
- GitHub workflow changes unless both the package manifest and workflow invocation explicitly permit them.

## Workflow inputs

- `package_name`: optional exact root ZIP filename. Leave empty when there is only one matching package.
- `dry_run`: validates and prints the plan without committing changes.
- `validation_profile`: uses the package profile or overrides it with `none`, `standard`, or `full`.

Use `standard` for ordinary milestones and `full` for final consolidation.

## Package retention

The root update ZIP is intentionally removed by the workflow before the update commit. Release archives and final source packages belong in GitHub Releases or Actions artifacts rather than in the source tree.
