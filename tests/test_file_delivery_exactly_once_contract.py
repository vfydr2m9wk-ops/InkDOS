from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FileDeliveryExactlyOnceContractTests(unittest.TestCase):
    def _read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_apple_touch_share_route_is_terminal_for_documents_and_spreadsheets(self):
        cases = (
            ("documents", "if(c.preferShareSave&&c.share)return viaShare(blob,fileName,file)"),
            ("spreadsheets", "if(c.preferShareSave&&c.share)return viaShare(blob,fileName,file,sourceKind)"),
        )
        for app, terminal in cases:
            source = self._read(f"apps/{app}/io/file-delivery.js")
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

    def test_web_share_attempt_is_terminal_suite_wide(self):
        cases = (
            ("apps/documents/io/file-delivery.js", "viaShare(blob,fileName,file).catch", "viaDownload(blob,fileName)"),
            ("apps/spreadsheets/io/file-delivery.js", "viaShare(blob,fileName,file,sourceKind).catch", "viaDownload(blob,fileName,sourceKind)"),
            ("apps/presentations/io/file-delivery.js", "viaShare(blob,name,file)}catch", "download(blob,name)"),
            ("apps/pdf/io/file-delivery.js", "share(blob,name)}catch", "download(blob,name)"),
            ("apps/epub/io/file-delivery.js", "share(blob,name,f).catch", "download(blob,name)"),
            ("apps/txt/runtime/services/file-delivery.js", "viaShare(blob,fileName,file).catch", "viaDownload(blob,fileName)"),
        )
        for path, share_fallback_marker, download_marker in cases:
            source = self._read(path)
            self.assertNotIn(
                share_fallback_marker,
                source,
                f"{path}: once Web Share is invoked, Save must not auto-fallback to another delivery route",
            )
            self.assertIn(download_marker, source, f"{path}: direct download fallback must remain available before Share starts")

    def test_concurrent_save_delivery_is_single_flight_suite_wide(self):
        cases = (
            ("apps/documents/io/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,fileName))"),
            ("apps/spreadsheets/io/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,fileName,options))"),
            ("apps/presentations/io/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,name))"),
            ("apps/pdf/io/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,name))"),
            ("apps/epub/io/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,name))"),
            ("apps/txt/runtime/services/file-delivery.js", "deliveryInFlight", "return singleFlight(()=>deliverOnce(blob,fileName))"),
        )
        for path, state_marker, wrapper_marker in cases:
            source = self._read(path)
            self.assertIn(state_marker, source, f"{path}: must retain one in-flight Save delivery")
            self.assertIn(wrapper_marker, source, f"{path}: concurrent Save calls must share the in-flight delivery")


if __name__ == "__main__":
    unittest.main()
