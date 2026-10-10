# Contributing to InkDOS

Thank you for helping InkDOS. It is a local-first productivity suite (Documents, Spreadsheets, Presentations, PDF, EPUB and Plain Text) that runs entirely in the browser (Chromium and iOS/iPadOS WebKit; see `SUPPORT.md`). The Tauri desktop app in `desktop/` is kept but not published. Contributions of every size are welcome: bug reports, reproductions, translations, documentation and code.

By participating you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Report a bug**: use the [bug report form](https://github.com/vfydr2m9wk-ops/InkDOS/issues/new?template=bug_report.yml). Include the InkDOS version, browser and operating system, and the smallest steps that reproduce the problem.
- **Suggest a feature**: use the [feature request form](https://github.com/vfydr2m9wk-ops/InkDOS/issues/new?template=feature_request.yml). Describe the problem it solves before the solution.
- **Improve translations**: interface strings live in `shared/localization/locales/*.js` (German, Spanish, French, Japanese, Portuguese (Brazil), Russian, Simplified Chinese). Every locale must keep the same keys.
- **Send a pull request**: see below.
- **Report a security issue privately**: see [SECURITY.md](SECURITY.md). Never open a public issue for vulnerabilities.

### Privacy first

InkDOS edits people's own files. **Never attach real documents, screenshots, recordings or private filenames** to issues or pull requests. Build a synthetic file that reproduces the problem with the minimum structure needed. See [SECURITY.md](SECURITY.md#public-qa-privacy).

## Running InkDOS locally

No build step is needed for the web edition:

```bash
git clone https://github.com/vfydr2m9wk-ops/InkDOS.git
cd InkDOS
python -m http.server 8000
# open http://127.0.0.1:8000/
```

Generated files are checked in and must be regenerated with the repository scripts, never edited by hand:

- `apps/txt/index.html`: `python scripts/build_txt_bundle.py` (edit `apps/txt/page.template.html` and the TXT sources instead).
- `service-worker.js` offline snapshot: `python scripts/build_offline_snapshot.py`.
- Content-Security-Policy metadata: `python scripts/generate_csp.py`.

The former browser extension is discontinued; its last code is kept, unmaintained, on the `extension` branch.

## How changes are organized

InkDOS is maintained with small, audited changes. The rules are in [AGENTS.md](AGENTS.md); in short:

- **One component per pull request.** Components are `hub` (Home), `documents`, `spreadsheets`, `presentations`, `txt`, `epub` and `pdf`; their paths are in `config/components.json`. Cross-component changes need a demonstrated technical reason, stated in the pull request.
- **Preserve working code.** Fix reproduced defects or explicit requirements. Do not refactor, rename or clean up unrelated code in the same change.
- **Frozen legacy** (`INKDOS:FROZEN-LEGACY`, registry in `config/frozen-legacy.json`) is changed only when the task explicitly authorizes it.
- **Vendor/minified files** are not edited unless the defect is in that dependency.
- **Versions and releases** are handled by the maintainers in separate pull requests. Do not bump versions or rewrite the changelog in a feature or fix PR.

## Tests

Every fix should come with a regression test that fails before the change and passes after it. Browser tests use Playwright (Chromium and WebKit run in CI; see SUPPORT.md).

```bash
pip install -r requirements-ci.txt
python scripts/agent_context.py <component>        # owned paths and relevant tests
python scripts/agent_test.py <component>           # component smoke tests
python scripts/agent_test.py <component> --browser # plus browser tests
python scripts/agent_verify.py <component> --base main
```

`scripts/run_release_validation.py` is the full release gate; the maintainers run it before a release.

Vendored third-party code is listed with exact hashes in `config/vendor-inventory.json`. Before a release, run `python3 scripts/check_vendor_advisories.py` (network) to check those versions for known advisories on OSV.dev; an advisory must be fixed by updating the library or accepted with a written reason.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make the smallest correct change for one component, with its regression test.
3. Run the component tests and `agent_verify` above.
4. Open the pull request and fill in the template (task contract, result, human audit). Keep it short: what changed, why, and how it was verified.
5. CI must be green before review. Maintainers may ask for changes; small follow-up commits are preferred over force-pushes during review.

## License

InkDOS is released under the [MIT License](LICENSE). By contributing, you agree that your contributions are licensed under the same terms. Third-party components keep their own licenses (see `licenses/` and `docs/THIRD_PARTY_NOTICES.md`).
