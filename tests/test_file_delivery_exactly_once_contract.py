from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FileDeliveryExactlyOnceContractTests(unittest.TestCase):
    def _read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_apple_touch_share_route_is_terminal_for_documents_and_spreadsheets(self):
        for app in ("documents", "spreadsheets"):
            source = self._read(f"apps/{app}/io/file-delivery.js")
            guard = "if(c.preferShareSave&&c.share){"
            self.assertIn(guard, source, app)
            branch = source.split(guard, 1)[1].split("if(c.fileSystem)", 1)[0]
            self.assertNotIn("viaDownload", branch, f"{app}: selected Apple-touch share route must not fall through to a second download")

    def test_apple_touch_share_route_is_terminal_for_presentations_and_pdf(self):
        cases = (
            ("apps/presentations/io/file-delivery.js", "if(isAppleTouchHost()&&canShare(file))", "if(typeof global.showSaveFilePicker"),
            ("apps/pdf/io/file-delivery.js", "if(isAppleTouchHost()&&canShare(file))", "if(typeof global.showSaveFilePicker"),
        )
        for path, guard, next_guard in cases:
            source = self._read(path)
            self.assertIn(guard, source, path)
            branch = source.split(guard, 1)[1].split(next_guard, 1)[0]
            self.assertNotIn("download(", branch, f"{path}: selected Apple-touch share route must not trigger a second download")

    def test_plain_text_selected_share_route_is_terminal(self):
        source = self._read("apps/txt/index.html")
        marker = "if(route==='web-share')"
        self.assertIn(marker, source)
        branch = source.split(marker, 1)[1].split("if(route==='file-system-access')", 1)[0]
        self.assertNotIn("viaDownload", branch, "Plain Text web-share route must not fall through to a second download")


if __name__ == "__main__":
    unittest.main()
