# INKBUG-0001 PPTX AutoFit Line-Spacing Preservation Fix

**Goal:** Preserve a PPTX text box's existing `a:normAutofit/@lnSpcReduction` when a mapped text box is edited and rewritten.

**Baseline:** `1986ae0fd81c94fa8202c10d9dea6fcd11d807af` (InkDOS 2.0.12 immutable regression reference).

**Environment / reproduction:** Repository source audit plus synthetic OOXML semantics. In `apps/presentations/io/pptx-preservation-writer.js`, `setBodyPr()` removes the existing autofit child and recreates `a:normAutofit` with `lnSpcReduction="0"`. Therefore an imported text box such as `<a:normAutofit fontScale="92000" lnSpcReduction="20000"/>` loses its 20% line-space reduction whenever its text is rewritten.

**Expected:** Text-only edit/save/reopen preserves the source line-space reduction unless the user explicitly changes that formatting.

**Actual:** Writer forces the value to zero.

**Severity / impact:** Medium fidelity defect; no package corruption, but save/reopen changes vertical text layout and can alter wrapping/clipping in presentations.

## Tasks

1. Add a focused regression contract to `tests/test_real_device_remediation_contract.py` and verify RED against the baseline writer.
2. In `apps/presentations/io/pptx-preservation-writer.js`, capture the existing direct `normAutofit` line-spacing reduction before replacing autofit nodes and reuse it when normal autofit is rewritten; default to `0` when absent.
3. Run the focused regression contract and relevant presentation/package-preservation validation available in CI.
4. Refetch `main`; fast-forward only if it still matches the audited baseline.
5. Persist Prompt 2 checkpoint/evidence with INKBUG-0001 FIXED/VERIFIED only after verification succeeds.
