# Data Safety and Browser Matrix

## Private recovery snapshots

InkDesk 0.20.2 stores unsaved recovery snapshots only in the browser IndexedDB database `InkDeskLocalRecovery`. Documents, Spreadsheets and Presentations use separate workspace namespaces. The source file is retained only as local browser data when it is needed to reconstruct a package-preserving copy. No recovery data is sent to an InkDesk server.

Recovery never overwrites the selected source file. On startup, the user chooses **Restore**, **Open normally**, or **Discard recovery**. A browser download request is deliberately treated as unverified: editable Office workspaces keep dirty/recovery protection until the user explicitly replaces or discards that work. Shared OOXML source data is retained locally when needed for package-preserving recovery and can be rehydrated by an active session.

New recovery snapshots are isolated by both document identity and a per-tab/session identifier. Reset, clean and discard operations therefore affect only the current recovery session, not another tab editing the same file. Retention keeps up to three snapshots per document session and targets twelve snapshots per workspace while preserving at least one recovery point per independent session; records expire after thirty days. Legacy snapshots created before session isolation remain discoverable and restorable.

## Browser validation

The stable incremental update workflow runs the complete Chromium regression suite once. The updater does not repeat unit, audit or repository gates before the complete release validator, keeping hosted-runner duration predictable.

The hosted offline regression also verifies cache-busted shell URLs against canonical pre-cache keys, so `?v=` release tokens do not bypass the service-worker application shell.

Run the explicit installed-browser matrix with:

```bash
python3 scripts/run_browser_matrix.py
```

The runner checks Chromium, Firefox and WebKit. Missing engines are reported and skipped by default. To require every requested engine:

```bash
INKDESK_BROWSER_MATRIX_STRICT=1 python3 scripts/run_browser_matrix.py
```

Select engines with `INKDESK_BROWSERS=chromium,firefox,webkit`.
## Functional acceptance inventory

`docs/FUNCTIONAL_ACCEPTANCE_MATRIX.json` is the machine-readable inventory for user-visible controls, while `docs/FUNCTIONAL_ACCEPTANCE_CHECKLIST.md` is the human review view. A rendered control is not counted as confirmed merely because it exists in HTML or JavaScript. Behavioral automation or an explicit manual device check is required.

The v0.20.2 correction adds a dedicated Presentations control regression, including the responsive format-panel drawer at compact/iPad-width viewports. Remaining inventoried controls stay marked **scheduled** until dedicated behavior coverage is added in this release line or the next stabilization releases.

- Presentations format-panel cascade regression: verifies desktop visibility plus compact fixed-drawer open/close behavior after the shared Office shell cascade.

### Hosted correction-2 result

The hosted Chromium transaction passed 200 unit tests and 10 of 11 browser scripts. Local recovery and offline launch passed. The only remaining browser failure was the Presentations format-panel visibility regression; correction revision 3 addresses the final shared-stylesheet cascade that could override the product drawer rules.



#### Presentations control acceptance correction 4

The Format panel and Presenter Notes now have an explicit closed-at-open contract. The browser regression starts from that state and must prove that the visible View controls open, hide, and reopen the Format panel, that format controls mutate a selected object, and that Presenter Notes toggle reversibly. This prevents a correct collapsed startup state from being mistaken for a broken panel while still catching an unresponsive button.


### Hosted correction-4 result and correction-5 response

The hosted correction-4 transaction passed 205 unit tests and 10 of 11 Chromium browser scripts. Offline launch, local recovery, three-era Office fixtures and isolation all passed. The remaining failure occurred after switching the Presentations viewport to compact width: the drawer was visually collapsed but `aria-expanded` could still reflect the previous desktop-open state. A deeper review also found the more important real-device path: on a compact cold start, `resetOptionalPanelsForOpen()` could re-add the desktop `hide-inspector` class after the initial media-query synchronization, allowing the Show button and CSS cascade to disagree. Correction 5 replaces the split class state with one `inspectorOpen` source of truth and adds a fresh compact-context behavioral test.
