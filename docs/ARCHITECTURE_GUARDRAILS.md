# Architecture guardrails — InkDOS 0.20.x

## Goal

The 0.20.x refactoring phase reduces the amount of code an AI or human must
understand for a focused change without altering InkDOS's product behavior.
The target is **modularity and confidence**, not framework parity or a rewrite.

## Runtime architecture

InkDOS remains a build-free local-first web application. Each workspace owns
its document state and domain behavior. Shared modules exist only for behavior
that is genuinely common.

The preferred dependency direction is:

```text
workspace entry/controller
        ↓
workspace feature modules
        ↓
shared primitives/runtime
```

Dependencies from one workspace into another are prohibited. Shared runtime
modules may not import a workspace implementation. Relative ES-module cycles
are prohibited even if a browser could execute them.

## Extraction pattern

A large controller should become a composition layer, not another generic
framework. Typical extraction order:

1. state and lifecycle;
2. UI controllers for independent regions;
3. editing/domain operations;
4. file import/export adapters;
5. final controller cleanup and dead-code removal.

Each extraction should be behavior-neutral and independently reversible.

## Size/readability ratchet

`architecture-policy.json` records the v0.20.2.1 runtime debt baseline. New
runtime JS/CSS files are limited to 500 physical lines and 240 characters per
physical source line. Existing files that already exceed those values are
explicitly grandfathered at their current metrics and may not grow.

This is intentionally a ratchet rather than an immediate formatting rewrite:
large inherited files can be reduced progressively without mixing thousands of
format-only line changes into one release.

Run:

```bash
python3 scripts/check_architecture_guardrails.py
```

The command is also part of the release-validation cycle.

## UI and visual ownership

Refactoring does not authorize visual redesign. Shared visual tokens and the
current workspace identities remain authoritative. UI controllers should own
behavior, while CSS owns responsive presentation whenever possible. JavaScript
should not maintain duplicate visual state when one canonical state is enough.

## OOP policy

Object orientation is used selectively. Classes are appropriate for objects
with state/lifecycle such as a document session, history stack, renderer,
recovery store or controller. Pure data transforms remain functions. Deep
inheritance and speculative factories are discouraged.

## Framework policy

React is not introduced during the 0.20.x refactor. Component boundaries are
created first using native modules and existing runtime primitives. Any future
framework migration would require a separate architecture decision with
measured benefits, offline/build implications, migration cost and a complete
regression plan.

## Required evidence

Before code is extracted, the owning behavior needs a regression test. After
the extraction the same behavioral checks, browser suite and file-integrity
checks must pass. A refactor cannot be considered successful merely because
static tests pass.
