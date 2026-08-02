from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.data.discover_catalog import (
    MAX_RESPONSE_BYTES,
    REQUIRED_ASSETS,
    _get_json,
    _safe_next_url,
    _sanitize_item,
)
from scripts.data.discover_earth_engine import REQUIRED_BANDS, _exclusive_end, _require_project, _sanitize_feature


class CatalogDiscoveryTests(unittest.TestCase):
    def test_pagination_must_remain_on_the_official_search_endpoint(self) -> None:
        safe = "https://stac.dataspace.copernicus.eu/v1/search?token=next:test"
        self.assertEqual(_safe_next_url(safe), safe)
        for unsafe in (
            "http://stac.dataspace.copernicus.eu/v1/search",
            "https://attacker.example/v1/search",
            "https://stac.dataspace.copernicus.eu/other",
            "https://user:password@stac.dataspace.copernicus.eu/v1/search",
        ):
            with self.assertRaises(RuntimeError):
                _safe_next_url(unsafe)

    def test_item_sanitization_keeps_metadata_but_removes_asset_urls(self) -> None:
        assets = {
            key: {
                "href": "https://example.invalid/signed?token=secret",
                "type": "image/jp2",
                "file:size": 123,
                "file:checksum": "abc",
                "roles": ["data"],
            }
            for key in REQUIRED_ASSETS
        }
        result = _sanitize_item(
            {
                "id": "item-1",
                "collection": "sentinel-2-l2a",
                "bbox": [1, 2, 3, 4],
                "properties": {"datetime": "2024-01-01T00:00:00Z", "eo:cloud_cover": 12},
                "assets": assets,
            }
        )
        self.assertEqual(result["requiredAssetsPresent"], list(REQUIRED_ASSETS))
        self.assertNotIn("href", str(result))
        self.assertNotIn("secret", str(result))

    def test_response_body_is_bounded(self) -> None:
        class Headers:
            @staticmethod
            def get_content_type():
                return "application/geo+json"

            @staticmethod
            def get(name):
                return str(MAX_RESPONSE_BYTES + 1) if name == "Content-Length" else None

        class Response:
            headers = Headers()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

        with patch("scripts.data.discover_catalog.HTTP_OPENER.open", return_value=Response()):
            with self.assertRaisesRegex(RuntimeError, "byte safety limit"):
                _get_json("https://stac.dataspace.copernicus.eu/v1/search")

    def test_earth_engine_project_and_metadata_are_bounded_and_sanitized(self) -> None:
        self.assertEqual(_require_project("orbitwatch-503717"), "orbitwatch-503717")
        with self.assertRaises(ValueError):
            _require_project("../../project")
        self.assertEqual(_exclusive_end("2024-12-31"), "2025-01-01")

        result = _sanitize_feature(
            {
                "properties": {
                    "id": "COPERNICUS/S2_SR_HARMONIZED/example",
                    "datetime": "2024-10-15T05:00:00Z",
                    "cloudCoverPercent": 12.5,
                    "mgrsTile": "43QPG",
                    "bandNames": [*REQUIRED_BANDS, "QA60"],
                    "providerUrl": "https://example.invalid/token=secret",
                }
            }
        )
        self.assertEqual(result["requiredBandsPresent"], list(REQUIRED_BANDS))
        self.assertNotIn("providerUrl", str(result))
        self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()
