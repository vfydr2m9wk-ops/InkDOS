# InkDOS 2.6.0 Stage 5 — distribution and validation

Approved reference: /Inkdos/InkDOS_Roadmap_2.6.0.txt and Checkpoint 04.
Base: bcac7844e8b75d9f558ba9905eb36dcd2e862fb5, existing PR #187 and feat/2.6.0-workspace-manifests.
Preserve main a7d94851128651e6713546e2727e2c98f1dbbe4b, v2.5.2 and VERSION.json. No merge or publication.

Inventory findings:
- Candidate CI 36017651692 passed. Stages 1–4 remain authoritative.
- Root worker is network-first, overwrites cached resources individually, calls skipWaiting/clients.claim and reuses baseline cache name. These allow revision mixing.
- Existing offline list covers runtime, including file-launch and manifests. Three absent TXT source modules are already bundled in index.html.
- Desktop staging injects desktop-host into HTML; snapshot hashes must be regenerated over staged bytes.
- Existing online audit targets published Pages, which remains 2.5.2. Candidate audit must serve the exact PR commit locally in CI, never claim it is deployed.

Execution sequence:
1. Reproduce cache revision mixing with real worker source in Node event/cache harness.
2. Generate SHA-256 asset inventory and content-derived cache revision from current APP_SHELL and worker runtime. Fail validation if stale. Verify each install response; remove incomplete new caches; preserve active snapshot.
3. Serve known runtime from verified immutable snapshot; verify network recovery for cache misses. Keep native waiting lifecycle so existing tabs are not forcibly switched. Scope cache ownership to registration URL. Preserve unknown requests and canonical directory navigation.
4. Regenerate snapshot after desktop bridge injection; check staging with existing contracts.
5. Add actual browser upgrade/offline regression and candidate matrix (Chromium, Firefox, WebKit) on PR head. Reuse visual/stateful harnesses and store exact commit evidence.
6. Review concrete findings, fix regressions, update existing PR and checkpoint. No unrelated editor changes.

Evidence ledger:
- Reanchored from Checkpoint 04 and live GitHub. Previous local isolated draft is not applied to current branch.
- Local browser download unavailable; use authenticated repository CI for browser evidence.
