# ADR 0001: Keep a native modular runtime during 0.20.x refactoring

- Status: Accepted
- Date: 2026-08-07

## Context

InkDesk is a local-first, static browser application that already runs without a
mandatory package-manager or compilation step. Large controllers have become a
maintenance and AI-context cost, but replacing the runtime architecture while
stabilizing file behavior would greatly increase regression risk.

## Decision

InkDesk will create feature-oriented component boundaries using native
HTML/CSS/JavaScript during the 0.20.x refactoring sequence. React or another UI
framework will not be introduced as part of these behavior-neutral releases.

Object-oriented design may be used selectively for stateful lifecycle objects;
stateless transformations remain functions/modules.

## Consequences

- Runtime remains easy to host, test offline and embed.
- Refactoring can proceed one component at a time.
- Existing tests remain directly applicable.
- A later framework decision remains possible, but requires a separate ADR and
  migration/regression plan.
