# Development guide

InkDOS is a static, build-free browser application. Serve the repository root or open `index.html` directly; HTTP(S) is recommended for service-worker and PWA testing.

## Change discipline

Work from the current behavior contract, not from historical implementation. Prefer deleting, consolidating or rewriting over adding compatibility layers. Changes that affect file handling, recovery, save semantics or UI interaction require targeted regression coverage.

Before publication run the complete release validator:

```bash
python3 scripts/run_release_validation.py
```

Incremental update packages are applied to a disposable candidate tree first. Only a fully validated candidate is copied into the working tree.

See `AGENTS.md` for the engineering policy and `docs/ARCHITECTURE.md` for the current component boundaries.
