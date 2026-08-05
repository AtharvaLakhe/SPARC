from __future__ import annotations

import json
import unittest

from apps.api.reporting.gemini_narrative import generate_narrative, safe_context


class _Response:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self):
        return json.dumps({"candidates": [{"content": {"parts": [{"text": "Requested inspection."}]}}]}).encode()


class GeminiNarrativeTests(unittest.TestCase):
    def test_context_excludes_sensitive_fields_and_exact_coordinates(self) -> None:
        context = safe_context({
            "regionId": "district:nagpur", "coordinates": {"longitude": 79, "latitude": 21},
            "observation": "water appears different", "complainant": {"name": "Private"},
            "attachments": [{"name": "photo.png"}], "issueCodes": ["WATER_BODY_SHRINKAGE"],
        })
        encoded = json.dumps(context)
        self.assertNotIn("Private", encoded)
        self.assertNotIn("79", encoded)
        self.assertNotIn("attachments", encoded)

    def test_generate_narrative_uses_server_key_and_parses_text(self) -> None:
        captured = {}
        def opener(req, timeout):
            captured["key"] = req.headers.get("X-goog-api-key")
            captured["body"] = json.loads(req.data.decode())
            return _Response()
        result = generate_narrative({"observation": "check this"}, api_key="secret", model="gemini-test", opener=opener)
        self.assertEqual(result["text"], "Requested inspection.")
        self.assertEqual(captured["key"], "secret")
        self.assertIn("contents", captured["body"])


if __name__ == "__main__":
    unittest.main()

