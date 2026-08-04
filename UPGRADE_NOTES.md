# Upgrade Notes — 0.19.1-beta

- Replace the previous static application folder with the complete 0.19.1-beta runtime package; do not mix old and new `shared/` files.
- Hosted/PWA users should reload after the new service worker activates. The cache name changed to `inkdesk-shell-v0.19.1-beta`.
- A requested download no longer clears the dirty warning. Reopen the generated copy to obtain fingerprint verification.
- Unsupported spreadsheet formulas may now show their cached value with a “not recalculated” indication rather than an unsafe or misleading local result.
- Packages rejected by the new ZIP/XML limits should be inspected/constrained in a trusted desktop Office application; do not weaken limits merely to open an unknown file.
- No account, backend, database, or persistent document migration is introduced.
