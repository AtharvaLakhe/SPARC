"""Tests for importing a completed Earth Engine P0 batch-export CSV."""

from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.data.process_earth_engine_p0 import (
    BUILT_IBI_SENSITIVITY_ID,
    EXPLORATORY_VALIDATION_POINTS_PER_STRATUM,
    EXPLORATORY_VALIDATION_SEED,
    VALIDATION_SAMPLING_UNIT,
    VALIDATION_STRATA,
    VEGETATION_SENSITIVITY_THRESHOLDS,
    WATER_OTSU_HISTOGRAM,
    WATER_OTSU_SENSITIVITY_ID,
    _pooled_otsu_threshold_from_histograms,
    _validation_frame_method,
    _validation_frame_task_description,
    _validation_population_task_description,
    _vegetation_threshold_label,
    import_alternative_sensitivity,
    import_batch_export,
    import_validation_frame_populations,
    import_vegetation_sensitivity,
    import_water_otsu_histogram,
)


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

    def _sensitivity_request(self) -> dict:
        request = self._request()
        request["task"] = {"description": "sparc_nagpur_vegetation_p0_sensitivity_v1", "id": "task-sensitivity"}
        request["method"] = {"vegetationSensitivityThresholds": [0.2, 0.3, 0.4]}
        return request

    def _sensitivity_row(self, threshold: float) -> dict[str, str]:
        row = self._export_row()
        row["sensitivityThreshold"] = str(threshold)
        row["threshold"] = f"NDVI >= {threshold:.2f}"
        return row

    def _alternative_sensitivity_request(self, sensitivity_id: str) -> dict:
        request = self._request()
        if sensitivity_id == WATER_OTSU_SENSITIVITY_ID:
            request["task"] = {"description": "sparc_nagpur_surface-water_p0_water-pooled-otsu_v1", "id": "task-water"}
            request["indicatorIds"] = ["surface-water"]
            request["method"] = {
                "sensitivity": {
                    "id": sensitivity_id,
                    "indicatorId": "surface-water",
                    "methodVersion": "p0-mndwi-pooled-otsu-sensitivity-v1",
                    "threshold": "MNDWI > 0.00390645 (pooled Otsu)",
                    "thresholdNumeric": 0.00390645,
                    "histogram": WATER_OTSU_HISTOGRAM,
                }
            }
        else:
            request["task"] = {"description": "sparc_nagpur_built-up_p0_built-ibi_v1", "id": "task-built"}
            request["indicatorIds"] = ["built-up"]
            request["method"] = {
                "sensitivity": {
                    "id": BUILT_IBI_SENSITIVITY_ID,
                    "indicatorId": "built-up",
                    "methodVersion": "p0-ibi-l0.5-positive-sensitivity-v1",
                    "threshold": "IBI > 0 (SAVI L = 0.5)",
                    "thresholdNumeric": 0.0,
                }
            }
        return request

    def _alternative_sensitivity_row(self, sensitivity_id: str) -> dict[str, str]:
        row = self._export_row()
        if sensitivity_id == WATER_OTSU_SENSITIVITY_ID:
            row.update({
                "indicatorId": "surface-water",
                "methodVersion": "p0-mndwi-fixed-zero-v1",
                "pixelSizeMetres": "20",
                "threshold": "MNDWI > 0.00390645 (pooled Otsu)",
                "sensitivityId": sensitivity_id,
                "sensitivityMethodVersion": "p0-mndwi-pooled-otsu-sensitivity-v1",
                "sensitivityThresholdNumeric": "0.00390645",
            })
        else:
            row.update({
                "indicatorId": "built-up",
                "methodVersion": "p0-constrained-ndbi-v1",
                "pixelSizeMetres": "20",
                "threshold": "IBI > 0 (SAVI L = 0.5)",
                "sensitivityId": BUILT_IBI_SENSITIVITY_ID,
                "sensitivityMethodVersion": "p0-ibi-l0.5-positive-sensitivity-v1",
                "sensitivityThresholdNumeric": "0",
            })
        return row

    def _water_histogram_request(self) -> dict:
        request = self._alternative_sensitivity_request(WATER_OTSU_SENSITIVITY_ID)
        request["task"] = {"description": "sparc_nagpur_surface-water_p0_water-pooled-otsu_histogram_v1", "id": "task-histogram"}
        request["method"]["sensitivity"].pop("threshold")
        request["method"]["sensitivity"].pop("thresholdNumeric")
        return request

    def _water_histogram_rows(self) -> list[dict[str, str]]:
        minimum = WATER_OTSU_HISTOGRAM["minimum"]
        width = (WATER_OTSU_HISTOGRAM["maximum"] - minimum) / WATER_OTSU_HISTOGRAM["buckets"]
        rows = []
        for bucket in range(WATER_OTSU_HISTOGRAM["buckets"]):
            rows.append({
                "bucket": str(bucket),
                "lowerEdge": str(minimum + bucket * width),
                "baselineCount": "10" if bucket == 100 else "0",
                "comparisonCount": "10" if bucket == 150 else "0",
                "boundarySha256": BOUNDARY_SHA,
                "analysisCrs": "EPSG:32644",
                "pixelSizeMetres": "20",
                "minClearObservations": "2",
                "histogramMinimum": str(minimum),
                "histogramMaximum": str(WATER_OTSU_HISTOGRAM["maximum"]),
                "histogramBuckets": str(WATER_OTSU_HISTOGRAM["buckets"]),
            })
        return rows

    def _validation_population_request(self) -> dict:
        return {
            "task": {
                "description": "sparc_nagpur_vegetation_validation_frame_populations_default_v2",
                "id": "task-populations",
            },
            "region": {"key": "nagpur", "boundarySha256": BOUNDARY_SHA},
            "method": {
                "indicatorId": "vegetation",
                "mapMethod": {
                    "id": "default",
                    "methodVersion": "p0-ndvi-green-cover-v1",
                    "threshold": "NDVI >= 0.30",
                },
                "analysisCrs": "EPSG:32644",
                "pixelSizeMetres": 10,
                "minClearObservations": 2,
                "samplingUnit": VALIDATION_SAMPLING_UNIT,
                "strata": {str(code): name for code, name in VALIDATION_STRATA.items()},
                "designStatus": "STRATA_DISCOVERY_ONLY",
            },
        }

    def _validation_population_rows(self) -> list[dict[str, str]]:
        return [
            {
                "stratum": str(code),
                "stratumName": name,
                "populationPixels": str(100 + code),
                "indicatorId": "vegetation",
                "mapMethodId": "default",
                "mapMethodVersion": "p0-ndvi-green-cover-v1",
                "boundarySha256": BOUNDARY_SHA,
                "analysisCrs": "EPSG:32644",
                "pixelSizeMetres": "10",
                "minClearObservations": "2",
                "samplingUnit": VALIDATION_SAMPLING_UNIT,
                "designStatus": "STRATA_DISCOVERY_ONLY",
            }
            for code, name in VALIDATION_STRATA.items()
        ]

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

    def test_vegetation_sensitivity_thresholds_are_fixed_and_labelled(self) -> None:
        self.assertEqual(VEGETATION_SENSITIVITY_THRESHOLDS, (0.20, 0.30, 0.40))
        self.assertEqual(_vegetation_threshold_label(0.20), "NDVI >= 0.20")
        self.assertEqual(_vegetation_threshold_label(0.40), "NDVI >= 0.40")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            _vegetation_threshold_label(0.25)

    def test_imports_each_documented_vegetation_sensitivity_threshold_once(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        with (
            patch(
                "scripts.data.process_earth_engine_p0._read_export_rows",
                return_value=[self._sensitivity_row(threshold) for threshold in VEGETATION_SENSITIVITY_THRESHOLDS],
            ),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._sensitivity_request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="2" * 64),
        ):
            report = import_vegetation_sensitivity(Path("sensitivity.csv"), Path("request.json"))

        self.assertEqual([row["threshold"] for row in report["rows"]], [0.2, 0.3, 0.4])
        self.assertEqual(report["batchExport"]["taskId"], "task-sensitivity")

    def test_imports_vegetation_sensitivity_for_each_approved_region(self) -> None:
        boundary_sha = "b" * 64
        request = self._sensitivity_request()
        request["region"] = {"key": "bengaluru-urban", "boundarySha256": boundary_sha}
        rows = [self._sensitivity_row(threshold) for threshold in VEGETATION_SENSITIVITY_THRESHOLDS]
        for row in rows:
            row["boundarySha256"] = boundary_sha
            row["analysisCrs"] = "EPSG:32643"
        with (
            patch("scripts.data.process_earth_engine_p0._read_export_rows", return_value=rows),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=request),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, {"boundary": {"sha256": boundary_sha}})),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="5" * 64),
        ):
            report = import_vegetation_sensitivity(
                Path("sensitivity.csv"),
                Path("request.json"),
                region="bengaluru-urban",
            )

        self.assertEqual(report["region"]["key"], "bengaluru-urban")
        self.assertEqual(report["method"]["fixedControls"]["analysisCrs"], "EPSG:32643")

    def test_exploratory_validation_frame_configuration_is_fixed(self) -> None:
        self.assertEqual(EXPLORATORY_VALIDATION_POINTS_PER_STRATUM, 25)
        self.assertEqual(EXPLORATORY_VALIDATION_SEED, 20_260_803)

    def test_built_validation_frames_are_separate_and_frozen_to_one_rule(self) -> None:
        default = _validation_frame_method("built-up", None)
        ibi = _validation_frame_method("built-up", BUILT_IBI_SENSITIVITY_ID)

        self.assertEqual(default["id"], "default")
        self.assertEqual(default["methodVersion"], "p0-constrained-ndbi-v1")
        self.assertEqual(ibi["id"], BUILT_IBI_SENSITIVITY_ID)
        self.assertEqual(ibi["methodVersion"], "p0-ibi-l0.5-positive-sensitivity-v2")
        self.assertIn("denominator", ibi["validityGuard"])
        self.assertEqual(
            _validation_frame_task_description("built-up", None),
            "sparc_nagpur_built-up_validation_frame_default_v1",
        )
        self.assertEqual(
            _validation_frame_task_description("built-up", BUILT_IBI_SENSITIVITY_ID),
            "sparc_nagpur_built-up_validation_frame_built-ibi-v2_v1",
        )
        with self.assertRaisesRegex(ValueError, "Only the documented"):
            _validation_frame_method("vegetation", BUILT_IBI_SENSITIVITY_ID)

    def test_validation_population_import_records_finite_stratum_counts(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        with (
            patch("scripts.data.process_earth_engine_p0._read_export_rows", return_value=self._validation_population_rows()),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._validation_population_request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="6" * 64),
        ):
            evidence = import_validation_frame_populations(
                "nagpur",
                "vegetation",
                Path("population.csv"),
                Path("request.json"),
            )

        self.assertEqual(evidence["status"], "FRAME_DISCOVERED_NOT_SAMPLED")
        self.assertEqual(evidence["batchExport"]["taskId"], "task-populations")
        self.assertEqual([row["populationPixels"] for row in evidence["strata"]], [100, 101, 102, 103])
        self.assertEqual(evidence["strata"][0]["populationAreaSqKm"], 0.01)
        self.assertEqual(
            _validation_population_task_description("nagpur", "vegetation", None),
            "sparc_nagpur_vegetation_validation_frame_populations_default_v2",
        )

    def test_validation_population_import_rejects_non_integer_population(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        rows = self._validation_population_rows()
        rows[0]["populationPixels"] = "100.5"
        with (
            patch("scripts.data.process_earth_engine_p0._read_export_rows", return_value=rows),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._validation_population_request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
        ):
            with self.assertRaisesRegex(ValueError, "non-negative integer"):
                import_validation_frame_populations(
                    "nagpur",
                    "vegetation",
                    Path("population.csv"),
                    Path("request.json"),
                )

    def test_pooled_otsu_uses_locked_histogram_bins_and_both_periods(self) -> None:
        minimum = WATER_OTSU_HISTOGRAM["minimum"]
        width = (WATER_OTSU_HISTOGRAM["maximum"] - minimum) / WATER_OTSU_HISTOGRAM["buckets"]
        baseline = [[minimum + index * width, 0] for index in range(WATER_OTSU_HISTOGRAM["buckets"])]
        comparison = [[minimum + index * width, 0] for index in range(WATER_OTSU_HISTOGRAM["buckets"])]
        baseline[100][1] = 10
        comparison[150][1] = 10

        threshold = _pooled_otsu_threshold_from_histograms(baseline, comparison)

        self.assertAlmostEqual(threshold, minimum + (101.5 * width))
        comparison[150][0] += width
        with self.assertRaisesRegex(ValueError, "bucket edges"):
            _pooled_otsu_threshold_from_histograms(baseline, comparison)

    def test_imports_documented_water_sensitivity_only_when_request_and_csv_agree(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        request = self._alternative_sensitivity_request(WATER_OTSU_SENSITIVITY_ID)
        with (
            patch("scripts.data.process_earth_engine_p0._read_single_export_row", return_value=self._alternative_sensitivity_row(WATER_OTSU_SENSITIVITY_ID)),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=request),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="3" * 64),
        ):
            report = import_alternative_sensitivity(
                "nagpur", "surface-water", WATER_OTSU_SENSITIVITY_ID, Path("water.csv"), Path("request.json")
            )

        self.assertEqual(report["method"]["sensitivity"]["id"], WATER_OTSU_SENSITIVITY_ID)
        self.assertEqual(report["batchExport"]["taskId"], "task-water")

    def test_imports_complete_locked_water_histogram_before_deriving_threshold(self) -> None:
        approved_manifest = {"boundary": {"sha256": BOUNDARY_SHA}}
        with (
            patch("scripts.data.process_earth_engine_p0._read_export_rows", return_value=self._water_histogram_rows()),
            patch("scripts.data.process_earth_engine_p0._read_json", return_value=self._water_histogram_request()),
            patch("scripts.data.process_earth_engine_p0._load_region_geometry", return_value=({}, approved_manifest)),
            patch("scripts.data.process_earth_engine_p0._sha256_file", return_value="4" * 64),
        ):
            evidence = import_water_otsu_histogram(Path("histogram.csv"), Path("request.json"))

        self.assertEqual(evidence["method"]["id"], WATER_OTSU_SENSITIVITY_ID)
        self.assertEqual(evidence["batchExport"]["taskId"], "task-histogram")


if __name__ == "__main__":
    unittest.main()
