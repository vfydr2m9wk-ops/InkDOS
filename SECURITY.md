# Security

InkDOS processes supported files locally. Do not attach confidential files to public bug reports.

## Public QA privacy

Do not attach real user documents, screenshots, recordings, or private source material to public Issues or Pull Requests.

All repository fixtures and public reproduction material must be synthetic and privacy-safe. Never publish personal, medical, or educational data from a user's source files, and do not publish original private filenames or identifying document metadata.

Private QA material must not be committed to the repository or copied into release assets, GitHub Actions artifacts, workflow logs, Issues, or Pull Requests. Reproduce defects with synthetic fixtures that preserve only the minimum technical structure needed to exercise the bug.

If a report cannot be reproduced without confidential material, keep that material outside the public repository and reduce the report to an anonymized technical description before publication.

## Origin isolation

InkDOS is served from `https://vfydr2m9wk-ops.github.io/InkDOS/`. A browser treats every GitHub Pages site of the `vfydr2m9wk-ops` account as the same origin: such a page could read InkDOS's recovery drafts and settings, rewrite its offline cache or script its windows. Therefore:

- no other GitHub Pages site is published under the `vfydr2m9wk-ops` account (by people or by AI tools);
- third-party web code (the advanced tools and the OpenDocument/iWork viewers) is served by the separate `inkdos-tools` organization at `https://inkdos-tools.github.io/InkDOS-tools/`, a different origin; InkDOS exchanges files with it only through `postMessage` with explicit, checked origins;
- the offline service worker serves a cached file only while it matches the release snapshot hash;
- every tools page carries a strict Content-Security-Policy: nothing is fetched from or sent to another site.

`tests/test_origin_isolation_contract.py` fails the release validation if InkDOS starts using another page of its own origin, points the tools elsewhere or frames any other origin.

## Desktop update trust boundary

Desktop releases are built from an immutable version tag. The release workflow validates the tagged source, builds native artifacts on platform runners, signs updater artifacts, records build provenance and verifies that provenance before publication.

The Tauri updater public key may be configured in the built application. The signing private key and its password must remain GitHub Actions secrets and must never be committed to this repository.

## Desktop beta tools trust boundary

Beta tools are delivered to the desktop app outside desktop releases (see `docs/UPDATE_MODEL.md`). The app installs a bundle only when its manifest is signed by the beta-channel key pinned in the app (separate from the updater key) and every file matches the signed hash, and never installs an older bundle over a newer one. Beta tools run in isolated windows with no native access: they cannot read or write files except those the user picks in the page, and cannot call the updater or any other InkDOS desktop command.

## Digital signatures (PDF tools, beta)

The PDF tools sign with an A1 certificate (.pfx/.p12) entirely in the browser; the certificate, key and password never leave the device. Signatures are PAdES baseline B-B (`/ETSI.CAdES.detached`, SHA-256, signing-certificate-v2). Expired, not-yet-valid, sub-2048-bit or non-signing certificates are refused, and every new signature must pass the built-in check before it is returned.

The built-in check verifies integrity, the signer's signature, the signing-certificate binding, the byte range, an optional signature policy and the certificate chain. The chain is completed from the bundled ICP-Brasil list (`labs/pdf/trust/`, pinned document-signing roots; see its PROVENANCE.txt) and reported as "ICP-Brasil certificate" only when it ends at one of those roots. It does not check revocation (CRL/OCSP) or timestamps: ICP-Brasil revocation lists are served over plain HTTP without CORS, so a web page cannot fetch them without an intermediary.

For the complete validation the page offers the official ITI validator (https://validar.iti.gov.br). InkDOS never contacts it: after a warning that the document will be sent to the government's servers, the user opens the site in a new tab (`noopener,noreferrer`) and uploads the file there. Signing can optionally declare the ICP-Brasil policy PA_PAdES_AD_RB v1.1 (experimental; confirm the result on the ITI validator). Legal validity depends on the certificate (for Brazil, an ICP-Brasil certificate).
