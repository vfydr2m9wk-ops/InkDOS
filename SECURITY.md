# Security Policy

InkDOS treats imported Office documents as untrusted ZIP/XML input. It does not intentionally execute VBA macros, ActiveX, embedded JavaScript, add-ins, or remote document instructions. Core processing is local, and the project includes no telemetry or document-upload backend.

The shared runtime rejects encrypted/ZIP64 packages, unsafe paths, malformed offsets, excessive entry counts, unreasonable compressed or expanded sizes, and extreme compression ratios before committing a new document model. These controls reduce risk but do not replace browser sandboxing or fuzz testing.

Report vulnerabilities privately through GitHub Security Advisories when available. Include the affected version, browser/platform, reproduction steps, and a minimal proof of concept. Do not publish sensitive details before a fix can be evaluated.

Current hardening priorities include broader malformed-package fixtures, XML/ZIP fuzzing, native browser validation, review of the restricted spreadsheet arithmetic evaluator, and privacy-preserving recovery storage.
