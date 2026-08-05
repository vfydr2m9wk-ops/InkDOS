# Release Readiness and Privacy Audit — InkDesk 0.19.2-beta

## Version decision

The package is suitable for a new beta release but not for a `1.0` designation. The current evidence covers repository validation, source audit, 53 Python tests, 46 JavaScript security assertions, syntax checks, and previously executed Chromium regression scenarios. It does not include native Safari, physical iPadOS, installed-PWA, local Firefox/WebKit engine, memory-pressure, crash-recovery, broad fuzzing, or post-hardening real-corpus validation.

## Comparison with repository `main`

The input hardening package was compared against the repository checksum manifest current on 2026-08-04. Of 164 files represented by `main`, 149 were byte-identical, 14 were modified, four were added, and one obsolete force-promotion workflow was absent. The package therefore represents a forward hardening/packaging change rather than a repackaging of the exact `main` tree.

## Privacy and hidden-file findings

No real-world name, personal email address, telephone number, CPF/CNPJ, postal address, absolute local user path, private key, access token, `.git` directory, editor workspace, OS metadata file, ZIP comment, or EXIF identity field is included.

Tool-generated personal-name metadata in synthetic Office fixtures was replaced with generic InkDesk fixture metadata. Intentional dot-paths remain: `.github/`, `.gitignore`, `.editorconfig`, and `.nojekyll`. These are normal repository files and contain no secret values. Workflow files refer to the secret name `INKDESK_RELEASE_PAT`, never to its value.

The string `vfydr2m9wk-ops` remains in public repository URLs and `CODEOWNERS`. It identifies the publishing GitHub account. The source package contains no additional information connecting that handle to a real person.

## Release recommendation

Publish as `v0.19.2-beta` with the title **InkDesk 0.19.2-beta — Release Packaging and Privacy Cleanup**. Retain beta warnings and do not market the package for regulated, medical, legal, financial, or fidelity-critical production use.
