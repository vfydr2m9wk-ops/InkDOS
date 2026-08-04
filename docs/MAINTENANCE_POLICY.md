# Maintenance Policy

## Stabilization cadence

At least every third feature-oriented release should reserve time for cleanup, dependency review, test expansion and documentation corrections.

## Technical-debt triggers

A stabilization milestone is required when any of the following occurs:

- a source file exceeds 1,000 non-vendor lines;
- multiple bugs originate from the same parser assumption;
- a workaround is duplicated across components;
- a feature depends on undocumented host behavior;
- issue triage cannot reproduce compatibility reports;
- release validation becomes primarily manual and undocumented.

## Deprecation

Experimental features can be removed when they expand the failure surface without demonstrated use. Removal should be documented in the changelog.
