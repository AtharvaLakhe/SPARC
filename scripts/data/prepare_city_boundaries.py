"""Select and gate the pinned geoBoundaries sources for the quick-target cities.

The source downloads live under ``data/raw`` (ignored working data).  This
script never picks a nearest feature or creates an envelope: every selection
is pinned by a geoBoundaries shape ID or an exact, complete name set.  A
missing or ambiguous selection stops the run and prints the candidate names.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any

from .validate_boundary_gate import BoundaryGateError, validate_boundary_gate


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "data" / "catalog" / "city-boundary-sources.json"
VALIDATED_ROOT = ROOT / "data" / "validated" / "boundaries" / "global"
METADATA_ROOT = ROOT / "data" / "metadata" / "boundaries" / "global"
PROTOTYPE_DISCLAIMER = (
    "This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary."
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryGateError(f"Could not read JSON source {path}") from exc
    if not isinstance(value, dict):
        raise BoundaryGateError(f"Expected a JSON object in {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _positions(geometry: dict[str, Any]) -> list[list[float]]:
    kind = geometry.get("type")
    if kind == "Polygon":
        return [position for ring in geometry["coordinates"] for position in ring]
    if kind == "MultiPolygon":
        return [position for polygon in geometry["coordinates"] for ring in polygon for position in ring]
    raise BoundaryGateError(f"Unsupported source geometry type: {kind!r}")


def _geometry_parts(geometry: dict[str, Any]) -> list[list[list[list[float]]]]:
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"]]
    if kind == "MultiPolygon":
        return geometry["coordinates"]
    raise BoundaryGateError(f"Unsupported source geometry type: {kind!r}")


def _bbox(geometry: dict[str, Any]) -> list[float]:
    points = _positions(geometry)
    return [
        min(float(point[0]) for point in points),
        min(float(point[1]) for point in points),
        max(float(point[0]) for point in points),
        max(float(point[1]) for point in points),
    ]


def _select_features(slug: str, spec: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    features = source.get("features")
    if not isinstance(features, list):
        raise BoundaryGateError(f"{slug}: source is not a GeoJSON FeatureCollection")

    expected_ids = list(spec.get("shapeIds", []))
    expected_names = list(spec.get("shapeNames", []))
    if not expected_ids and not expected_names:
        raise BoundaryGateError(f"{slug}: boundary selector has no shape IDs or names")

    if expected_ids:
        selected = [
            feature
            for feature in features
            if isinstance(feature, dict)
            and feature.get("properties", {}).get("shapeID") in expected_ids
        ]
        missing = sorted(set(expected_ids) - {feature.get("properties", {}).get("shapeID") for feature in selected})
        duplicate_ids = sorted(
            shape_id
            for shape_id in expected_ids
            if sum(feature.get("properties", {}).get("shapeID") == shape_id for feature in features) != 1
        )
        if missing or duplicate_ids:
            raise BoundaryGateError(
                f"{slug}: pinned shape IDs were not unique; missing={missing}, duplicate-or-nonunique={duplicate_ids}"
            )
    else:
        matches_by_name: dict[str, list[dict[str, Any]]] = {}
        for name in expected_names:
            matches_by_name[name] = [
                feature
                for feature in features
                if isinstance(feature, dict) and feature.get("properties", {}).get("shapeName") == name
            ]
        ambiguous = {name: len(rows) for name, rows in matches_by_name.items() if len(rows) != 1}
        if ambiguous:
            candidates = sorted(
                {
                    str(feature.get("properties", {}).get("shapeName", ""))
                    for feature in features
                    if isinstance(feature, dict)
                }
            )
            raise BoundaryGateError(f"{slug}: exact name selection failed {ambiguous}; candidate names={candidates}")
        selected = [matches_by_name[name][0] for name in expected_names]

    for feature in selected:
        properties = feature.get("properties", {})
        if properties.get("shapeGroup") != spec["countryCode"]:
            raise BoundaryGateError(
                f"{slug}: selected feature {properties.get('shapeName')!r} is not in {spec['countryCode']}"
            )
        if properties.get("shapeType") != spec["level"]:
            raise BoundaryGateError(
                f"{slug}: selected feature {properties.get('shapeName')!r} is not {spec['level']}"
            )
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            raise BoundaryGateError(f"{slug}: selected feature has no geometry")
        for position in _positions(geometry):
            if (
                not isinstance(position, list)
                or len(position) < 2
                or isinstance(position[0], bool)
                or isinstance(position[1], bool)
                or not isinstance(position[0], (int, float))
                or not isinstance(position[1], (int, float))
                or not math.isfinite(float(position[0]))
                or not math.isfinite(float(position[1]))
                or not -180 <= float(position[0]) <= 180
                or not -90 <= float(position[1]) <= 90
            ):
                raise BoundaryGateError(f"{slug}: selected feature has invalid WGS84 coordinates")
    selected_ids = [feature.get("properties", {}).get("shapeID") for feature in selected]
    if expected_ids and set(selected_ids) != set(expected_ids):
        raise BoundaryGateError(f"{slug}: selected shape IDs do not match the pinned set")
    selected_names = [feature.get("properties", {}).get("shapeName") for feature in selected]
    if set(selected_names) != set(expected_names):
        raise BoundaryGateError(
            f"{slug}: selected feature names {selected_names!r} do not match the expected names {expected_names!r}"
        )
    return selected


def prepare_city(slug: str, spec: dict[str, Any]) -> dict[str, Any]:
    source_path = ROOT / spec["source"]
    metadata_path = ROOT / spec["metadata"]
    source = _read_json(source_path)
    source_metadata = _read_json(metadata_path)
    if source_metadata.get("boundaryID") != spec["boundaryId"]:
        raise BoundaryGateError(
            f"{slug}: source metadata boundaryID {source_metadata.get('boundaryID')!r} does not match {spec['boundaryId']}"
        )
    selected = _select_features(slug, spec, source)
    parts = []
    for feature in selected:
        parts.extend(_geometry_parts(feature["geometry"]))
    geometry_type = "MultiPolygon" if len(parts) != 1 or selected[0]["geometry"].get("type") == "MultiPolygon" else "Polygon"
    geometry = {"type": geometry_type, "coordinates": parts if geometry_type == "MultiPolygon" else parts[0]}
    boundary = {
        "type": "Feature",
        "properties": {
            "sparcCitySlug": slug,
            "sparcScope": spec["scope"],
            "sparcBoundaryId": spec["boundaryId"],
            "sparcBoundaryLevel": spec["level"],
            "sparcSelectedShapeIds": [feature["properties"]["shapeID"] for feature in selected],
            "sparcSelectedShapeNames": [feature["properties"]["shapeName"] for feature in selected],
            "sparcPrototypeDisclaimer": PROTOTYPE_DISCLAIMER,
        },
        "geometry": geometry,
    }

    output_boundary = VALIDATED_ROOT / f"{slug}.geojson"
    output_provenance = METADATA_ROOT / f"{slug}.provenance.json"
    output_gate = METADATA_ROOT / f"{slug}.boundary-gate.json"
    provenance = {
        "sourceName": f"geoBoundaries gbOpen {spec['countryCode']} {spec['level']}; source: {source_metadata.get('boundarySource', 'unspecified')}",
        "sourceUrl": source_metadata.get("simplifiedGeometryGeoJSON"),
        "version": (
            f"{source_metadata.get('boundaryID')}; year {source_metadata.get('boundaryYearRepresented')}; "
            f"build {source_metadata.get('buildDate')}"
        ),
        "license": source_metadata.get("boundaryLicense"),
        "attribution": (
            "Contains modified geoBoundaries data (Runfola et al., 2020, "
            "https://doi.org/10.1371/journal.pone.0231866); upstream source: "
            f"{source_metadata.get('boundarySource')}; source terms: {source_metadata.get('boundaryLicense')}."
        ),
        "redistributionPermitted": True,
        "releaseMetadataUrl": f"https://www.geoboundaries.org/api/current/gbOpen/{spec['countryCode']}/{spec['level']}/",
        "rawSourceFile": spec["source"],
        "rawSourceSha256": _sha256(source_path),
        "selection": {
            "scope": spec["scope"],
            "shapeIds": [feature["properties"]["shapeID"] for feature in selected],
            "shapeNames": [feature["properties"]["shapeName"] for feature in selected],
        },
        "crs": "EPSG:4326",
        "disclaimer": PROTOTYPE_DISCLAIMER,
    }
    _write_json(output_boundary, boundary)
    _write_json(output_provenance, provenance)
    gate = validate_boundary_gate(output_boundary, output_provenance)
    _write_json(output_gate, gate)
    return {
        "slug": slug,
        "scope": spec["scope"],
        "boundaryId": spec["boundaryId"],
        "level": spec["level"],
        "sourceMetadata": spec["metadata"],
        "sourceFile": spec["source"],
        "sourceSha256": provenance["rawSourceSha256"],
        "selectedShapeIds": provenance["selection"]["shapeIds"],
        "selectedShapeNames": provenance["selection"]["shapeNames"],
        "validatedGeoJson": output_boundary.relative_to(ROOT).as_posix(),
        "provenance": output_provenance.relative_to(ROOT).as_posix(),
        "boundaryGate": output_gate.relative_to(ROOT).as_posix(),
        "boundarySha256": gate["boundary"]["sha256"],
        "geometryType": gate["boundary"]["geometryType"],
        "bbox": gate["boundary"]["bbox"],
        "crs": "EPSG:4326",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--city", choices=("all",), default="all")
    args = parser.parse_args()
    config = _read_json(args.config)
    results: dict[str, Any] = {}
    for slug, spec in config.get("cities", {}).items():
        try:
            results[slug] = prepare_city(slug, spec)
        except BoundaryGateError as exc:
            parser.error(str(exc))
    _write_json(METADATA_ROOT / "release-metadata.json", {
        "metadataVersion": "1",
        "catalogVersion": config.get("catalogVersion"),
        "provider": "geoBoundaries gbOpen",
        "disclaimer": PROTOTYPE_DISCLAIMER,
        "cities": results,
    })
    print(f"Prepared and gated {len(results)} city boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
