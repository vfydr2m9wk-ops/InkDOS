# Incremental InkDOS updates

InkDOS uses a monotonically increasing internal update sequence that is
independent from the public semantic version. The current sequence is recorded
in `DEVELOPMENT_STATE.json`.

## Permanent workflow

The stable workflow is:

```text
.github/workflows/apply-inkdos-update.yml
```

Workflow changes are installed manually in an ordinary repository commit.
Update ZIPs can never create, modify or delete `.github/workflows/`.

## Package format

```text
InkDOS-update-vX.Y.Z.zip
├── patch-manifest.json
├── files/
│   └── repository-relative files to add or replace
└── DELETE.txt                 # optional
```

`patch-manifest.json` identifies `product: InkDOS`, the target release line,
package label, sequence, required previous sequence, allowed application base
versions, validation profile, and optional per-file SHA-256 contracts.

`DELETE.txt` contains one repository-relative path per line. Empty lines and
lines beginning with `#` are ignored.

## Transaction and rollback

The updater:

1. validates the ZIP structure, paths, limits, manifest, base version and sequence;
2. verifies declared payload SHA-256 values and optional hashes of files being replaced or deleted;
3. applies the package to a disposable copy of the repository;
4. regenerates deterministic release/checksum metadata when validation requires it;
5. runs the selected validation profile against that candidate;
6. leaves the real repository untouched when candidate validation fails;
7. applies only the validated candidate diff to the real repository;
8. restores touched files if the final filesystem transaction itself fails.

## Safety rules

The updater rejects absolute/traversal/backslash paths, symbolic links,
duplicate or case-colliding entries, `.git` modification, GitHub workflow
changes, oversized archives, suspicious compression ratios, unsupported base
versions, product mismatches and skipped/repeated sequence numbers.

## Workflow inputs

- `package_name`: optional exact root ZIP filename; leave empty when exactly one matching package exists.
- `dry_run`: validates a disposable candidate without committing changes.
- `validation_profile`: uses the package profile or overrides it with `none`, `standard`, or `full`.

Use `full` for release-bearing consolidation packages.

## Package retention

The root update ZIP is removed by the workflow only after validation succeeds
and immediately before the generated update commit. Release archives belong in
GitHub Releases or Actions artifacts rather than in the source tree.
