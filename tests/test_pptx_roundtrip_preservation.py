from pathlib import Path
from zipfile import ZipFile
import hashlib
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "compatibility-fixtures" / "presentations"
APP = ROOT / "apps" / "presentations" / "app.js"
FILE_IO = ROOT / "apps" / "presentations" / "io" / "file-controller.js"
PPTX_WRITER = ROOT / "apps" / "presentations" / "io" / "pptx-write-adapter.js"


def hashes(path: Path) -> dict[str, str]:
    with ZipFile(path) as archive:
        return {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in archive.namelist()
            if not name.endswith("/")
        }


class PptxPreservationTests(unittest.TestCase):
    def test_relationship_path_regression_is_removed(self):
        source = APP.read_text(encoding="utf-8")
        self.assertIn("function relationshipPartPath", source)
        self.assertIn("relationshipPartPath(slidePath)", source)
        self.assertIn("relationshipPartPath(layoutPath)", source)
        self.assertIn("relationshipPartPath(masterPath)", source)
        self.assertNotIn("replace('presentations/'", source)

    def test_imported_export_uses_original_package(self):
        app = APP.read_text(encoding="utf-8")
        source = FILE_IO.read_text(encoding="utf-8")
        writer = PPTX_WRITER.read_text(encoding="utf-8")
        self.assertIn("this.sourceBuffer = null", source)
        self.assertIn("async saveImportedPptx()", source)
        self.assertIn("JSZip.loadAsync(previousSource)", source)
        self.assertIn("this.patchImportedSlide", source)
        self.assertIn("originalSlideRids", writer)

    def test_modern_rendering_hooks_exist(self):
        source = APP.read_text(encoding="utf-8")
        for marker in (
            "parseGraphicFrame",
            "renderChartObject",
            "parseSlideTransition",
            "parsePresenterNotes",
            "cropZoom:hasCrop",
        ):
            self.assertIn(marker, source)

    def test_legacy_fixture_is_binary_ppt(self):
        data = (FIXTURES / "era1_office_97_2003_legacy.ppt").read_bytes()
        self.assertTrue(data.startswith(bytes.fromhex("D0CF11E0A1B11AE1")))

    def test_baseline_fixture_has_image_table_layout_and_master(self):
        path = FIXTURES / "era2_office_2007_2013_baseline.pptx"
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            self.assertIn("ppt/media/image1.png", names)
            self.assertIn("ppt/slideMasters/slideMaster1.xml", names)
            self.assertIn("ppt/slideLayouts/slideLayout1.xml", names)
            slide_xml = "\n".join(
                archive.read(name).decode("utf-8", "replace")
                for name in names
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            self.assertIn("<a:tbl", slide_xml)

    def test_modern_fixture_has_chart_notes_transition_and_crop(self):
        path = FIXTURES / "era3_office_2016_365_modern.pptx"
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            self.assertIn("ppt/charts/chart1.xml", names)
            self.assertIn("ppt/notesSlides/notesSlide1.xml", names)
            self.assertIn("ppt/notesSlides/notesSlide2.xml", names)
            joined = "\n".join(
                archive.read(name).decode("utf-8", "replace")
                for name in names
                if name.startswith("ppt/slides/slide") and name.endswith(".xml")
            )
            self.assertIn("<p:transition", joined)
            self.assertIn("<a:srcRect", joined)
            self.assertIn("<p:graphicFrame", joined)

    def test_fixture_hashes_are_stable_during_read_only_inspection(self):
        for name in (
            "era2_office_2007_2013_baseline.pptx",
            "era3_office_2016_365_modern.pptx",
        ):
            path = FIXTURES / name
            before = hashes(path)
            with ZipFile(path) as archive:
                _ = archive.read("ppt/presentation.xml")
            self.assertEqual(before, hashes(path))


if __name__ == "__main__":
    unittest.main()
