# InkDOS Security Audit Status

Tested branch: `audit/stability-functional-isolation`
Baseline reviewed: `ed77615eaadd8680c2c63221d9b57e2ce4ef6b54`
Security-test increment: `42921fc9a49564d335fe4781ee0cf2a314935d58`
Date: 2026-09-08

## Gate status

**SECURITY GATE: BLOCKED**

The roadmap and Stability Freeze must remain suspended until the blocking items below are remediated and regression-tested.

## Confirmed findings

### PDF.js / CVE-2024-4367 — confirmed, reachable dependency, explicit workaround present, upgrade still required

- Vendored PDF.js version is `3.11.174`.
- Upstream advisory GHSA-wgrm-67xf-hhpq / CVE-2024-4367 affects `pdfjs-dist <= 4.1.392`; patched version begins at `4.2.67`.
- InkDOS already passes `isEvalSupported:false` to `pdfjsLib.getDocument(...)`, which is the documented workaround and materially reduces exploitability of this specific issue.
- The external remediation specification nevertheless requires replacing the vulnerable vendored release with a non-vulnerable release at least `4.2.67`; therefore this item remains blocking until the vendored display library and modified worker are upgraded together and the PDF regression/offline matrix passes.
- Regression coverage added: `tests/test_security_pdfjs_config.py` verifies the explicit `isEvalSupported:false` configuration remains present.

### Content Security Policy — confirmed missing at root entry point

- `index.html` has no Content-Security-Policy meta tag.
- It contains inline scripts, so a CSP meeting the required `script-src 'self'` posture cannot be added safely without first externalizing inline script blocks.
- Treat CSP rollout as a cross-entry-point migration; do not weaken the target policy with `unsafe-inline` or `unsafe-eval` merely to preserve current markup.

### Repository governance — external administrative action required

- `main` is currently reported as unprotected.
- Repository rulesets endpoint currently returns no rulesets.
- `.github/CODEOWNERS` exists and assigns the repository to `@vfydr2m9wk-ops`, but CODEOWNERS alone does not enforce review while branch/ruleset protection is absent.
- Autonomous code changes must not modify `.github/workflows/**` or repository privilege boundaries. Required owner-side controls: protect `main`; disallow force-push/deletion; require pull requests and required status checks; require CODEOWNER/human review for `.github/workflows/**` and release/security-control surfaces.

### Security disclosure — incomplete

- `SECURITY.md` warns against posting confidential files publicly but does not currently provide a verified private reporting channel.
- GitHub Private Vulnerability Reporting should be enabled by the repository owner if available. Until a private path is verified, reporters should not be instructed to publish exploit details in Issues.

## Not yet fully classified

The following remain required before the security gate can turn green: all HTML entry-point CSP migration; DOM/XSS sink audit with EPUB priority; sandboxed/opaque-origin EPUB rendering and sanitizer review; same-origin storage/IndexedDB/Cache/Service Worker isolation; ZIP/XML container limits for DOCX/XLSX/PPTX/EPUB; active URL/resource scheme allowlists; complete vendored dependency inventory and vulnerability scan; CI workflow supply-chain review with human-approved remediation patch; malicious-fixture regression coverage; final cross-suite browser/offline security matrix.

## Reproducible checks

```bash
python -m pytest -q tests/test_security_pdfjs_config.py
python -m pytest -q tests/test_pdf_stability_contract.py tests/test_pdf_stability_comments.py
python -m pytest -q tests/test_pdf_stability_browser.py
```

When dependency scanning is available in CI or a trusted local checkout, record the exact scanner version and command output here rather than marking the gate green from state JSON alone.

## Promotion policy

Do not promote this branch checkpoint to `main` while PDF.js `3.11.174` remains vendored or while any confirmed reachable High/Critical issue is unresolved. Security remediation may interrupt the normal workspace order; after the blocking issue is removed and the combined PDF stability+security gate is green, resume the stability sequence on the same audit branch.
