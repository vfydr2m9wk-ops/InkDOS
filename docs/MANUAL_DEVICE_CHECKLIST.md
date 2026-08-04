# Manual Device Checklist — 0.19.1-beta

Record date, exact browser build, OS/device, host mode, fixture, and result. Preserve screenshots/logs without private documents.

| Environment | Open | Edit | Export request | Reopen/fingerprint | Offline/PWA | Current result |
|---|---|---|---|---|---|---|
| Desktop Safari | — | — | — | — | — | Not tested |
| Native desktop Firefox | — | — | — | — | — | Not tested |
| iPadOS Safari | — | — | — | — | — | Not tested |
| Installed PWA | — | — | — | — | — | Not tested |
| Direct `file://` where allowed | — | — | — | — | N/A | Not tested |
| Embedded/local-file host | — | — | — | — | Host-specific | Not tested |

For each environment test all three workspaces with backup fixtures. Verify dirty indicators, cancellation/blocked download behavior, before-unload after an unverified request, exact exported-copy reopen, no unexpected network traffic, memory behavior on a representative large file, and service-worker update/cache behavior where applicable.
