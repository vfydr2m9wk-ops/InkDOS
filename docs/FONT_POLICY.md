# Font and Typography Policy

The project does not bundle proprietary Microsoft fonts or proprietary Office rendering libraries.

## Consequences

When a source font is unavailable, the browser or host substitutes another font. This can change:

- line breaks;
- text-box height;
- page or slide pagination;
- bullet alignment;
- table dimensions;
- overall visual fidelity.

## Project approach

- Preserve the requested family name in parsed metadata when practical.
- Use common system-font fallbacks.
- Document known substitutions.
- Avoid distributing fonts without a license that explicitly permits redistribution.
- Treat typography differences as expected unless they cause severe overlap, disappearance or data loss.

The long-term goal is predictable substitution, not a claim of metric identity with Microsoft Office.
