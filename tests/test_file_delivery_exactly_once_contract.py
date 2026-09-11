from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FileDeliveryExactlyOnceContractTests(unittest.TestCase):
    def _read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_apple_touch_share_route_is_terminal_for_documents_and_spreadsheets(self):
        for app in ("documents", "spreadsheets"):
            source = self._read(f"apps/{app}/io/file-delivery.js")
            terminal = "if(c.preferShareSave&&c.share)return viaShare(blob,fileName,file)"
            self.assertIn(terminal, source, f"{app}: Apple-touch Web Share must be a terminal return")

    def test_apple_touch_share_route_is_terminal_for_presentations_and_pdf(self):
        cases = (
            ("apps/presentations/io/file-delivery.js", "if(isAppleTouchHost()&&canShare(file))return viaShare(blob,name,file)"),
            ("apps/pdf/io/file-delivery.js", "if(isAppleTouchHost()&&canShare(file))return share(blob,name)"),
        )
        for path, terminal in cases:
            source = self._read(path)
            self.assertIn(terminal, source, f"{path}: Apple-touch Web Share must be a terminal return")

    def test_plain_text_selected_share_route_is_terminal(self):
        source = self._read("apps/txt/index.html")
        self.assertIn(
            "if(route==='web-share')return viaShare(blob,fileName,file);",
            source,
            "Plain Text selected Web Share route must be terminal",
        )


if __name__ == "__main__":
    unittest.main()
