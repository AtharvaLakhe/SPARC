from __future__ import annotations

from pathlib import Path
import unittest

from apps.api.app.precomputed_repository import BUILT_UP_CONFLICT_REASON, PrecomputedPackRepository


ROOT = Path(__file__).resolve().parents[2]


class PrecomputedRepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = PrecomputedPackRepository(
            ROOT / "data" / "processed" / "prepublication-packs",
            ROOT / "data" / "processed" / "earth-engine-p0",
            ROOT
            / "data"
            / "metadata"
            / "boundaries"
            / "geoBoundaries-IND-ADM2-76128533"
            / "release-metadata.json",
        )

    def test_catalogue_exposes_reviewed_district_packs(self) -> None:
        regions = self.repository.list_regions("district", None)
        self.assertEqual([region["id"] for region in regions], [
            "district:bengaluru-urban",
            "district:mumbai-city",
            "district:nagpur",
        ])
        self.assertEqual(regions[0]["bbox"], [77.32755, 12.65818, 77.82026, 13.23257])

    def test_mumbai_city_uses_validated_pack_and_keeps_built_up_result(self) -> None:
        summary = self.repository.get_summary("district:mumbai-city")
        detail = self.repository.get_indicator("district:mumbai-city", "built-up")
        assert summary is not None and detail is not None
        self.assertEqual(summary["data"]["region"]["name"], "Mumbai City district")
        self.assertEqual(detail["data"]["status"], "complete")
        self.assertIsNotNone(detail["data"]["metric"]["absoluteChange"])
        self.assertEqual(detail["data"]["provenance"]["analysisCrs"], "EPSG:32643")

    def test_bengaluru_uses_its_own_frozen_period(self) -> None:
        summary = self.repository.get_summary("district:bengaluru-urban")
        assert summary is not None
        self.assertEqual(summary["data"]["baselinePeriod"]["startDate"], "2019-01-15")
        self.assertEqual(summary["data"]["comparisonPeriod"]["startDate"], "2024-01-15")
        self.assertFalse(summary["meta"]["mock"])
        self.assertEqual(summary["meta"]["dataMode"], "cache")

    def test_nagpur_built_up_conflict_remains_unavailable(self) -> None:
        summary = self.repository.get_summary("district:nagpur")
        detail = self.repository.get_indicator("district:nagpur", "built-up")
        assert summary is not None and detail is not None
        built = next(item for item in summary["data"]["indicators"] if item["indicator"]["id"] == "built-up")
        self.assertEqual(built["status"], "unavailable")
        self.assertEqual(built["metric"]["unavailableReason"], BUILT_UP_CONFLICT_REASON)
        self.assertIsNone(detail["data"]["metric"]["absoluteChange"])

    def test_provenance_contains_actual_scene_ids_and_method(self) -> None:
        detail = self.repository.get_indicator("district:nagpur", "surface-water")
        assert detail is not None
        source = detail["data"]["provenance"]["sources"][0]
        self.assertTrue(source["itemIds"])
        self.assertTrue(source["acquiredAt"])
        self.assertEqual(source["collection"], "COPERNICUS/S2_SR_HARMONIZED")
        self.assertEqual(detail["data"]["provenance"]["analysisCrs"], "EPSG:32644")
        self.assertTrue(detail["data"]["provenance"]["parametersHash"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
