"""Tests for importing a completed Earth Engine P0 batch-export CSV."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.data.process_earth_engine_p0 import import_batch_export


BOUNDARY_SHA = "f811022adbe26c7634ba4d884db3251c53bd2d23b8d55e18f6d24fe3cb3b2b33"
class EarthEngineP0ImportTests(unittest.TestCase):
    def _request(self) -> dict:
        return {
            "task": {"description": "sparc_nagpur_vegetation_p0_v1", "id": "task-1"},
            "region": {"key": "nagpur", "boundarySha256": BOUNDARY_SHA},
            "indicatorIds": ["vegetation"],
            "periods": {
                "baseline": {"start": "2019-10-15", "end": "2019-12-15", "endInclusive": True},
                "comparison": {"start": "2024-10-15", "end": "2024-12-15", "endInclusive": True},
            },
            "source": {
                "provider": "Google Earth Engine",
                "collection": "COPERNICUS/S2_SR_HARMONIZED",
                "baselineImages": [],
                "comparisonImages": [],
            },
        }

    def _export_row(self, boundary_sha: str = BOUNDARY_SHA) -> dict[str, str]:
        return {
            "analysisCrs": "EPSG:32644",
            "baselineAreaSqM": "1000000",
            "baselineMedianIndex": "0.6",
            "boundaryAreaSqM": "1200000",
            "boundarySha256": boundary_sha,
            "commonValidAreaSqM": "1100000",
            "comparisonAreaSqM": "900000",
            "comparisonMedianIndex": "0.5",
            "gainAreaSqM": "100000",
            "indicatorId": "vegetation",
            "lossAreaSqM": "200000",
            "methodVersion": "p0-ndvi-green-cover-v1",
            "minClearObservations": "2",
            "netAreaSqM": "-100000",
            "percentChange": "-10",
            "pixelSizeMetres": "10",
            "threshold": "NDVI >= 0.30",
        }

    def test_import_validates_and_converts_batch_summary(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        with (
            patch("scripts.data.process_earth_engine_p0._read_single_export_row", return_value=self._export_row()),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="1" * 64),
        ):
            report = import_batch_export("nagpur", "vegetation", Path("vegetation.csv"), Path("request.json"))

        indicator = report["indicators"][0]
        self.assertEqual(report["status"], "pre-publication")
        self.assertEqual(report["batchExport"]["taskId"], "task-1")
        self.assertEqual(indicator["analysis"]["pixelSizeMetres"], 10)
        self.assertEqual(indicator["areaSqKm"]["net"], -0.1)
        self.assertEqual(indicator["commonValid"]["fraction"], 1100000 / 1200000)

    def test_import_rejects_mismatched_boundary_checksum(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        with (
            patch(
                "scripts.data.process_earth_engine_p0._read_single_export_row",
                return_value=self._export_row("0" * 64),
            ),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
        ):
            with self.assertRaisesRegex(ValueError, "boundary checksum"):
                import_batch_export("nagpur", "vegetation", Path("vegetation.csv"), Path("request.json"))


if __name__ == "__main__":
    unittest.main()
