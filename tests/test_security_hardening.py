from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_audit_module():
    path = ROOT / "scripts" / "audit_source.py"
    spec = importlib.util.spec_from_file_location("inkdesk_audit_source", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SecurityHardeningTests(unittest.TestCase):
    def test_postmessage_scanner_handles_nested_multiline_and_optional_calls(self):
        audit = load_audit_module()
        source = """
        frame.postMessage({type: 'x', values: [1, 2]}, '*');
        frame.postMessage(variable, "*");
        frame.postMessage(build(one, two), '*');
        frame?.postMessage(function(){ return call(a, b); }, '*');
        frame.postMessage?.(
          make({nested: [one, two]}),
          `*`
        );
        frame.postMessage({safe: true}, expectedOrigin);
        """
        calls = audit.find_wildcard_postmessage_calls(source)
        self.assertEqual(len(calls), 5)
        self.assertEqual([call.line for call in calls], [2, 3, 4, 5, 6])

    def test_runtime_has_one_documented_opaque_origin_exception(self):
        audit = load_audit_module()
        source = (ROOT / "shared" / "file-router.js").read_text(encoding="utf-8")
        calls = audit.find_wildcard_postmessage_calls(source)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].allowed_opaque_exception)
        self.assertIn("event.origin===policy.expectedOrigin", source)
        self.assertIn("event.source!==frame.contentWindow", source)
        self.assertIn("event.source!==global.parent", source)
        self.assertIn("BRIDGE_TIMEOUT_MS", source)
        self.assertIn("inkdesk:file-received", source)
        self.assertIn("removeEventListener('message'", source)

    def test_service_worker_uses_explicit_cache_keys_and_reports_failures(self):
        source = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        self.assertNotIn("ignoreSearch", source)
        self.assertNotIn("catch(()=>{})", source)
        self.assertIn("canonicalCacheKey", source)
        self.assertIn("isCacheableShellRequest", source)
        self.assertIn("incomplete cache was removed", source)
        self.assertIn("inkdesk:clear-app-cache", source)
        self.assertIn("inkdesk-shell-v0.19.2-beta-router2", source)


if __name__ == "__main__":
    unittest.main()
