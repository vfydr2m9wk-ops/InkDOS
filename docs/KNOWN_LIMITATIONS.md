# Known limitations

- PDF Workspace is not installed in InkDOS 2.0.1 Core.
- Each frozen app retains the explicit limitations of its accepted FINAL baseline.
- Save behavior is copy-based where the app's file contract specifies Save Copy; source bytes are not silently overwritten.
- Service-worker/PWA caching requires HTTP(S); direct `file://` execution depends on the host browser's local-file policy.
