# Home-functional Audit checkpoint — 2026-09-09

## Scope

This checkpoint closes the `Audit` phase of the home-functional roadmap after the XLS-S2 semantic clipboard checkpoint was promoted to `main` as `5f8894dc5144ca94f50718595b603d1827c01126`.

The audit is a regression and integration checkpoint. It does not broaden any file-format fidelity claim, does not reopen frozen workspace UI/architecture, and does not certify security beyond the existing configuration regressions and documented limitations.

## Verified gate set

The promotion snapshot `9f095bccf9a9e2b3352aad3232579ed97fdf510e` completed the full PR gate set successfully before merge:

- XLS-S1 structural formula regression, including Chromium, Firefox and WebKit;
- XLS-S2 semantic clipboard regression;
- Spreadsheets stability regression;
- Cross-suite stability regression;
- PPT-P2 regression;
- pre-phase architecture/isolation audit;
- InkDOS integrity and update validation;
- Stability freeze regression, including suite architecture/offline contracts, all frozen static contracts, security configuration regression, the complete primary stability browser matrix in Chromium/Firefox/WebKit, and preserved format round-trips.

Two lifecycle-only gate defects discovered during the audit were corrected before approval: phase-scope validation now handles canonical same-workspace multi-step promotions without opening sibling app roots, and the legacy XLS-S1 static contract now recognizes later canonical roadmap phases while retaining its formula/structure assertions.

## Freeze transition contract

`FUNCTIONAL_STATE.json` moves to `Freeze` only after the gate set above is green. The cross-suite and stability-freeze workflows explicitly include `FUNCTIONAL_STATE.json` in their path triggers so future functional-roadmap transitions cannot bypass the integration/freeze regression matrices.

Known functional and platform limitations remain those recorded in `docs/KNOWN_LIMITATIONS.md` and the accepted per-workspace baselines.
