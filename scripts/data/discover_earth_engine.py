"""Metadata-only Sentinel-2 discovery through Google Earth Engine."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, timedelta
import json
import os
from pathlib import Path
import re
from typing import Any

from .discover_catalog import PILOTS, Pilot


COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
REQUIRED_BANDS = ("B2", "B3", "B4", "B8", "B11", "B12", "SCL")
MAX_IMAGES = 500
PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")


def _require_project(project: str | None) -> str:
    value = (project or "").strip()
    if not PROJECT_ID_PATTERN.fullmatch(value):
        raise ValueError("Set EARTH_ENGINE_PROJECT or pass a valid --project value")
    return value


def _initialize(project: str):
    try:
        import ee

        ee.Initialize(project=project)
        return ee
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine initialization failed. Run `earthengine authenticate` and verify project access."
        ) from exc


def _exclusive_end(value: str) -> str:
    return (date.fromisoformat(value) + timedelta(days=1)).isoformat()


def _sanitize_feature(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties") or {}
    band_names = properties.get("bandNames") or []
    present = [band for band in REQUIRED_BANDS if band in band_names]
    return {
        "id": properties.get("id"),
        "datetime": properties.get("datetime"),
        "cloudCoverPercent": properties.get("cloudCoverPercent"),
        "mgrsTile": properties.get("mgrsTile"),
        "spacecraft": properties.get("spacecraft"),
        "processingBaseline": properties.get("processingBaseline"),
        "requiredBandsPresent": present,
    }


def discover(project: str, pilot: Pilot, start: str, end: str) -> dict[str, Any]:
    ee = _initialize(project)
    geometry = ee.Geometry.Rectangle(list(pilot.bbox), "EPSG:4326", False)
    collection = (
        ee.ImageCollection(COLLECTION)
        .filterBounds(geometry)
        .filterDate(start, _exclusive_end(end))
        .sort("system:time_start")
    )
    count = collection.size().getInfo()
    if not isinstance(count, int) or count < 0:
        raise RuntimeError("Earth Engine returned an invalid image count")
    if count > MAX_IMAGES:
        raise RuntimeError(f"Earth Engine query returned {count} images; limit is {MAX_IMAGES}")

    images = collection.toList(MAX_IMAGES)

    def to_feature(image):
        image = ee.Image(image)
        return ee.Feature(
            None,
            {
                "id": image.id(),
                "datetime": ee.Date(image.get("system:time_start")).format("YYYY-MM-dd'T'HH:mm:ss'Z'"),
                "cloudCoverPercent": image.get("CLOUDY_PIXEL_PERCENTAGE"),
                "mgrsTile": image.get("MGRS_TILE"),
                "spacecraft": image.get("SPACECRAFT_NAME"),
                "processingBaseline": image.get("PROCESSING_BASELINE"),
                "bandNames": image.bandNames(),
            },
        )

    feature_collection = ee.FeatureCollection(images.map(to_feature))
    feature_info = feature_collection.getInfo()
    features = feature_info.get("features") if isinstance(feature_info, dict) else None
    if not isinstance(features, list) or len(features) != count:
        raise RuntimeError("Earth Engine returned incomplete metadata")

    items = sorted((_sanitize_feature(feature) for feature in features), key=lambda item: item["datetime"] or "")
    cloud_values = [item["cloudCoverPercent"] for item in items if isinstance(item["cloudCoverPercent"], (int, float))]
    return {
        "manifestVersion": "1",
        "createdAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "metadataOnly": True,
        "coverageStatus": "search-envelope-only-pending-approved-district-geometry",
        "pilot": {
            "key": pilot.key,
            "name": pilot.name,
            "searchBbox": list(pilot.bbox),
            "bboxSource": pilot.bbox_source,
        },
        "period": {"start": start, "end": end, "endInclusive": True},
        "catalog": {"provider": "Google Earth Engine", "collection": COLLECTION},
        "summary": {
            "imageCount": len(items),
            "imagesWithAllRequiredBands": sum(
                len(item["requiredBandsPresent"]) == len(REQUIRED_BANDS) for item in items
            ),
            "minimumSceneCloudCoverPercent": min(cloud_values) if cloud_values else None,
            "maximumSceneCloudCoverPercent": max(cloud_values) if cloud_values else None,
            "distinctMgrsTiles": sorted({item["mgrsTile"] for item in items if item["mgrsTile"]}),
        },
        "items": items,
        "licenseAndAttribution": [
            "Copernicus Sentinel data; derived outputs must state: Contains modified Copernicus Sentinel data [year]."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=["all", *PILOTS], default="all")
    parser.add_argument("--project", default=os.getenv("EARTH_ENGINE_PROJECT"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/earth-engine-discovery"))
    args = parser.parse_args()

    project = _require_project(args.project)
    selected = PILOTS.values() if args.pilot == "all" else (PILOTS[args.pilot],)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for pilot in selected:
        for start, end in pilot.periods:
            report = discover(project, pilot, start, end)
            target = args.output_dir / f"{pilot.key}-{start}-{end}.json"
            target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{target}: {report['summary']['imageCount']} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
