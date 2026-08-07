# Development Guide

InkDesk intentionally avoids a mandatory build system. Source files are served directly.

## Setup

```bash
python3 -m http.server 8080
```

## Principles

Keep changes small, preserve offline operation, avoid unnecessary dependencies, maintain workspace isolation, and update tests and documentation together with behavior changes. All source code, comments, identifiers, filenames, and developer-facing messages must remain in English.

## Commands

```bash
npm run validate
npm run audit
npm test
npm run test:browser
npm run test:release
```

Use focused commits such as `fix:`, `docs:`, `test:`, `refactor:`, and `chore:`. Do not rename persisted storage keys without migration or a backward-compatible fallback. The current application has no persisted document schema.

## Architecture guardrail

The 0.20.x refactor is behavior-neutral and protected by
`architecture-policy.json`. Run `python3 scripts/check_architecture_guardrails.py`
before and after each extraction. AI-assisted work must also follow `AGENTS.md`.
