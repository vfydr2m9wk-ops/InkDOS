# Contributing to InkDesk

Contributions are welcome. Keep pull requests focused, preserve offline behavior and workspace isolation, and do not introduce telemetry, cloud requirements, or unnecessary frameworks. Treat imported documents as untrusted input.

Before submitting, run repository validation, source audit, unit tests, and relevant browser regression. Update documentation in the same pull request when behavior changes. All project-facing text and code identifiers must be in English.

## Refactoring contributions

Read `AGENTS.md` before changing runtime architecture. Refactors must be small,
behavior-neutral, covered by existing or new behavioral tests, and must pass
`python3 scripts/check_architecture_guardrails.py`. Do not add an architecture
policy exception merely to bypass the ratchet.
