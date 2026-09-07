# Known limitations

- PDF uses the accepted PDF.js 3.11.174 engine with its modified annotation worker. New text/ink/markup and form values are supported; arbitrary editing of existing PDF text, advanced forms, signatures and password UI are not certified.
- PDF changes remain in memory until exported. Downloads/system-sheet handoffs are reported as unverified storage and retain the unsaved indicator; mobile app termination can bypass unload warnings.
- Dependency advisory clearance and a new browser rendering matrix were not completed in the local audit; functional freeze is not a security certification.
- Each frozen app retains the explicit limitations of its accepted FINAL baseline.
- Save behavior is copy-based where the app's file contract specifies Save Copy; source bytes are not silently overwritten.
- Service-worker/PWA caching requires HTTP(S); direct `file://` execution depends on the host browser's local-file policy.
