"""Compute bounded, pre-publication P0 summaries with Google Earth Engine."""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
from typing import Any

from .discover_catalog import PILOTS
from .discover_earth_engine import COLLECTION, MAX_IMAGES, _exclusive_end, _initialize, _require_project
from .validate_boundary_gate import BoundaryGateError, validate_boundary_gate


MIN_CLEAR_OBSERVATIONS = 2
ALLOWED_SCL_VALUES = (4, 5, 6)
VEGETATION_SENSITIVITY_THRESHOLDS = (0.20, 0.30, 0.40)
EXPLORATORY_VALIDATION_POINTS_PER_STRATUM = 25
EXPLORATORY_VALIDATION_SEED = 20_260_803
DRIVE_FOLDER_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
REGIONS = {
    "nagpur": {
        "boundary": Path("data/validated/boundaries/geoBoundaries-IND-ADM2-76128533/nagpur.geojson"),
        "provenance": Path("data/metadata/boundaries/geoBoundaries-IND-ADM2-76128533/nagpur.provenance.json"),
        "gate": Path("data/metadata/boundaries/geoBoundaries-IND-ADM2-76128533/nagpur.boundary-gate.json"),
        "analysisCrs": "EPSG:32644",
    },
    "bengaluru-urban": {
        "boundary": Path("data/validated/boundaries/geoBoundaries-IND-ADM2-76128533/bengaluru-urban.geojson"),
        "provenance": Path("data/metadata/boundaries/geoBoundaries-IND-ADM2-76128533/bengaluru-urban.provenance.json"),
        "gate": Path("data/metadata/boundaries/geoBoundaries-IND-ADM2-76128533/bengaluru-urban.boundary-gate.json"),
        "analysisCrs": "EPSG:32643",
    },
}
INDICATORS = {
    "surface-water": {
        "scaleMetres": 20,
        "indexBands": ("mndwi",),
        "threshold": "MNDWI > 0",
        "methodVersion": "p0-mndwi-fixed-zero-v1",
    },
    "vegetation": {
        "scaleMetres": 10,
        "indexBands": ("ndvi",),
        "threshold": "NDVI >= 0.30",
        "methodVersion": "p0-ndvi-green-cover-v1",
    },
    "built-up": {
        "scaleMetres": 20,
        "indexBands": ("ndbi", "mndwi", "ndvi"),
        "threshold": "NDBI > 0 AND MNDWI <= 0 AND NDVI < 0.30",
        "methodVersion": "p0-constrained-ndbi-v1",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryGateError(f"Could not read required boundary record: {path}") from exc


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_region_geometry(region: str) -> tuple[dict[str, Any], dict[str, Any]]:
    files = REGIONS[region]
    gate = _read_json(files["gate"])
    manifest = validate_boundary_gate(files["boundary"], files["provenance"])
    if manifest["boundary"]["sha256"] != gate.get("boundary", {}).get("sha256"):
        raise BoundaryGateError(f"Boundary checksum no longer matches the approved gate for {region}")
    feature = _read_json(files["boundary"])
    if feature.get("type") != "Feature" or not isinstance(feature.get("geometry"), dict):
        raise BoundaryGateError(f"Validated boundary is not a GeoJSON feature for {region}")
    return feature["geometry"], manifest


def _observable_mask(image: Any) -> Any:
    scl = image.select("SCL")
    mask = scl.eq(ALLOWED_SCL_VALUES[0])
    for value in ALLOWED_SCL_VALUES[1:]:
        mask = mask.Or(scl.eq(value))
    return mask


def _indices_for_image(ee: Any, image: Any, indicator_id: str) -> Any:
    image = ee.Image(image)
    observable = _observable_mask(image)
    reflectance = image.select(["B3", "B4", "B8", "B11"]).multiply(0.0001)
    mndwi = reflectance.normalizedDifference(["B3", "B11"]).rename("mndwi")
    ndvi = reflectance.normalizedDifference(["B8", "B4"]).rename("ndvi")
    if indicator_id == "surface-water":
        result = mndwi
    elif indicator_id == "vegetation":
        result = ndvi
    elif indicator_id == "built-up":
        ndbi = reflectance.normalizedDifference(["B11", "B8"]).rename("ndbi")
        result = ee.Image.cat([ndbi, mndwi, ndvi])
    else:
        raise ValueError(f"Unknown indicator: {indicator_id}")
    return result.updateMask(observable).copyProperties(
        image, ["system:index", "system:time_start", "PROCESSING_BASELINE", "CLOUDY_PIXEL_PERCENTAGE"]
    )


def _source_metadata(ee: Any, collection: Any) -> list[dict[str, Any]]:
    def as_feature(image: Any) -> Any:
        image = ee.Image(image)
        return ee.Feature(
            None,
            {
                "id": image.id(),
                "datetime": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd'T'HH:mm:ss'Z'"),
                "cloudCoverPercent": image.get("CLOUDY_PIXEL_PERCENTAGE"),
                "mgrsTile": image.get("MGRS_TILE"),
                "processingBaseline": image.get("PROCESSING_BASELINE"),
            },
        )

    info = ee.FeatureCollection(collection.map(as_feature)).getInfo()
    features = info.get("features") if isinstance(info, dict) else None
    if not isinstance(features, list):
        raise RuntimeError("Earth Engine did not return source-image metadata")
    return sorted((feature.get("properties", {}) for feature in features), key=lambda item: item.get("datetime", ""))


def _period_collection(ee: Any, geometry: Any, start: str, end: str) -> Any:
    collection = (
        ee.ImageCollection(COLLECTION)
        .filterBounds(geometry)
        .filterDate(start, _exclusive_end(end))
        .sort("system:time_start")
    )
    count = collection.size().getInfo()
    if not isinstance(count, int) or count < 1 or count > MAX_IMAGES:
        raise RuntimeError(f"Unexpected image count for {start} to {end}: {count}")
    return collection


def _period_composite(ee: Any, collection: Any, indicator_id: str) -> dict[str, Any]:
    index_bands = list(INDICATORS[indicator_id]["indexBands"])

    def mapper(image: Any) -> Any:
        return _indices_for_image(ee, image, indicator_id)

    indexed = collection.map(mapper)
    observation_count = indexed.select(index_bands[0]).count().unmask(0).rename("observationCount")
    return {
        "median": indexed.median(),
        "valid": observation_count.gte(MIN_CLEAR_OBSERVATIONS),
        "observationCount": observation_count,
    }


def _area_statistics(ee: Any, baseline_class: Any, comparison_class: Any, common_valid: Any, geometry: Any, scale: int, crs: str) -> dict[str, float]:
    result = _area_statistics_lazy(ee, baseline_class, comparison_class, common_valid, geometry, scale, crs).getInfo()
    return {name: float((result or {}).get(name, 0.0)) for name in ("boundary", "commonValid", "baseline", "comparison", "gain", "loss")}


def _median_indices(ee: Any, baseline: Any, comparison: Any, common_valid: Any, geometry: Any, scale: int, crs: str) -> dict[str, float | None]:
    result = _median_indices_lazy(ee, baseline, comparison, common_valid, geometry, scale, crs).getInfo()
    return {
        name: float(value) if isinstance(value := (result or {}).get(name), (int, float)) else None
        for name in ("baseline", "comparison")
    }


def _vegetation_threshold_label(threshold: float) -> str:
    if threshold not in VEGETATION_SENSITIVITY_THRESHOLDS:
        raise ValueError(f"Unsupported vegetation sensitivity threshold: {threshold}")
    return f"NDVI >= {threshold:.2f}"


def _classification(ee: Any, indicator_id: str, median: Any, *, vegetation_threshold: float | None = None) -> Any:
    if indicator_id == "surface-water":
        return median.select("mndwi").gt(0)
    if indicator_id == "vegetation":
        threshold = 0.30 if vegetation_threshold is None else vegetation_threshold
        return median.select("ndvi").gte(threshold)
    if indicator_id == "built-up":
        return (
            median.select("ndbi")
            .gt(0)
            .And(median.select("mndwi").lte(0))
            .And(median.select("ndvi").lt(0.30))
        )
    raise ValueError(f"Unknown indicator: {indicator_id}")


def _indicator_summary(
    ee: Any,
    indicator_id: str,
    geometry: Any,
    baseline_collection: Any,
    comparison_collection: Any,
    analysis_crs: str,
) -> dict[str, Any]:
    config = INDICATORS[indicator_id]
    scale = int(config["scaleMetres"])
    baseline = _period_composite(ee, baseline_collection, indicator_id)
    comparison = _period_composite(ee, comparison_collection, indicator_id)
    common_valid = baseline["valid"].And(comparison["valid"])
    baseline_class = _classification(ee, indicator_id, baseline["median"]).updateMask(common_valid)
    comparison_class = _classification(ee, indicator_id, comparison["median"]).updateMask(common_valid)
    areas = _area_statistics(ee, baseline_class, comparison_class, common_valid, geometry, scale, analysis_crs)
    boundary_area_sq_m = areas["boundary"]
    common_area_sq_m = areas["commonValid"]
    baseline_area_sq_m = areas["baseline"]
    comparison_area_sq_m = areas["comparison"]
    gain_area_sq_m = areas["gain"]
    loss_area_sq_m = areas["loss"]
    median_band = INDICATORS[indicator_id]["indexBands"][0]
    median_indexes = _median_indices(
        ee,
        baseline["median"].select(median_band),
        comparison["median"].select(median_band),
        common_valid,
        geometry,
        scale,
        analysis_crs,
    )
    percent_change = (
        None if baseline_area_sq_m == 0 else 100 * (comparison_area_sq_m - baseline_area_sq_m) / baseline_area_sq_m
    )
    return {
        "indicatorId": indicator_id,
        "methodVersion": config["methodVersion"],
        "threshold": config["threshold"],
        "analysis": {"crs": analysis_crs, "pixelSizeMetres": scale, "minClearObservations": MIN_CLEAR_OBSERVATIONS},
        "areaSqKm": {
            "baseline": baseline_area_sq_m / 1_000_000,
            "comparison": comparison_area_sq_m / 1_000_000,
            "gain": gain_area_sq_m / 1_000_000,
            "loss": loss_area_sq_m / 1_000_000,
            "net": (comparison_area_sq_m - baseline_area_sq_m) / 1_000_000,
            "percentChange": percent_change,
        },
        "commonValid": {
            "boundaryAreaSqKm": boundary_area_sq_m / 1_000_000,
            "areaSqKm": common_area_sq_m / 1_000_000,
            "fraction": None if boundary_area_sq_m == 0 else common_area_sq_m / boundary_area_sq_m,
        },
        "medianIndex": median_indexes,
        "quality": {
            "level": "unknown",
            "warnings": [
                "Pre-publication result: independent validation and threshold sensitivity are not complete.",
                "This is a prototype analysis boundary, not an authoritative legal or cadastral boundary.",
            ],
        },
    }


def _indicator_export_feature(
    ee: Any,
    indicator_id: str,
    geometry: Any,
    baseline_collection: Any,
    comparison_collection: Any,
    analysis_crs: str,
    boundary_sha256: str,
    *,
    vegetation_threshold: float | None = None,
) -> Any:
    """Build one lazy Earth Engine feature for an asynchronous CSV export.

    This deliberately mirrors ``_indicator_summary`` without calling ``getInfo``.
    It is used when a full-resolution regional reduction exceeds an interactive
    request deadline. The export computes the same scalar statistics in Earth
    Engine's batch system; it does not relax the scale, masks, or threshold.
    """

    config = INDICATORS[indicator_id]
    if vegetation_threshold is not None and indicator_id != "vegetation":
        raise ValueError("Vegetation sensitivity thresholds can only be exported for the vegetation indicator")
    threshold_label = (
        config["threshold"] if vegetation_threshold is None else _vegetation_threshold_label(vegetation_threshold)
    )
    scale = int(config["scaleMetres"])
    baseline = _period_composite(ee, baseline_collection, indicator_id)
    comparison = _period_composite(ee, comparison_collection, indicator_id)
    common_valid = baseline["valid"].And(comparison["valid"])
    baseline_class = _classification(
        ee, indicator_id, baseline["median"], vegetation_threshold=vegetation_threshold
    ).updateMask(common_valid)
    comparison_class = _classification(
        ee, indicator_id, comparison["median"], vegetation_threshold=vegetation_threshold
    ).updateMask(common_valid)
    areas = _area_statistics_lazy(ee, baseline_class, comparison_class, common_valid, geometry, scale, analysis_crs)
    median_band = INDICATORS[indicator_id]["indexBands"][0]
    median_indexes = _median_indices_lazy(
        ee,
        baseline["median"].select(median_band),
        comparison["median"].select(median_band),
        common_valid,
        geometry,
        scale,
        analysis_crs,
    )
    baseline_area = ee.Number(areas.get("baseline"))
    comparison_area = ee.Number(areas.get("comparison"))
    return ee.Feature(
        None,
        {
            "indicatorId": indicator_id,
            "methodVersion": config["methodVersion"],
            "threshold": threshold_label,
            "sensitivityThreshold": vegetation_threshold,
            "boundarySha256": boundary_sha256,
            "analysisCrs": analysis_crs,
            "pixelSizeMetres": scale,
            "minClearObservations": MIN_CLEAR_OBSERVATIONS,
            "boundaryAreaSqM": areas.get("boundary"),
            "commonValidAreaSqM": areas.get("commonValid"),
            "baselineAreaSqM": baseline_area,
            "comparisonAreaSqM": comparison_area,
            "gainAreaSqM": areas.get("gain"),
            "lossAreaSqM": areas.get("loss"),
            "netAreaSqM": comparison_area.subtract(baseline_area),
            "percentChange": ee.Algorithms.If(
                baseline_area.eq(0), None, comparison_area.subtract(baseline_area).divide(baseline_area).multiply(100)
            ),
            "baselineMedianIndex": median_indexes.get("baseline"),
            "comparisonMedianIndex": median_indexes.get("comparison"),
        },
    )


def _area_statistics_lazy(
    ee: Any,
    baseline_class: Any,
    comparison_class: Any,
    common_valid: Any,
    geometry: Any,
    scale: int,
    crs: str,
) -> Any:
    pixel_area = ee.Image.pixelArea()
    areas = ee.Image.cat(
        [
            pixel_area.rename("boundary"),
            pixel_area.updateMask(common_valid).rename("commonValid"),
            pixel_area.updateMask(baseline_class).rename("baseline"),
            pixel_area.updateMask(comparison_class).rename("comparison"),
            pixel_area.updateMask(baseline_class.Not().And(comparison_class)).rename("gain"),
            pixel_area.updateMask(baseline_class.And(comparison_class.Not())).rename("loss"),
        ]
    )
    return areas.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        crs=crs,
        scale=scale,
        maxPixels=10_000_000_000,
        tileScale=4,
    )


def _median_indices_lazy(
    ee: Any,
    baseline: Any,
    comparison: Any,
    common_valid: Any,
    geometry: Any,
    scale: int,
    crs: str,
) -> Any:
    return ee.Image.cat([baseline.rename("baseline"), comparison.rename("comparison")]).updateMask(common_valid).reduceRegion(
        reducer=ee.Reducer.median(),
        geometry=geometry,
        crs=crs,
        scale=scale,
        maxPixels=10_000_000_000,
        tileScale=4,
    )


def create_batch_export(
    project: str,
    region: str,
    indicator_ids: tuple[str, ...],
    drive_folder: str,
    output_dir: Path,
    *,
    start: bool,
    vegetation_sensitivity_thresholds: tuple[float, ...] | None = None,
) -> dict[str, Any]:
    """Create an explicitly guarded Earth Engine table-export task.

    ``start=False`` is intentionally side-effect-free: it writes a local request
    record and prints the exact task that would be created. Starting an export
    creates external state in the account's Google Drive and therefore requires
    both a destination and an explicit CLI flag.
    """

    if not DRIVE_FOLDER_PATTERN.fullmatch(drive_folder):
        raise ValueError("--drive-folder must contain 1–80 letters, numbers, hyphens, or underscores")
    if vegetation_sensitivity_thresholds:
        if indicator_ids != ("vegetation",):
            raise ValueError("Vegetation sensitivity export requires exactly --indicator vegetation")
        if tuple(vegetation_sensitivity_thresholds) != VEGETATION_SENSITIVITY_THRESHOLDS:
            raise ValueError("Vegetation sensitivity export must use the documented 0.20, 0.30, and 0.40 thresholds")
    ee = _initialize(project)
    boundary_geometry, boundary_manifest = _load_region_geometry(region)
    analysis_crs = REGIONS[region]["analysisCrs"]
    geometry = ee.Geometry(boundary_geometry, "EPSG:4326", False)
    pilot = PILOTS[region]
    baseline_start, baseline_end = pilot.periods[0]
    comparison_start, comparison_end = pilot.periods[1]
    baseline_collection = _period_collection(ee, geometry, baseline_start, baseline_end)
    comparison_collection = _period_collection(ee, geometry, comparison_start, comparison_end)
    baseline_sources = _source_metadata(ee, baseline_collection)
    comparison_sources = _source_metadata(ee, comparison_collection)
    task_description = f"sparc_{region}_{'_'.join(indicator_ids)}_p0"
    task_description += "_sensitivity_v1" if vegetation_sensitivity_thresholds else "_v1"
    request = {
        "manifestVersion": "1",
        "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "started" if start else "dry-run",
        "task": {
            "description": task_description,
            "destination": "Google Drive",
            "driveFolder": drive_folder,
            "fileNamePrefix": task_description,
            "fileFormat": "CSV",
        },
        "region": {
            "key": region,
            "name": pilot.name,
            "boundarySha256": boundary_manifest["boundary"]["sha256"],
        },
        "periods": {
            "baseline": {"start": baseline_start, "end": baseline_end, "endInclusive": True},
            "comparison": {"start": comparison_start, "end": comparison_end, "endInclusive": True},
        },
        "indicatorIds": list(indicator_ids),
        "method": {
            "collection": COLLECTION,
            "sclAllowedValues": list(ALLOWED_SCL_VALUES),
            "minClearObservations": MIN_CLEAR_OBSERVATIONS,
            "notes": "Batch task preserves full-resolution statistics after an interactive reduction timeout.",
            "vegetationSensitivityThresholds": list(vegetation_sensitivity_thresholds or ()),
        },
        "source": {
            "provider": "Google Earth Engine",
            "collection": COLLECTION,
            "baselineImages": baseline_sources,
            "comparisonImages": comparison_sources,
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / f"{task_description}.batch-request.json"
    request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    features = []
    for indicator_id in indicator_ids:
        thresholds = (
            vegetation_sensitivity_thresholds
            if indicator_id == "vegetation" and vegetation_sensitivity_thresholds
            else (None,)
        )
        features.extend(
            _indicator_export_feature(
                ee,
                indicator_id,
                geometry,
                baseline_collection,
                comparison_collection,
                analysis_crs,
                boundary_manifest["boundary"]["sha256"],
                vegetation_threshold=threshold,
            )
            for threshold in thresholds
        )
    task = ee.batch.Export.table.toDrive(
        collection=ee.FeatureCollection(features),
        description=task_description,
        folder=drive_folder,
        fileNamePrefix=task_description,
        fileFormat="CSV",
    )
    if not start:
        return request

    task.start()
    request["task"]["id"] = task.id
    request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return request


def create_vegetation_validation_sample_export(
    project: str,
    drive_folder: str,
    output_dir: Path,
    *,
    start: bool,
) -> dict[str, Any]:
    """Export a blinded exploratory label frame for the fixed Nagpur vegetation map.

    The export omits mapped classes and NDVI values so an annotator can label
    reference evidence without seeing the candidate classification. It is a
    exploratory sample frame, not completed independent validation.
    """

    if not DRIVE_FOLDER_PATTERN.fullmatch(drive_folder):
        raise ValueError("--drive-folder must contain 1–80 letters, numbers, hyphens, or underscores")
    ee = _initialize(project)
    boundary_geometry, boundary_manifest = _load_region_geometry("nagpur")
    analysis_crs = REGIONS["nagpur"]["analysisCrs"]
    geometry = ee.Geometry(boundary_geometry, "EPSG:4326", False)
    pilot = PILOTS["nagpur"]
    baseline_start, baseline_end = pilot.periods[0]
    comparison_start, comparison_end = pilot.periods[1]
    baseline_collection = _period_collection(ee, geometry, baseline_start, baseline_end)
    comparison_collection = _period_collection(ee, geometry, comparison_start, comparison_end)
    baseline = _period_composite(ee, baseline_collection, "vegetation")
    comparison = _period_composite(ee, comparison_collection, "vegetation")
    common_valid = baseline["valid"].And(comparison["valid"])
    baseline_class = _classification(ee, "vegetation", baseline["median"]).updateMask(common_valid)
    comparison_class = _classification(ee, "vegetation", comparison["median"]).updateMask(common_valid)
    stable_target = baseline_class.And(comparison_class)
    gain = baseline_class.Not().And(comparison_class)
    loss = baseline_class.And(comparison_class.Not())
    strata = (
        ee.Image(0)
        .where(stable_target, 1)
        .where(gain, 2)
        .where(loss, 3)
        .rename("stratum")
        .toInt()
        .updateMask(common_valid)
    )
    samples = strata.stratifiedSample(
        numPoints=EXPLORATORY_VALIDATION_POINTS_PER_STRATUM,
        classBand="stratum",
        region=geometry,
        scale=10,
        projection=analysis_crs,
        seed=EXPLORATORY_VALIDATION_SEED,
        classValues=[0, 1, 2, 3],
        classPoints=[EXPLORATORY_VALIDATION_POINTS_PER_STRATUM] * 4,
        dropNulls=True,
        tileScale=4,
        geometries=True,
    )

    def blind_sample(feature: Any) -> Any:
        coordinates = ee.List(ee.Feature(feature).geometry().coordinates())
        sample_id = ee.String(ee.Number(coordinates.get(0)).format("%.6f")).cat("_").cat(
            ee.Number(coordinates.get(1)).format("%.6f")
        )
        return ee.Feature(
            ee.Feature(feature).geometry(),
            {
                "sampleId": sample_id,
                "inclusionProbability": None,
                "design": "exploratory-stratified-25-per-mapped-stratum",
                "referenceStatus": "UNLABELLED",
            },
        )

    blinded_samples = samples.map(blind_sample)
    task_description = "sparc_nagpur_vegetation_validation_frame_v1"
    request = {
        "manifestVersion": "1",
        "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "started" if start else "dry-run",
        "task": {
            "description": task_description,
            "destination": "Google Drive",
            "driveFolder": drive_folder,
            "fileNamePrefix": task_description,
            "fileFormat": "CSV",
        },
        "region": {
            "key": "nagpur",
            "boundarySha256": boundary_manifest["boundary"]["sha256"],
        },
        "method": {
            "indicatorId": "vegetation",
            "methodVersion": INDICATORS["vegetation"]["methodVersion"],
            "threshold": INDICATORS["vegetation"]["threshold"],
            "analysisCrs": analysis_crs,
            "pixelSizeMetres": 10,
            "minClearObservations": MIN_CLEAR_OBSERVATIONS,
            "commonValidOnly": True,
            "strata": {
                "0": "stable-non-target",
                "1": "stable-target",
                "2": "mapped-gain",
                "3": "mapped-loss",
            },
            "targetPointsPerStratum": EXPLORATORY_VALIDATION_POINTS_PER_STRATUM,
            "seed": EXPLORATORY_VALIDATION_SEED,
            "blindedExport": True,
            "status": "EXPLORATORY_REVIEW_ONLY",
        },
        "periods": {
            "baseline": {"start": baseline_start, "end": baseline_end, "endInclusive": True},
            "comparison": {"start": comparison_start, "end": comparison_end, "endInclusive": True},
        },
        "disclaimer": "This is an unlabeled exploratory sample frame, not completed independent validation.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    request_path = output_dir / f"{task_description}.batch-request.json"
    request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    task = ee.batch.Export.table.toDrive(
        collection=blinded_samples,
        description=task_description,
        folder=drive_folder,
        fileNamePrefix=task_description,
        fileFormat="CSV",
    )
    if not start:
        return request
    task.start()
    request["task"]["id"] = task.id
    request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return request


def _required_csv_float(row: dict[str, str], field: str) -> float:
    value = row.get(field)
    try:
        parsed = float(value) if value not in (None, "") else math.nan
    except ValueError as exc:
        raise ValueError(f"Batch CSV field {field!r} is not a number") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"Batch CSV field {field!r} must be finite")
    return parsed


def _read_export_rows(path: Path) -> list[dict[str, str]]:
    try:
        if path.stat().st_size > 1024 * 1024:
            raise ValueError("Batch CSV exceeds the 1 MiB safety limit")
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ValueError(f"Could not read batch CSV: {path}") from exc
    if not rows:
        raise ValueError("Batch CSV must contain at least one summary row")
    return rows


def _read_single_export_row(path: Path) -> dict[str, str]:
    rows = _read_export_rows(path)
    if len(rows) != 1:
        raise ValueError(f"Batch CSV must contain exactly one summary row, found {len(rows)}")
    return rows[0]


def _validated_sensitivity_row(row: dict[str, str], boundary_sha256: str) -> dict[str, Any]:
    threshold = _required_csv_float(row, "sensitivityThreshold")
    if threshold not in VEGETATION_SENSITIVITY_THRESHOLDS:
        raise ValueError("Sensitivity CSV has an unapproved threshold")
    if row.get("indicatorId") != "vegetation" or row.get("methodVersion") != INDICATORS["vegetation"]["methodVersion"]:
        raise ValueError("Sensitivity CSV indicator or method version does not match the approved method")
    if row.get("threshold") != _vegetation_threshold_label(threshold):
        raise ValueError("Sensitivity CSV threshold label does not match its numeric threshold")
    if row.get("boundarySha256") != boundary_sha256:
        raise ValueError("Sensitivity CSV boundary checksum does not match the approved boundary")
    if row.get("analysisCrs") != REGIONS["nagpur"]["analysisCrs"]:
        raise ValueError("Sensitivity CSV analysis CRS does not match the approved region CRS")
    if _required_csv_float(row, "pixelSizeMetres") != float(INDICATORS["vegetation"]["scaleMetres"]):
        raise ValueError("Sensitivity CSV pixel size does not match the approved method")
    if _required_csv_float(row, "minClearObservations") != float(MIN_CLEAR_OBSERVATIONS):
        raise ValueError("Sensitivity CSV observation floor does not match the approved method")

    areas = {field: _required_csv_float(row, field) for field in (
        "boundaryAreaSqM", "commonValidAreaSqM", "baselineAreaSqM", "comparisonAreaSqM", "gainAreaSqM", "lossAreaSqM", "netAreaSqM"
    )}
    if min(areas[name] for name in ("boundaryAreaSqM", "commonValidAreaSqM", "baselineAreaSqM", "comparisonAreaSqM", "gainAreaSqM", "lossAreaSqM")) < 0:
        raise ValueError("Sensitivity CSV contains a negative area")
    if areas["commonValidAreaSqM"] > areas["boundaryAreaSqM"] + 1:
        raise ValueError("Sensitivity CSV common-valid area exceeds the boundary area")
    if not math.isclose(areas["netAreaSqM"], areas["comparisonAreaSqM"] - areas["baselineAreaSqM"], abs_tol=1):
        raise ValueError("Sensitivity CSV net area does not equal comparison minus baseline")
    if not math.isclose(areas["netAreaSqM"], areas["gainAreaSqM"] - areas["lossAreaSqM"], abs_tol=1):
        raise ValueError("Sensitivity CSV net area does not equal gain minus loss")
    percent_change = _required_csv_float(row, "percentChange")
    expected_percent = 100 * areas["netAreaSqM"] / areas["baselineAreaSqM"] if areas["baselineAreaSqM"] else None
    if expected_percent is None or not math.isclose(percent_change, expected_percent, abs_tol=1e-9):
        raise ValueError("Sensitivity CSV percent change is inconsistent with its baseline and net area")
    return {
        "threshold": threshold,
        "thresholdLabel": row["threshold"],
        "areaSqKm": {
            "baseline": areas["baselineAreaSqM"] / 1_000_000,
            "comparison": areas["comparisonAreaSqM"] / 1_000_000,
            "gain": areas["gainAreaSqM"] / 1_000_000,
            "loss": areas["lossAreaSqM"] / 1_000_000,
            "net": areas["netAreaSqM"] / 1_000_000,
            "percentChange": percent_change,
        },
        "commonValidFraction": areas["commonValidAreaSqM"] / areas["boundaryAreaSqM"],
    }


def import_vegetation_sensitivity(csv_path: Path, batch_request_path: Path) -> dict[str, Any]:
    """Validate the fixed three-threshold vegetation sensitivity batch export."""

    rows = _read_export_rows(csv_path)
    request = _read_json(batch_request_path)
    _, boundary_manifest = _load_region_geometry("nagpur")
    boundary_sha256 = boundary_manifest["boundary"]["sha256"]
    if request.get("region", {}).get("key") != "nagpur" or request.get("region", {}).get("boundarySha256") != boundary_sha256:
        raise ValueError("Sensitivity batch request does not match the approved Nagpur boundary")
    if request.get("indicatorIds") != ["vegetation"]:
        raise ValueError("Sensitivity batch request does not match the vegetation indicator")
    if request.get("method", {}).get("vegetationSensitivityThresholds") != list(VEGETATION_SENSITIVITY_THRESHOLDS):
        raise ValueError("Sensitivity batch request does not contain the documented threshold set")
    if len(rows) != len(VEGETATION_SENSITIVITY_THRESHOLDS):
        raise ValueError("Sensitivity CSV must contain exactly the three documented threshold rows")
    validated_rows = [_validated_sensitivity_row(row, boundary_sha256) for row in rows]
    if {item["threshold"] for item in validated_rows} != set(VEGETATION_SENSITIVITY_THRESHOLDS):
        raise ValueError("Sensitivity CSV must contain each documented threshold exactly once")
    return {
        "status": "completed-pre-publication",
        "region": {"key": "nagpur", "boundarySha256": boundary_sha256},
        "batchExport": {
            "taskDescription": request.get("task", {}).get("description"),
            "taskId": request.get("task", {}).get("id"),
            "rawCsv": csv_path.as_posix(),
            "rawCsvSha256": _sha256_file(csv_path),
        },
        "method": {
            "indicatorId": "vegetation",
            "methodVersion": INDICATORS["vegetation"]["methodVersion"],
            "thresholds": list(VEGETATION_SENSITIVITY_THRESHOLDS),
            "fixedControls": {"analysisCrs": REGIONS["nagpur"]["analysisCrs"], "pixelSizeMetres": 10, "minClearObservations": MIN_CLEAR_OBSERVATIONS},
        },
        "rows": sorted(validated_rows, key=lambda item: item["threshold"]),
        "disclaimer": "Sensitivity evidence does not calibrate or replace the default green-cover proxy.",
    }


def import_batch_export(
    region: str,
    indicator_id: str,
    csv_path: Path,
    batch_request_path: Path,
) -> dict[str, Any]:
    """Validate a completed Earth Engine CSV and convert it to a local report."""

    if region not in REGIONS or indicator_id not in INDICATORS:
        raise ValueError("Unknown region or indicator")
    row = _read_single_export_row(csv_path)
    request = _read_json(batch_request_path)
    boundary_geometry, boundary_manifest = _load_region_geometry(region)
    del boundary_geometry
    config = INDICATORS[indicator_id]
    request_region = request.get("region", {})
    request_task = request.get("task", {})
    if request_region.get("key") != region or request_region.get("boundarySha256") != boundary_manifest["boundary"]["sha256"]:
        raise ValueError("Batch request does not match the approved region boundary")
    if request.get("indicatorIds") != [indicator_id]:
        raise ValueError("Batch request does not match the requested indicator")
    if row.get("indicatorId") != indicator_id or row.get("methodVersion") != config["methodVersion"]:
        raise ValueError("Batch CSV indicator or method version does not match the approved method")
    if row.get("boundarySha256") != boundary_manifest["boundary"]["sha256"]:
        raise ValueError("Batch CSV boundary checksum does not match the approved boundary")
    if row.get("analysisCrs") != REGIONS[region]["analysisCrs"]:
        raise ValueError("Batch CSV analysis CRS does not match the approved region CRS")
    if row.get("threshold") != config["threshold"]:
        raise ValueError("Batch CSV threshold does not match the approved method")
    if _required_csv_float(row, "pixelSizeMetres") != float(config["scaleMetres"]):
        raise ValueError("Batch CSV pixel size does not match the approved method")
    if _required_csv_float(row, "minClearObservations") != float(MIN_CLEAR_OBSERVATIONS):
        raise ValueError("Batch CSV observation floor does not match the approved method")

    boundary_area = _required_csv_float(row, "boundaryAreaSqM")
    common_valid_area = _required_csv_float(row, "commonValidAreaSqM")
    baseline_area = _required_csv_float(row, "baselineAreaSqM")
    comparison_area = _required_csv_float(row, "comparisonAreaSqM")
    gain_area = _required_csv_float(row, "gainAreaSqM")
    loss_area = _required_csv_float(row, "lossAreaSqM")
    net_area = _required_csv_float(row, "netAreaSqM")
    percent_change = _required_csv_float(row, "percentChange")
    if min(boundary_area, common_valid_area, baseline_area, comparison_area, gain_area, loss_area) < 0:
        raise ValueError("Batch CSV contains a negative area")
    if common_valid_area > boundary_area + 1:
        raise ValueError("Batch CSV common-valid area exceeds the boundary area")
    if not math.isclose(net_area, comparison_area - baseline_area, abs_tol=1):
        raise ValueError("Batch CSV net area does not equal comparison minus baseline")
    if not math.isclose(net_area, gain_area - loss_area, abs_tol=1):
        raise ValueError("Batch CSV net area does not equal gain minus loss")
    expected_percent = 100 * net_area / baseline_area if baseline_area else None
    if expected_percent is None or not math.isclose(percent_change, expected_percent, abs_tol=1e-9):
        raise ValueError("Batch CSV percent change is inconsistent with its baseline and net area")

    pilot = PILOTS[region]
    return {
        "manifestVersion": "1",
        "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "pre-publication",
        "region": {"key": region, "name": pilot.name, "boundarySha256": boundary_manifest["boundary"]["sha256"]},
        "periods": request["periods"],
        "source": request["source"],
        "batchExport": {
            "taskDescription": request_task.get("description"),
            "taskId": request_task.get("id"),
            "rawCsv": csv_path.as_posix(),
            "rawCsvSha256": _sha256_file(csv_path),
        },
        "indicators": [
            {
                "indicatorId": indicator_id,
                "methodVersion": config["methodVersion"],
                "threshold": config["threshold"],
                "analysis": {
                    "crs": row["analysisCrs"],
                    "pixelSizeMetres": int(config["scaleMetres"]),
                    "minClearObservations": MIN_CLEAR_OBSERVATIONS,
                },
                "areaSqKm": {
                    "baseline": baseline_area / 1_000_000,
                    "comparison": comparison_area / 1_000_000,
                    "gain": gain_area / 1_000_000,
                    "loss": loss_area / 1_000_000,
                    "net": net_area / 1_000_000,
                    "percentChange": percent_change,
                },
                "commonValid": {
                    "boundaryAreaSqKm": boundary_area / 1_000_000,
                    "areaSqKm": common_valid_area / 1_000_000,
                    "fraction": common_valid_area / boundary_area if boundary_area else None,
                },
                "medianIndex": {
                    "baseline": _required_csv_float(row, "baselineMedianIndex"),
                    "comparison": _required_csv_float(row, "comparisonMedianIndex"),
                },
                "quality": {
                    "level": "unknown",
                    "warnings": [
                        "Pre-publication result: independent validation and threshold sensitivity are not complete.",
                        "Imported from a full-resolution Earth Engine batch export after the interactive reduction timed out.",
                        "This is a prototype analysis boundary, not an authoritative legal or cadastral boundary.",
                    ],
                },
            }
        ],
        "disclaimer": "This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.",
    }


def process_region(project: str, region: str, indicator_ids: tuple[str, ...]) -> dict[str, Any]:
    ee = _initialize(project)
    boundary_geometry, boundary_manifest = _load_region_geometry(region)
    analysis_crs = REGIONS[region]["analysisCrs"]
    geometry = ee.Geometry(boundary_geometry, "EPSG:4326", False)
    pilot = PILOTS[region]
    baseline_start, baseline_end = pilot.periods[0]
    comparison_start, comparison_end = pilot.periods[1]
    baseline_collection = _period_collection(ee, geometry, baseline_start, baseline_end)
    comparison_collection = _period_collection(ee, geometry, comparison_start, comparison_end)
    baseline_sources = _source_metadata(ee, baseline_collection)
    comparison_sources = _source_metadata(ee, comparison_collection)
    return {
        "manifestVersion": "1",
        "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "status": "pre-publication",
        "region": {"key": region, "name": pilot.name, "boundarySha256": boundary_manifest["boundary"]["sha256"]},
        "periods": {
            "baseline": {"start": baseline_start, "end": baseline_end, "endInclusive": True},
            "comparison": {"start": comparison_start, "end": comparison_end, "endInclusive": True},
        },
        "source": {
            "provider": "Google Earth Engine",
            "collection": COLLECTION,
            "sclAllowedValues": list(ALLOWED_SCL_VALUES),
            "baselineImages": baseline_sources,
            "comparisonImages": comparison_sources,
        },
        "indicators": [
            _indicator_summary(ee, indicator_id, geometry, baseline_collection, comparison_collection, analysis_crs)
            for indicator_id in indicator_ids
        ],
        "disclaimer": "This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=["all", *REGIONS], default="all")
    parser.add_argument("--indicator", choices=["all", *INDICATORS], default="all")
    parser.add_argument(
        "--mode",
        choices=("interactive", "batch-export", "validation-sample-export"),
        default="interactive",
    )
    parser.add_argument("--drive-folder", help="Google Drive folder name for a batch CSV export")
    parser.add_argument(
        "--start-batch-export",
        action="store_true",
        help="Create external Google Drive state. Without this flag batch-export records only a local dry run.",
    )
    parser.add_argument("--import-export-csv", type=Path, help="Completed Earth Engine batch CSV to validate and import")
    parser.add_argument("--batch-request", type=Path, help="Local batch-request JSON associated with --import-export-csv")
    parser.add_argument(
        "--import-vegetation-sensitivity-csv",
        type=Path,
        help="Completed three-row vegetation sensitivity CSV to validate and attach to the local vegetation report",
    )
    parser.add_argument(
        "--vegetation-sensitivity",
        action="store_true",
        help="Export the documented NDVI 0.20, 0.30, and 0.40 sensitivity rows in one guarded batch task.",
    )
    parser.add_argument("--project", default=os.getenv("EARTH_ENGINE_PROJECT"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/earth-engine-p0"))
    args = parser.parse_args()

    if args.vegetation_sensitivity and (args.mode != "batch-export" or args.indicator != "vegetation"):
        parser.error("--vegetation-sensitivity requires --mode batch-export --indicator vegetation")
    if args.import_export_csv and args.import_vegetation_sensitivity_csv:
        parser.error("Use only one batch CSV import mode at a time")

    if args.import_vegetation_sensitivity_csv:
        if args.region != "nagpur" or args.indicator != "vegetation":
            parser.error("--import-vegetation-sensitivity-csv requires --region nagpur --indicator vegetation")
        request_path = args.batch_request or args.output_dir / "sparc_nagpur_vegetation_p0_sensitivity_v1.batch-request.json"
        sensitivity = import_vegetation_sensitivity(args.import_vegetation_sensitivity_csv, request_path)
        output = args.output_dir / "nagpur-vegetation.json"
        report = _read_json(output)
        if report.get("region", {}).get("boundarySha256") != sensitivity["region"]["boundarySha256"]:
            parser.error("Local vegetation report does not match the approved sensitivity boundary")
        indicators = report.get("indicators")
        if not isinstance(indicators, list) or len(indicators) != 1 or indicators[0].get("indicatorId") != "vegetation":
            parser.error("Local vegetation report does not have exactly one vegetation indicator")
        indicators[0]["thresholdSensitivity"] = sensitivity
        indicators[0]["quality"]["warnings"] = [
            "Pre-publication result: independent validation is not complete.",
            "Threshold sensitivity completed with fixed documented NDVI thresholds 0.20, 0.30, and 0.40.",
            "Imported from a full-resolution Earth Engine batch export after the interactive reduction timed out.",
            "This is a prototype analysis boundary, not an authoritative legal or cadastral boundary.",
        ]
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"nagpur: imported vegetation sensitivity -> {output}")
        return 0

    if args.import_export_csv:
        if args.region == "all" or args.indicator == "all":
            parser.error("--import-export-csv requires one --region and one --indicator")
        request_path = args.batch_request or args.output_dir / f"sparc_{args.region}_{args.indicator}_p0_v1.batch-request.json"
        report = import_batch_export(args.region, args.indicator, args.import_export_csv, request_path)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        output = args.output_dir / f"{args.region}-{args.indicator}.json"
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{args.region}: imported batch export -> {output}")
        return 0
    project = _require_project(args.project)
    if args.mode == "validation-sample-export":
        if args.region != "nagpur" or args.indicator != "vegetation":
            parser.error("--mode validation-sample-export requires --region nagpur --indicator vegetation")
        if not args.drive_folder:
            parser.error("--drive-folder is required with --mode validation-sample-export")
        request = create_vegetation_validation_sample_export(
            project,
            args.drive_folder,
            args.output_dir,
            start=args.start_batch_export,
        )
        action = "started" if args.start_batch_export else "prepared"
        print(f"nagpur: {action} validation sample export {request['task']['description']}")
        return 0
    selected = REGIONS if args.region == "all" else {args.region: REGIONS[args.region]}
    indicator_ids = tuple(INDICATORS) if args.indicator == "all" else (args.indicator,)
    for region in selected:
        if args.mode == "batch-export":
            if not args.drive_folder:
                parser.error("--drive-folder is required with --mode batch-export")
            request = create_batch_export(
                project,
                region,
                indicator_ids,
                args.drive_folder,
                args.output_dir,
                start=args.start_batch_export,
                vegetation_sensitivity_thresholds=(
                    VEGETATION_SENSITIVITY_THRESHOLDS if args.vegetation_sensitivity else None
                ),
            )
            action = "started" if args.start_batch_export else "prepared"
            print(f"{region}: {action} batch export {request['task']['description']}")
            continue
        args.output_dir.mkdir(parents=True, exist_ok=True)
        report = process_region(project, region, indicator_ids)
        suffix = "" if args.indicator == "all" else f"-{args.indicator}"
        output = args.output_dir / f"{region}{suffix}.json"
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{region}: processed {len(report['indicators'])} P0 indicators -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
