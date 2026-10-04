# Security

InkDOS processes supported files locally. Do not attach confidential files to public bug reports.

## Public QA privacy

Do not attach real user documents, screenshots, recordings, or private source material to public Issues or Pull Requests.

All repository fixtures and public reproduction material must be synthetic and privacy-safe. Never publish personal, medical, or educational data from a user's source files, and do not publish original private filenames or identifying document metadata.

Private QA material must not be committed to the repository or copied into release assets, GitHub Actions artifacts, workflow logs, Issues, or Pull Requests. Reproduce defects with synthetic fixtures that preserve only the minimum technical structure needed to exercise the bug.

If a report cannot be reproduced without confidential material, keep that material outside the public repository and reduce the report to an anonymized technical description before publication.

## Desktop update trust boundary

Desktop releases are built from an immutable version tag. The release workflow validates the tagged source, builds native artifacts on platform runners, signs updater artifacts, records build provenance and verifies that provenance before publication.

The Tauri updater public key may be configured in the built application. The signing private key and its password must remain GitHub Actions secrets and must never be committed to this repository.

## Digital signatures (PDF tools, beta)

The PDF tools sign with an A1 certificate (.pfx/.p12) entirely in the browser; the certificate, key and password never leave the device. Signatures are PAdES baseline B-B (`/ETSI.CAdES.detached`, SHA-256, signing-certificate-v2). Expired, not-yet-valid, sub-2048-bit or non-signing certificates are refused, and every new signature must pass the built-in check before it is returned.

The built-in check verifies integrity, the signer's signature, the signing-certificate binding, the byte range and the certificate chain carried in the signature. It does not check the chain against a trust list (e.g. ICP-Brasil), revocation (CRL/OCSP) or timestamps, so it reports "identity not verified". Legal validity depends on the certificate (for Brazil, an ICP-Brasil certificate) and should be confirmed with an official validator such as https://validar.iti.gov.br.
