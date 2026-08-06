# Publishing and incremental updates on GitHub

InkDesk uses one stable workflow:

```text
.github/workflows/apply-inkdesk-update.yml
```

## One-time bootstrap

Workflow files are security-sensitive and the default `GITHUB_TOKEN` cannot
create or update them through an ordinary workflow push. Install or replace the
stable workflow manually in the GitHub web interface. This is a one-time
bootstrap operation.

After bootstrap, update packages must never contain files below
`.github/workflows/` and must never delete workflow files.

## Normal update path

1. Place exactly one `InkDesk-update-v*.zip` in the repository root.
2. Run **InkDesk integrity and update** from the Actions tab.
3. Leave `package_name` empty, use `dry_run: false`, and use
   `validation_profile: package`.
4. The workflow validates the ZIP and repository transactionally.
5. Only after validation succeeds does it remove the root ZIP, create the
   update commit, push to `main`, and request a Pages rebuild.

If validation fails, changed files are restored. If the final push fails, the
remote repository and its root ZIP remain unchanged.

## Continuous integration

The same workflow runs a read-only integrity gate on ordinary pushes and pull
requests. Updates committed by the workflow are already validated before push;
GitHub intentionally does not recursively trigger another run for commits made
with `GITHUB_TOKEN`.
