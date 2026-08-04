# Publishing on GitHub

InkDesk can be reconstructed from a source ZIP by the repository bootstrap workflow. The bootstrap is intentionally the only workflow included in the source package.

## Bootstrap files

Place these files in the repository:

- `InkDesk-source.zip` at the repository root.
- `.github/workflows/bootstrap-inkdesk.yml` in the workflow directory.

Run **Bootstrap InkDesk repository** manually from the Actions tab. The workflow validates the archive, installs the application tree, validates the installed tree again, and commits the result to `main`.

## Why additional workflows are not created automatically

The standard `GITHUB_TOKEN` used by GitHub Actions can commit normal repository content, but GitHub may reject attempts by that token to create or update additional files in `.github/workflows/`. This restriction prevents a workflow from silently granting itself new automation capabilities.

For that reason, the bootstrap package does not include separate Pages or quality-gate workflows. Add any future workflow manually through the GitHub interface or with an appropriately authorized maintainer credential, then review it before committing.

## GitHub Pages

GitHub Pages deployment is optional and is not configured by the bootstrap. A maintainer may create a reviewed Pages workflow later or publish the static tree using another supported GitHub Pages configuration.

GitHub Pages provides the HTTPS context required for service-worker registration. Verify the deployed manifest, service worker, workspace links, and offline reload in a real browser before describing the hosted build as installable.

## Continuous validation

The bootstrap workflow runs checksum verification, structural validation, source auditing, unit tests, and JavaScript syntax checks before committing the application. Future continuous-integration workflows should reuse the same scripts:

```bash
python3 scripts/verify_checksums.py
python3 scripts/validate_repository.py
python3 scripts/audit_source.py
python3 -m unittest discover -s tests -p "test_*.py"
```
