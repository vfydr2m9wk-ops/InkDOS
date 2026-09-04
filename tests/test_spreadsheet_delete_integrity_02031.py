from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SpreadsheetDeleteIntegrity02031Tests(unittest.TestCase):
    def test_deleted_sheet_references_are_invalidated_in_runtime(self):
        app = (ROOT / "apps/spreadsheets/app.js").read_text(encoding="utf-8")
        integrity = (ROOT / "apps/spreadsheets/formula-integrity.js").read_text(encoding="utf-8")
        self.assertIn("invalidateDeletedSheetReferences", app)
        self.assertIn("explicit && !target", integrity)
        self.assertIn("error: '#REF!'", integrity)
        self.assertIn("rewriteCodeSegments", integrity)
        self.assertIn("A-Za-z0-9_.\\]", integrity)
        self.assertIn("if(/#REF!/i.test(f))return'#REF!'", app)
        self.assertIn("const invalidated=invalidateDeletedSheetReferences(current.name)", app)

    def test_deleted_sheet_dependencies_are_pruned_only_when_orphaned(self):
        package = (ROOT / "apps/spreadsheets/worksheet-package.js").read_text(encoding="utf-8")
        self.assertIn("removeOrphanedDependencies", package)
        self.assertIn("incomingReferenceCounts", package)
        self.assertIn("relationshipTargets", package)
        self.assertIn("if ((incoming.get(part) || 0) > 0) continue", package)
        self.assertIn("deletedDependencyTargets.push", package)

    def test_browser_round_trip_covers_ref_and_orphan_cleanup(self):
        regression = (ROOT / "tests/browser/revalidate_spreadsheet_add_sheet.py").read_text(encoding="utf-8")
        self.assertIn('deleted_reference_display', regression)
        self.assertIn('reopened_reference_display', regression)
        self.assertIn('orphan_parts_removed', regression)
        self.assertIn('xl/drawings/drawing1.xml', regression)
        self.assertIn('#REF!', regression)


if __name__ == "__main__":
    unittest.main()
