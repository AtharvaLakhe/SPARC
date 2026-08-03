"""Tests for the boundary licensing and GeoJSON validation gate."""

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.data.validate_boundary_gate import BoundaryGateError, validate_boundary_gate


def _feature() -> dict:
    return {
        "type": "Feature",
        "properties": {"district": "test"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[79.0, 21.0], [80.0, 21.0], [80.0, 22.0], [79.0, 21.0]]],
        },
    }


def _provenance() -> dict:
    return {
        "sourceName": "Approved boundary authority",
        "sourceUrl": "https://authority.example/district-boundaries",
        "version": "2026-08",
        "license": "Approved redistribution terms",
        "attribution": "Contains modified boundary data from Approved boundary authority.",
        "redistributionPermitted": True,
    }


class BoundaryGateTests(unittest.TestCase):
    def _validate(self, boundary: dict, provenance: dict) -> dict:
        boundary_bytes = json.dumps(boundary, sort_keys=True).encode("utf-8")
        provenance_bytes = json.dumps(provenance, sort_keys=True).encode("utf-8")
        with patch(
            "scripts.data.validate_boundary_gate._read_json",
            side_effect=[(boundary, boundary_bytes), (provenance, provenance_bytes)],
        ):
            return validate_boundary_gate(Path("district.geojson"), Path("provenance.json"))

    def test_approved_polygon_yields_stable_non_sensitive_manifest(self) -> None:
        manifest = self._validate(_feature(), _provenance())

        self.assertEqual(manifest["boundary"]["geometryType"], "Polygon")
        self.assertEqual(manifest["boundary"]["bbox"], [79.0, 21.0, 80.0, 22.0])
        self.assertEqual(len(manifest["boundary"]["sha256"]), 64)
        self.assertNotIn("path", manifest["boundary"])

    def test_missing_redistribution_permission_blocks_processing(self) -> None:
        provenance = _provenance()
        provenance["redistributionPermitted"] = False
        with self.assertRaisesRegex(BoundaryGateError, "redistributionPermitted"):
            self._validate(_feature(), provenance)

    def test_open_ring_or_invalid_coordinate_blocks_processing(self) -> None:
        boundary = _feature()
        boundary["geometry"]["coordinates"][0][-1] = [181.0, 21.0]
        with self.assertRaisesRegex(BoundaryGateError, "longitude/latitude"):
            self._validate(boundary, _provenance())


if __name__ == "__main__":
    unittest.main()
