# Presentations architecture delta — v0.20.2.9

## Scope

Behavior-preserving consolidation only. No visual redesign or new feature.

## New component

`apps/presentations/io/pptx-write-adapter.js` owns imported PPTX package mutation, source-order verification, transition patching, presenter-note patching and XML generation for newly inserted shapes/images.

## Entry-point boundary

`apps/presentations/app.js` now composes the write adapter and passes four narrow callbacks to `file-controller.js`. The entry point no longer owns the package-write helper implementations.

## Guardrail

The app.js ratchet is tightened to the physical-line and long-line count measured by the release gate. New extracted modules remain under the 500-line / 240-character limits.

## Next target

After this release passes the hosted dry-run and apply gates, Presentations refactoring is considered consolidated for this cycle and PDF becomes the next decomposition target.
