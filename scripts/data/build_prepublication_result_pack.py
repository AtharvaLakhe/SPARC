"""Build an immutable, offline-only SPARC pre-publication result pack.

The pack is a review/integration boundary, not an API response. It deliberately
retains unknown quality and incomplete-validation state so current Earth Engine
evidence cannot be mistaken for a released environmental result.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "packages" / "contracts" / "schemas" / "prepublication-result-pack.schema.json"
MAX_REPORT_BYTES = 2 * 1024 * 1024
P0_INDICATORS = ("surface-water", "vegetation", "built-up")
BOUNDARY_DISCLAIMER = "This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary."
SENSITIVITY_DISCLAIMER = "Sensitivity evidence does not calibrate or replace the default green-cover proxy."
PROXY_SENSITIVITY_DISCLAIMER = "Sensitivity evidence does not calibrate or replace the default district proxy."
SENSITIVE_KEY = re.compile(r"(?:api[_-]?key|authorization|bearer|cookie|password|secret|token|signed[_-]?url)", re.IGNORECASE)
DATE_TIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z$")


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _read_report(path: Path) -> tuple[dict[str, Any], str]:
    try:
        if path.stat().st_size > MAX_REPORT_BYTES:
            raise ValueError(f"Report exceeds the {MAX_REPORT_BYTES} byte safety limit: {path}")
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Could not read report: {path}") from exc
    try:
        report = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Report is not UTF-8 JSON: {path}") from exc
    if not isinstance(report, dict):
        raise ValueError(f"Report root must be an object: {path}")
    _reject_sensitive_keys(report, path)
    return report, _sha256_bytes(raw)


def _reject_sensitive_keys(value: Any, path: Path, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"Report has a non-string key at {location}: {path}")
            if SENSITIVE_KEY.search(key):
                raise ValueError(f"Report contains a prohibited credential-like key at {location}.{key}: {path}")
            _reject_sensitive_keys(nested, path, f"{location}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_sensitive_keys(nested, path, f"{location}[{index}]")


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _require_string(value: Any, field: str, *, maximum: int = 300) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} must be a non-empty string up to {maximum} characters")
    return value


def _finite_number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    return result


def _validate_date_time(value: Any, field: str) -> str:
    result = _require_string(value, field, maximum=35)
    if not DATE_TIME.fullmatch(result):
        raise ValueError(f"{field} must be a UTC ISO-8601 timestamp")
    return result


def _normalise_periods(value: Any) -> dict[str, dict[str, Any]]:
    periods = _require_dict(value, "periods")
    normalized: dict[str, dict[str, Any]] = {}
    for label in ("baseline", "comparison"):
        period = _require_dict(periods.get(label), f"periods.{label}")
        start = _require_string(period.get("start"), f"periods.{label}.start", maximum=10)
        end = _require_string(period.get("end"), f"periods.{label}.end", maximum=10)
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", start) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", end):
            raise ValueError(f"periods.{label} must use YYYY-MM-DD dates")
        if start > end or period.get("endInclusive") is not True:
            raise ValueError(f"periods.{label} has invalid bounds or endInclusive flag")
        normalized[label] = {"start": start, "end": end, "endInclusive": True}
    return normalized


def _normalise_sensitivity(value: Any, indicator_id: str) -> dict[str, Any] | None:
    if value is None:
        if indicator_id == "vegetation":
            raise ValueError("Vegetation report is missing completed sensitivity evidence")
        return None
    sensitivity = _require_dict(value, "indicators[].sensitivity")
    if sensitivity.get("status") != "completed-pre-publication":
        raise ValueError(f"{indicator_id} sensitivity is not completed pre-publication evidence")
    batch = _require_dict(sensitivity.get("batchExport"), "sensitivity.batchExport")
    raw_csv_sha = _require_string(batch.get("rawCsvSha256"), "sensitivity.batchExport.rawCsvSha256", maximum=64)
    if not re.fullmatch(r"[a-f0-9]{64}", raw_csv_sha):
        raise ValueError(f"{indicator_id} sensitivity raw CSV checksum is invalid")

    if indicator_id in ("surface-water", "built-up"):
        if sensitivity.get("disclaimer") != PROXY_SENSITIVITY_DISCLAIMER:
            raise ValueError(f"{indicator_id} sensitivity disclaimer is missing or changed")
        method = _require_dict(sensitivity.get("method"), "sensitivity.method")
        alternate = _require_dict(method.get("sensitivity"), "sensitivity.method.sensitivity")
        expected_id = "water-pooled-otsu" if indicator_id == "surface-water" else "built-ibi"
        if alternate.get("id") != expected_id or alternate.get("indicatorId") != indicator_id:
            raise ValueError(f"{indicator_id} sensitivity method is not the documented alternative")
        threshold = _require_string(alternate.get("threshold"), "sensitivity.method.sensitivity.threshold", maximum=120)
        threshold_numeric = _finite_number(alternate.get("thresholdNumeric"), "sensitivity.method.sensitivity.thresholdNumeric")
        row = _require_dict(sensitivity.get("row"), "sensitivity.row")
        areas = _require_dict(row.get("areaSqKm"), "sensitivity.row.areaSqKm")
        net_area = _finite_number(areas.get("net"), "sensitivity.row.areaSqKm.net")
        percent_change = _finite_number(areas.get("percentChange"), "sensitivity.row.areaSqKm.percentChange")
        common_valid_fraction = _finite_number(row.get("commonValidFraction"), "sensitivity.row.commonValidFraction", minimum=0)
        if common_valid_fraction > 1:
            raise ValueError(f"{indicator_id} sensitivity common-valid fraction exceeds 1")
        return {
            "status": "completed-pre-publication",
            "rawCsvSha256": raw_csv_sha,
            "method": {"id": expected_id, "threshold": threshold, "thresholdNumeric": threshold_numeric},
            "row": {
                "netAreaSqKm": net_area,
                "percentChange": percent_change,
                "commonValidFraction": common_valid_fraction,
            },
            "disclaimer": PROXY_SENSITIVITY_DISCLAIMER,
        }

    if indicator_id != "vegetation":
        raise ValueError(f"Unsupported sensitivity-bearing indicator: {indicator_id}")
    if sensitivity.get("disclaimer") != SENSITIVITY_DISCLAIMER:
        raise ValueError("Vegetation sensitivity disclaimer is missing or changed")
    method = _require_dict(sensitivity.get("method"), "sensitivity.method")
    if method.get("indicatorId") != "vegetation" or method.get("thresholds") != [0.2, 0.3, 0.4]:
        raise ValueError("Vegetation sensitivity method does not use the fixed documented thresholds")
    rows = sensitivity.get("rows")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("Vegetation sensitivity must contain exactly three rows")
    normalized_rows: list[dict[str, float]] = []
    observed_thresholds: set[float] = set()
    for index, row in enumerate(rows):
        row_data = _require_dict(row, f"sensitivity.rows[{index}]")
        threshold = _finite_number(row_data.get("threshold"), f"sensitivity.rows[{index}].threshold")
        if threshold not in (0.2, 0.3, 0.4) or threshold in observed_thresholds:
            raise ValueError("Vegetation sensitivity rows must contain each fixed threshold exactly once")
        observed_thresholds.add(threshold)
        areas = _require_dict(row_data.get("areaSqKm"), f"sensitivity.rows[{index}].areaSqKm")
        normalized_rows.append(
            {
                "threshold": threshold,
                "netAreaSqKm": _finite_number(areas.get("net"), f"sensitivity.rows[{index}].areaSqKm.net"),
                "percentChange": _finite_number(areas.get("percentChange"), f"sensitivity.rows[{index}].areaSqKm.percentChange"),
                "commonValidFraction": _finite_number(row_data.get("commonValidFraction"), f"sensitivity.rows[{index}].commonValidFraction", minimum=0),
            }
        )
    if observed_thresholds != {0.2, 0.3, 0.4}:
        raise ValueError("Vegetation sensitivity thresholds are incomplete")
    if any(row["commonValidFraction"] > 1 for row in normalized_rows):
        raise ValueError("Vegetation sensitivity common-valid fraction exceeds 1")
    return {
        "status": "completed-pre-publication",
        "rawCsvSha256": raw_csv_sha,
        "rows": sorted(normalized_rows, key=lambda row: row["threshold"]),
        "disclaimer": SENSITIVITY_DISCLAIMER,
    }


def _normalise_indicator(value: Any) -> dict[str, Any]:
    indicator = _require_dict(value, "indicator")
    indicator_id = indicator.get("indicatorId")
    if indicator_id not in P0_INDICATORS:
        raise ValueError(f"Unsupported P0 indicator: {indicator_id!r}")
    analysis = _require_dict(indicator.get("analysis"), f"{indicator_id}.analysis")
    crs = _require_string(analysis.get("crs"), f"{indicator_id}.analysis.crs", maximum=16)
    if not re.fullmatch(r"EPSG:[0-9]+", crs):
        raise ValueError(f"{indicator_id}.analysis.crs is invalid")
    pixel_size = _finite_number(analysis.get("pixelSizeMetres"), f"{indicator_id}.analysis.pixelSizeMetres", minimum=1)
    minimum_observations = _finite_number(analysis.get("minClearObservations"), f"{indicator_id}.analysis.minClearObservations", minimum=1)
    if not pixel_size.is_integer() or not minimum_observations.is_integer():
        raise ValueError(f"{indicator_id} analysis controls must be integers")

    areas = _require_dict(indicator.get("areaSqKm"), f"{indicator_id}.areaSqKm")
    area = {
        name: _finite_number(
            areas.get(name),
            f"{indicator_id}.areaSqKm.{name}",
            minimum=0 if name not in ("net", "percentChange") else None,
        )
        for name in ("baseline", "comparison", "gain", "loss", "net", "percentChange")
    }
    if area["baseline"] <= 0:
        raise ValueError(f"{indicator_id}.areaSqKm.baseline must be greater than zero")
    if not math.isclose(area["net"], area["comparison"] - area["baseline"], abs_tol=0.000001):
        raise ValueError(f"{indicator_id} net area does not equal comparison minus baseline")
    if not math.isclose(area["net"], area["gain"] - area["loss"], abs_tol=0.000001):
        raise ValueError(f"{indicator_id} net area does not equal gain minus loss")
    expected_percent = 100 * area["net"] / area["baseline"]
    if not math.isclose(area["percentChange"], expected_percent, abs_tol=0.000001):
        raise ValueError(f"{indicator_id} percent change is inconsistent with its areas")

    common_valid = _require_dict(indicator.get("commonValid"), f"{indicator_id}.commonValid")
    boundary_area = _finite_number(common_valid.get("boundaryAreaSqKm"), f"{indicator_id}.commonValid.boundaryAreaSqKm", minimum=0)
    observed_area = _finite_number(common_valid.get("areaSqKm"), f"{indicator_id}.commonValid.areaSqKm", minimum=0)
    fraction = _finite_number(common_valid.get("fraction"), f"{indicator_id}.commonValid.fraction", minimum=0)
    if boundary_area <= 0 or observed_area > boundary_area + 0.000001 or fraction > 1:
        raise ValueError(f"{indicator_id} common-valid coverage is invalid")
    if not math.isclose(fraction, observed_area / boundary_area, abs_tol=0.000001):
        raise ValueError(f"{indicator_id} common-valid fraction is inconsistent with its areas")

    median_index = _require_dict(indicator.get("medianIndex"), f"{indicator_id}.medianIndex")
    normalized_median: dict[str, float | None] = {}
    for period in ("baseline", "comparison"):
        median = median_index.get(period)
        normalized_median[period] = None if median is None else _finite_number(median, f"{indicator_id}.medianIndex.{period}")

    quality = _require_dict(indicator.get("quality"), f"{indicator_id}.quality")
    warnings = quality.get("warnings")
    if quality.get("level") != "unknown" or not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        raise ValueError(f"{indicator_id} must retain unknown quality and textual warnings")
    normalized_warnings = list(warnings)
    if BOUNDARY_DISCLAIMER not in normalized_warnings:
        if len(normalized_warnings) >= 20:
            raise ValueError(f"{indicator_id} has no room for the mandatory boundary disclaimer")
        normalized_warnings.append(BOUNDARY_DISCLAIMER)

    return {
        "indicatorId": indicator_id,
        "methodVersion": _require_string(indicator.get("methodVersion"), f"{indicator_id}.methodVersion", maximum=80),
        "threshold": _require_string(indicator.get("threshold"), f"{indicator_id}.threshold", maximum=120),
        "analysis": {"crs": crs, "pixelSizeMetres": int(pixel_size), "minClearObservations": int(minimum_observations)},
        "areaSqKm": area,
        "commonValid": {"boundaryAreaSqKm": boundary_area, "areaSqKm": observed_area, "fraction": fraction},
        "medianIndex": normalized_median,
        "quality": {"level": "unknown", "warnings": normalized_warnings},
        "sensitivity": _normalise_sensitivity(
            indicator.get("thresholdSensitivity") if indicator_id == "vegetation" else indicator.get("sensitivity"),
            indicator_id,
        ),
    }


def _normalise_report(report: dict[str, Any], path: Path, digest: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    if report.get("manifestVersion") != "1" or report.get("status") != "pre-publication":
        raise ValueError(f"Report is not a version-1 pre-publication report: {path}")
    if report.get("disclaimer") != BOUNDARY_DISCLAIMER:
        raise ValueError(f"Report is missing the mandatory boundary disclaimer: {path}")
    region = _require_dict(report.get("region"), "region")
    normalized_region = {
        "key": _require_string(region.get("key"), "region.key", maximum=80),
        "name": _require_string(region.get("name"), "region.name", maximum=120),
        "boundarySha256": _require_string(region.get("boundarySha256"), "region.boundarySha256", maximum=64),
    }
    if normalized_region["key"] not in ("nagpur", "bengaluru-urban") or not re.fullmatch(r"[a-f0-9]{64}", normalized_region["boundarySha256"]):
        raise ValueError(f"Report region is not an approved district identity: {path}")
    source = _require_dict(report.get("source"), "source")
    if source.get("provider") != "Google Earth Engine" or source.get("collection") != "COPERNICUS/S2_SR_HARMONIZED":
        raise ValueError(f"Report does not use the approved Earth Engine Sentinel-2 collection: {path}")
    indicators = report.get("indicators")
    if not isinstance(indicators, list) or not indicators:
        raise ValueError(f"Report has no indicators: {path}")
    normalized_indicators = [_normalise_indicator(indicator) for indicator in indicators]
    batch_export = report.get("batchExport")
    batch_task = None
    if batch_export is not None:
        batch = _require_dict(batch_export, "batchExport")
        raw_csv_sha = _require_string(batch.get("rawCsvSha256"), "batchExport.rawCsvSha256", maximum=64)
        if not re.fullmatch(r"[a-f0-9]{64}", raw_csv_sha):
            raise ValueError("batchExport raw CSV checksum is invalid")
        batch_task = {
            "description": batch.get("taskDescription"),
            "id": batch.get("taskId"),
            "rawCsvSha256": raw_csv_sha,
        }
        for field in ("description", "id"):
            if batch_task[field] is not None and (not isinstance(batch_task[field], str) or len(batch_task[field]) > 160):
                raise ValueError(f"batchExport {field} must be null or a bounded string")
    digest_record = {
        "fileName": path.name,
        "sha256": digest,
        "reportCreatedAt": _validate_date_time(report.get("createdAt"), "createdAt"),
        "batchTask": batch_task,
    }
    return normalized_region, normalized_indicators, {
        "periods": _normalise_periods(report.get("periods")),
        "sourceProvider": source["provider"],
        "sourceCollection": source["collection"],
        "digest": digest_record,
    }


def _load_schema() -> dict[str, Any]:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read result-pack schema: {SCHEMA_PATH}") from exc


def _validate_pack(pack: dict[str, Any]) -> None:
    validator = Draft202012Validator(_load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(pack), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.path) or "$"
        raise ValueError(f"Pre-publication pack schema validation failed at {location}: {error.message}")


def assemble_pack(reports: list[tuple[Path, dict[str, Any], str]]) -> dict[str, Any]:
    """Validate in-memory reports and return the immutable pack payload.

    Keeping assembly separate from file output lets callers inspect all evidence
    before a new immutable artifact is created.
    """

    if not reports:
        raise ValueError("At least one pre-publication report is required")
    first_region: dict[str, Any] | None = None
    first_periods: dict[str, Any] | None = None
    first_source: tuple[str, str] | None = None
    indicators: list[dict[str, Any]] = []
    digests: list[dict[str, Any]] = []
    seen_indicators: set[str] = set()
    seen_filenames: set[str] = set()
    for path, report, digest in reports:
        if path.name in seen_filenames:
            raise ValueError(f"Report filename is duplicated: {path.name}")
        seen_filenames.add(path.name)
        _reject_sensitive_keys(report, path)
        region, report_indicators, context = _normalise_report(report, path, digest)
        if first_region is None:
            first_region = region
            first_periods = context["periods"]
            first_source = (context["sourceProvider"], context["sourceCollection"])
        elif region != first_region or context["periods"] != first_periods or (context["sourceProvider"], context["sourceCollection"]) != first_source:
            raise ValueError("All reports in a pack must have the same approved region, periods, and source collection")
        for indicator in report_indicators:
            if indicator["indicatorId"] in seen_indicators:
                raise ValueError(f"Indicator is duplicated across reports: {indicator['indicatorId']}")
            seen_indicators.add(indicator["indicatorId"])
            indicators.append(indicator)
        digests.append(context["digest"])

    included = [indicator for indicator in P0_INDICATORS if indicator in seen_indicators]
    pack = {
        "packVersion": "1",
        "status": "pre-publication",
        "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "region": first_region,
        "periods": first_periods,
        "coverage": {
            "expectedIndicators": list(P0_INDICATORS),
            "includedIndicators": included,
            "allExpectedIndicatorsPresent": len(included) == len(P0_INDICATORS),
        },
        "indicators": sorted(indicators, key=lambda item: P0_INDICATORS.index(item["indicatorId"])),
        "validation": {
            "independentValidation": "NOT_COMPLETED",
            # The sole exploratory label frame is Nagpur-specific. A vegetation
            # report in another district must never inherit that evidence.
            "vegetationLabelFrame": (
                "EXPLORATORY_REVIEW_ONLY"
                if first_region["key"] == "nagpur" and "vegetation" in seen_indicators
                else "NOT_APPLICABLE"
            ),
        },
        "provenance": {"sourceProvider": first_source[0], "sourceCollection": first_source[1], "reportDigests": digests},
        "disclaimer": BOUNDARY_DISCLAIMER,
    }
    _validate_pack(pack)
    return pack


def build_pack(report_paths: list[Path], output_path: Path) -> dict[str, Any]:
    """Create one non-overwritable pack from trusted local report files."""

    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite immutable result pack: {output_path}")
    reports: list[tuple[Path, dict[str, Any], str]] = []
    for path in report_paths:
        report, digest = _read_report(path)
        reports.append((path, report, digest))
    pack = assemble_pack(reports)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(pack, indent=2, ensure_ascii=False) + "\n"
    try:
        with output_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
    except FileExistsError:
        raise FileExistsError(f"Refusing to overwrite immutable result pack: {output_path}") from None
    return pack


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an offline-only immutable pre-publication result pack")
    parser.add_argument("--report", type=Path, action="append", required=True, help="Validated local P0 report; repeat for each indicator")
    parser.add_argument("--output", type=Path, required=True, help="New pack path; an existing file is never overwritten")
    args = parser.parse_args()
    pack = build_pack(args.report, args.output)
    print(f"built {pack['status']} pack for {pack['region']['key']} at {args.output}")


if __name__ == "__main__":
    main()
