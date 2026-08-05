"""Tests for the offline-only pre-publication result-pack boundary."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.data.build_prepublication_result_pack import (
    BOUNDARY_DISCLAIMER,
    PROXY_SENSITIVITY_DISCLAIMER,
    SENSITIVITY_DISCLAIMER,
    assemble_pack,
    build_pack,
)


BOUNDARY_SHA = "f811022adbe26c7634ba4d884db3251c53bd2d23b8d55e18f6d24fe3cb3b2b33"
BENGALURU_BOUNDARY_SHA = "613c9f5da9e207d2acec5796488754abf0d2e48a6b341f5c0de25cbdc3ffa67a"
RAW_CSV_SHA = "4" * 64


class PrepublicationResultPackTests(unittest.TestCase):
    def _indicator(self, indicator_id: str) -> dict:
        indicator = {
            "indicatorId": indicator_id,
            "methodVersion": f"p0-{indicator_id}-v1",
            "threshold": "documented threshold",
            "analysis": {"crs": "EPSG:32644", "pixelSizeMetres": 20, "minClearObservations": 2},
            "areaSqKm": {"baseline": 10.0, "comparison": 9.0, "gain": 1.0, "loss": 2.0, "net": -1.0, "percentChange": -10.0},
            "commonValid": {"boundaryAreaSqKm": 12.0, "areaSqKm": 11.0, "fraction": 11 / 12},
            "medianIndex": {"baseline": 0.6, "comparison": 0.5},
            "quality": {"level": "unknown", "warnings": ["Pre-publication result.", BOUNDARY_DISCLAIMER]},
        }
        if indicator_id == "vegetation":
            indicator["analysis"]["pixelSizeMetres"] = 10
            indicator["thresholdSensitivity"] = {
                "status": "completed-pre-publication",
                "batchExport": {"rawCsvSha256": RAW_CSV_SHA},
                "method": {"indicatorId": "vegetation", "thresholds": [0.2, 0.3, 0.4]},
                "rows": [
                    {"threshold": 0.2, "areaSqKm": {"net": -0.1, "percentChange": -1.0}, "commonValidFraction": 11 / 12},
                    {"threshold": 0.3, "areaSqKm": {"net": -1.0, "percentChange": -10.0}, "commonValidFraction": 11 / 12},
                    {"threshold": 0.4, "areaSqKm": {"net": -2.0, "percentChange": -20.0}, "commonValidFraction": 11 / 12},
                ],
                "disclaimer": SENSITIVITY_DISCLAIMER,
            }
        return indicator

    def _report(self, indicator_id: str) -> dict:
        return {
            "manifestVersion": "1",
            "createdAt": "2026-08-03T00:00:00Z",
            "status": "pre-publication",
            "region": {"key": "nagpur", "name": "Nagpur", "boundarySha256": BOUNDARY_SHA},
            "periods": {
                "baseline": {"start": "2019-10-15", "end": "2019-12-15", "endInclusive": True},
                "comparison": {"start": "2024-10-15", "end": "2024-12-15", "endInclusive": True},
            },
            "source": {"provider": "Google Earth Engine", "collection": "COPERNICUS/S2_SR_HARMONIZED"},
            "indicators": [self._indicator(indicator_id)],
            "disclaimer": BOUNDARY_DISCLAIMER,
        }

    def _assembly_input(self, indicator_id: str) -> tuple[Path, dict, str]:
        return Path(f"nagpur-{indicator_id}.json"), self._report(indicator_id), "a" * 64

    def test_builds_non_publication_pack_and_preserves_validation_limits(self) -> None:
        reports = [self._assembly_input(indicator) for indicator in ("surface-water", "vegetation", "built-up")]
        pack = assemble_pack(reports)

        self.assertEqual(pack["status"], "pre-publication")
        self.assertTrue(pack["coverage"]["allExpectedIndicatorsPresent"])
        self.assertEqual(pack["validation"]["independentValidation"], "NOT_COMPLETED")
        self.assertEqual(pack["validation"]["vegetationLabelFrame"], "EXPLORATORY_REVIEW_ONLY")
        self.assertEqual([item["indicatorId"] for item in pack["indicators"]], ["surface-water", "vegetation", "built-up"])
        self.assertEqual(pack["indicators"][1]["sensitivity"]["rows"][1]["netAreaSqKm"], -1.0)
        self.assertNotIn("rawCsv", pack["indicators"][1]["sensitivity"])

    def test_rejects_report_with_mismatched_boundary(self) -> None:
        water = self._assembly_input("surface-water")
        vegetation = self._assembly_input("vegetation")
        vegetation[1]["region"]["boundarySha256"] = "0" * 64

        with self.assertRaisesRegex(ValueError, "pinned checksum"):
            assemble_pack([water, vegetation])

    def test_does_not_apply_nagpur_label_frame_to_bengaluru_vegetation(self) -> None:
        report = self._report("vegetation")
        report["region"] = {
            "key": "bengaluru-urban",
            "name": "Bengaluru Urban",
            "boundarySha256": BENGALURU_BOUNDARY_SHA,
        }
        report["periods"] = {
            "baseline": {"start": "2019-01-15", "end": "2019-03-15", "endInclusive": True},
            "comparison": {"start": "2024-01-15", "end": "2024-03-15", "endInclusive": True},
        }
        report["indicators"][0]["analysis"]["crs"] = "EPSG:32643"

        pack = assemble_pack([(Path("bengaluru-urban-vegetation.json"), report, "b" * 64)])

        self.assertEqual(pack["validation"]["vegetationLabelFrame"], "NOT_APPLICABLE")

    def test_preserves_validated_built_proxy_sensitivity_without_relaxing_pack_schema(self) -> None:
        built = self._assembly_input("built-up")
        built[1]["indicators"][0]["sensitivity"] = {
            "status": "completed-pre-publication",
            "batchExport": {"rawCsvSha256": RAW_CSV_SHA},
            "method": {
                "indicatorId": "built-up",
                "defaultMethodVersion": "p0-constrained-ndbi-v1",
                "sensitivity": {
                    "id": "built-ibi",
                    "indicatorId": "built-up",
                    "methodVersion": "p0-ibi-l0.5-positive-sensitivity-v2",
                    "threshold": "IBI > 0 (SAVI L = 0.5)",
                    "thresholdNumeric": 0.0,
                },
            },
            "row": {"areaSqKm": {"net": -1.0, "percentChange": -10.0}, "commonValidFraction": 11 / 12},
            "disclaimer": PROXY_SENSITIVITY_DISCLAIMER,
        }

        pack = assemble_pack([built])

        sensitivity = pack["indicators"][0]["sensitivity"]
        self.assertEqual(sensitivity["method"]["id"], "built-ibi")
        self.assertEqual(sensitivity["row"]["netAreaSqKm"], -1.0)

    def test_rejects_credential_like_key_and_never_overwrites(self) -> None:
        water = self._assembly_input("surface-water")
        water[1]["source"]["apiKey"] = "not-allowed"
        with self.assertRaisesRegex(ValueError, "credential-like"):
            assemble_pack([water])

        with patch("scripts.data.build_prepublication_result_pack.Path.exists", return_value=True):
            with self.assertRaises(FileExistsError):
                build_pack([Path("unreadable.json")], Path("already-exists.json"))


if __name__ == "__main__":
    unittest.main()
