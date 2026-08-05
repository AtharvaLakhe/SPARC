from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.data.prepare_city_boundaries import ROOT, _read_json
from scripts.data.validate_boundary_gate import validate_boundary_gate


class CityBoundaryPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.release = _read_json(ROOT / "data/metadata/boundaries/global/release-metadata.json")

    def test_all_requested_cities_have_gated_boundaries(self) -> None:
        expected = {
            "mumbai", "delhi", "chennai", "bhopal", "new-york", "washington-dc",
            "tokyo", "london", "cairo", "sydney", "rio-de-janeiro", "reykjavik",
        }
        self.assertEqual(set(self.release["cities"]), expected)
        for slug, record in self.release["cities"].items():
            boundary = ROOT / record["validatedGeoJson"]
            provenance = ROOT / record["provenance"]
            gate_path = ROOT / record["boundaryGate"]
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            checked = validate_boundary_gate(boundary, provenance)
            self.assertEqual(checked["boundary"]["sha256"], gate["boundary"]["sha256"], slug)
            self.assertEqual(record["boundarySha256"], gate["boundary"]["sha256"], slug)
            self.assertEqual(gate["boundary"]["crs"], "EPSG:4326", slug)
            self.assertTrue(gate["provenance"]["redistributionPermitted"], slug)

    def test_city_selections_are_pinned_and_not_nearest_feature_guesses(self) -> None:
        for slug, record in self.release["cities"].items():
            self.assertTrue(record["selectedShapeIds"], slug)
            self.assertEqual(len(record["selectedShapeIds"]), len(record["selectedShapeNames"]), slug)
            self.assertTrue(record["sourceSha256"], slug)
            self.assertIn("geoBoundaries gbOpen", _read_json(ROOT / record["provenance"])["sourceName"])


if __name__ == "__main__":
    unittest.main()
