"""Validate an approved district boundary before it enters the GEE worker."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MAX_BOUNDARY_BYTES = 5 * 1024 * 1024
REQUIRED_PROVENANCE_TEXT = ("sourceName", "sourceUrl", "version", "license", "attribution")


class BoundaryGateError(ValueError):
    """Raised when a boundary is not a safe, approved processing input."""


def _read_json(path: Path, *, max_bytes: int | None = None) -> tuple[Any, bytes]:
    try:
        if not path.is_file():
            raise BoundaryGateError(f"Input file does not exist: {path.name}")
        if max_bytes is not None and path.stat().st_size > max_bytes:
            raise BoundaryGateError(f"Boundary exceeds the {max_bytes} byte input limit")
        raw = path.read_bytes()
    except OSError as exc:
        raise BoundaryGateError(f"Could not read input file: {path.name}") from exc
    try:
        return json.loads(raw.decode("utf-8")), raw
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryGateError(f"Input file is not valid UTF-8 JSON: {path.name}") from exc


def _validated_provenance(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BoundaryGateError("Boundary provenance must be a JSON object")

    provenance: dict[str, Any] = {}
    for field in REQUIRED_PROVENANCE_TEXT:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            raise BoundaryGateError(f"Boundary provenance requires non-empty {field}")
        provenance[field] = item.strip()

    source_url = urlparse(provenance["sourceUrl"])
    if source_url.scheme != "https" or not source_url.netloc:
        raise BoundaryGateError("Boundary provenance sourceUrl must be an https URL")
    if value.get("redistributionPermitted") is not True:
        raise BoundaryGateError("Boundary provenance must explicitly set redistributionPermitted to true")
    provenance["redistributionPermitted"] = True
    return provenance


def _position(value: Any) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) < 2:
        raise BoundaryGateError("Every geometry position needs longitude and latitude")
    longitude, latitude = value[0], value[1]
    if (
        isinstance(longitude, bool)
        or isinstance(latitude, bool)
        or not isinstance(longitude, (int, float))
        or not isinstance(latitude, (int, float))
        or not math.isfinite(longitude)
        or not math.isfinite(latitude)
        or not -180 <= longitude <= 180
        or not -90 <= latitude <= 90
    ):
        raise BoundaryGateError("Geometry coordinates must be finite WGS84 longitude/latitude values")
    return float(longitude), float(latitude)


def _validate_ring(value: Any, bounds: list[float]) -> None:
    if not isinstance(value, list) or len(value) < 4:
        raise BoundaryGateError("Polygon rings must contain at least four positions")
    first: tuple[float, float] | None = None
    last: tuple[float, float] | None = None
    for position in value:
        longitude, latitude = _position(position)
        if first is None:
            first = (longitude, latitude)
        last = (longitude, latitude)
        bounds[0] = min(bounds[0], longitude)
        bounds[1] = min(bounds[1], latitude)
        bounds[2] = max(bounds[2], longitude)
        bounds[3] = max(bounds[3], latitude)
    if first != last:
        raise BoundaryGateError("Polygon rings must be closed")


def _validate_polygon(value: Any, bounds: list[float]) -> None:
    if not isinstance(value, list) or not value:
        raise BoundaryGateError("Polygon coordinates must contain an exterior ring")
    for ring in value:
        _validate_ring(ring, bounds)


def _extract_geometry(value: Any) -> tuple[dict[str, Any], int]:
    if not isinstance(value, dict):
        raise BoundaryGateError("Boundary must be a GeoJSON object")
    kind = value.get("type")
    if kind == "Feature":
        geometry = value.get("geometry")
        feature_count = 1
    elif kind == "FeatureCollection":
        features = value.get("features")
        if not isinstance(features, list) or len(features) != 1 or not isinstance(features[0], dict):
            raise BoundaryGateError("Boundary FeatureCollection must contain exactly one district feature")
        geometry = features[0].get("geometry")
        feature_count = 1
    else:
        raise BoundaryGateError("Boundary must be a GeoJSON Feature or a single-feature FeatureCollection")

    if not isinstance(geometry, dict):
        raise BoundaryGateError("Boundary feature must contain a geometry")
    return geometry, feature_count


def validate_boundary_gate(boundary_path: Path, provenance_path: Path) -> dict[str, Any]:
    """Return a deterministic manifest or reject an unapproved boundary input."""
    boundary, boundary_bytes = _read_json(boundary_path, max_bytes=MAX_BOUNDARY_BYTES)
    provenance, _ = _read_json(provenance_path)
    checked_provenance = _validated_provenance(provenance)
    geometry, feature_count = _extract_geometry(boundary)

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    bounds = [math.inf, math.inf, -math.inf, -math.inf]
    if geometry_type == "Polygon":
        _validate_polygon(coordinates, bounds)
    elif geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise BoundaryGateError("MultiPolygon coordinates must contain at least one polygon")
        for polygon in coordinates:
            _validate_polygon(polygon, bounds)
    else:
        raise BoundaryGateError("Boundary geometry must be Polygon or MultiPolygon")

    return {
        "manifestVersion": "1",
        "boundary": {
            "fileName": boundary_path.name,
            "sha256": sha256(boundary_bytes).hexdigest(),
            "geometryType": geometry_type,
            "featureCount": feature_count,
            "crs": "EPSG:4326",
            "bbox": bounds,
        },
        "provenance": checked_provenance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundary", type=Path, required=True, help="Approved district GeoJSON")
    parser.add_argument("--provenance", type=Path, required=True, help="Boundary source/license JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/boundary-gate/boundary-gate.json"),
        help="Ignored local manifest output path",
    )
    args = parser.parse_args()

    try:
        manifest = validate_boundary_gate(args.boundary, args.provenance)
    except BoundaryGateError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Boundary gate passed: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
