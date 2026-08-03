"""Extract and validate SPARC's pinned geoBoundaries India ADM2 districts."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable
import unicodedata
from zipfile import ZipFile

from .validate_boundary_gate import BoundaryGateError, validate_boundary_gate


ADM2_RELEASE = {
    "boundaryId": "IND-ADM2-76128533",
    "commit": "9469f09",
    "archiveMember": "geoBoundaries-IND-ADM2.geojson",
    "metadataMember": "geoBoundaries-IND-ADM2-metaData.json",
    "projectionMember": "geoBoundaries-IND-ADM2.prj",
    "archiveUrl": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM2/geoBoundaries-IND-ADM2-all.zip",
    "apiUrl": "https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/",
}
ADM1_RELEASE = {
    "boundaryId": "IND-ADM1-1811400",
    "archiveMember": "geoBoundaries-IND-ADM1.geojson",
    "projectionMember": "geoBoundaries-IND-ADM1.prj",
    "archiveUrl": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM1/geoBoundaries-IND-ADM1-all.zip",
    "apiUrl": "https://www.geoboundaries.org/api/current/gbOpen/IND/ADM1/",
}
SELECTIONS = {
    "nagpur": {
        "displayName": "Nagpur district",
        "providerName": "Nagpur",
        "shapeId": "76128533B3026318797185",
        "state": "Maharashtra",
    },
    "bengaluru-urban": {
        "displayName": "Bengaluru Urban district",
        "providerName": "Bangalore",
        "shapeId": "76128533B76927648517269",
        "state": "Karnataka",
        "nameNote": "The provider uses the legacy label 'Bangalore'; it is selected separately from 'Bangalore Rural'.",
    },
}
WGS84_MARKERS = ('GEOGCS["WGS84"', 'DATUM["WGS_1984"', 'UNIT["degree"')
PROTOTYPE_DISCLAIMER = (
    "This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary."
)


def _normalise_name(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    ).casefold()


def _read_zip_json(archive_path: Path, member: str) -> dict[str, Any]:
    try:
        with ZipFile(archive_path) as archive:
            return json.loads(archive.read(member))
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise BoundaryGateError(f"Could not read {member} from {archive_path.name}") from exc


def _read_zip_text(archive_path: Path, member: str) -> str:
    try:
        with ZipFile(archive_path) as archive:
            return archive.read(member).decode("utf-8")
    except (OSError, KeyError, UnicodeDecodeError) as exc:
        raise BoundaryGateError(f"Could not read {member} from {archive_path.name}") from exc


def _sha256_file(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise BoundaryGateError(f"Could not hash source archive: {path.name}") from exc
    return digest.hexdigest()


def _polygons(geometry: dict[str, Any]) -> Iterable[list[list[list[float]]]]:
    coordinates = geometry["coordinates"]
    if geometry["type"] == "Polygon":
        yield coordinates
    elif geometry["type"] == "MultiPolygon":
        yield from coordinates
    else:
        raise BoundaryGateError("Expected Polygon or MultiPolygon geometry")


def _ring_centroid(ring: list[list[float]]) -> tuple[float, float, float] | None:
    twice_area = centroid_x = centroid_y = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        cross = x1 * y2 - x2 * y1
        twice_area += cross
        centroid_x += (x1 + x2) * cross
        centroid_y += (y1 + y2) * cross
    if twice_area == 0:
        return None
    return abs(twice_area) / 2, centroid_x / (3 * twice_area), centroid_y / (3 * twice_area)


def _representative_point(geometry: dict[str, Any]) -> tuple[float, float]:
    weighted = [
        centroid
        for polygon in _polygons(geometry)
        if (centroid := _ring_centroid(polygon[0])) is not None
    ]
    if not weighted:
        raise BoundaryGateError("Could not calculate a representative point for the district")
    total_area = sum(item[0] for item in weighted)
    return (
        sum(item[0] * item[1] for item in weighted) / total_area,
        sum(item[0] * item[2] for item in weighted) / total_area,
    )


def _point_in_ring(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def _contains_point(geometry: dict[str, Any], point: tuple[float, float]) -> bool:
    return any(
        _point_in_ring(point, polygon[0])
        and not any(_point_in_ring(point, interior_ring) for interior_ring in polygon[1:])
        for polygon in _polygons(geometry)
    )


def _bbox(geometry: dict[str, Any]) -> list[float]:
    points = [point for polygon in _polygons(geometry) for ring in polygon for point in ring]
    return [
        min(point[0] for point in points),
        min(point[1] for point in points),
        max(point[0] for point in points),
        max(point[1] for point in points),
    ]


def _single_feature(collection: dict[str, Any], selection: dict[str, str]) -> dict[str, Any]:
    matches = [
        feature
        for feature in collection.get("features", [])
        if feature.get("properties", {}).get("shapeID") == selection["shapeId"]
        and feature.get("properties", {}).get("shapeName") == selection["providerName"]
        and feature.get("properties", {}).get("shapeGroup") == "IND"
        and feature.get("properties", {}).get("shapeType") == "ADM2"
    ]
    if len(matches) != 1:
        raise BoundaryGateError(
            f"Expected exactly one {selection['providerName']} feature with shape ID {selection['shapeId']}; found {len(matches)}"
        )
    return matches[0]


def _validate_state(
    geometry: dict[str, Any], state_collection: dict[str, Any], expected_state: str
) -> dict[str, Any]:
    point = _representative_point(geometry)
    matches = [
        feature.get("properties", {}).get("shapeName", "")
        for feature in state_collection.get("features", [])
        if _contains_point(feature.get("geometry", {}), point)
    ]
    if len(matches) != 1 or _normalise_name(matches[0]) != _normalise_name(expected_state):
        raise BoundaryGateError(
            f"District representative point did not resolve uniquely to expected state {expected_state}: {matches}"
        )
    return {
        "expectedState": expected_state,
        "providerStateName": matches[0],
        "representativePoint": {"longitude": point[0], "latitude": point[1]},
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract(
    *,
    adm2_archive: Path,
    adm1_archive: Path,
    output_boundary_dir: Path,
    output_metadata_dir: Path,
) -> dict[str, Any]:
    """Write selected district features, provenance records and gate manifests."""
    adm2_metadata = _read_zip_json(adm2_archive, ADM2_RELEASE["metadataMember"])
    adm2_collection = _read_zip_json(adm2_archive, ADM2_RELEASE["archiveMember"])
    adm1_collection = _read_zip_json(adm1_archive, ADM1_RELEASE["archiveMember"])
    adm2_projection = _read_zip_text(adm2_archive, ADM2_RELEASE["projectionMember"])
    adm1_projection = _read_zip_text(adm1_archive, ADM1_RELEASE["projectionMember"])
    if not all(marker in adm2_projection for marker in WGS84_MARKERS) or not all(
        marker in adm1_projection for marker in WGS84_MARKERS
    ):
        raise BoundaryGateError("geoBoundaries source CRS is not the expected WGS84 geographic CRS")
    if adm2_metadata.get("boundaryID") != ADM2_RELEASE["boundaryId"]:
        raise BoundaryGateError("ADM2 archive metadata does not match the pinned geoBoundaries release")

    archive_hashes = {"adm2": _sha256_file(adm2_archive), "adm1": _sha256_file(adm1_archive)}
    result: dict[str, Any] = {
        "metadataVersion": "1",
        "disclaimer": PROTOTYPE_DISCLAIMER,
        "release": {
            "provider": "geoBoundaries gbOpen",
            "boundaryId": ADM2_RELEASE["boundaryId"],
            "boundaryYear": adm2_metadata.get("boundaryYear"),
            "boundaryType": adm2_metadata.get("boundaryType"),
            "buildDate": adm2_metadata.get("buildDate"),
            "commit": ADM2_RELEASE["commit"],
            "apiUrl": ADM2_RELEASE["apiUrl"],
            "archiveUrl": ADM2_RELEASE["archiveUrl"],
            "archiveSha256": archive_hashes["adm2"],
            "metadataFeatureCountDeclared": adm2_metadata.get("admUnitCount"),
            "geojsonFeatureCountActual": len(adm2_collection.get("features", [])),
            "featureCountWarning": "The release metadata declares 736 ADM2 units; the downloaded GeoJSON contains 735 features. The selected features below were individually verified.",
            "source": adm2_metadata.get("boundarySource"),
            "sourceLicense": adm2_metadata.get("boundaryLicense"),
            "sourceLicenseTermsUrl": "https://opendatacommons.org/licenses/odbl/1.0/",
            "geoBoundariesDerivativeLicenseNotice": "The included geoBoundaries citation file says geoBoundaries code and derivative works are CC BY 4.0; the India ADM2 metadata labels the boundary source itself ODbL 1.0. SPARC follows the source-specific ODbL record for boundary redistribution.",
        },
        "stateReference": {
            "provider": "geoBoundaries gbOpen",
            "boundaryId": ADM1_RELEASE["boundaryId"],
            "apiUrl": ADM1_RELEASE["apiUrl"],
            "archiveUrl": ADM1_RELEASE["archiveUrl"],
            "archiveSha256": archive_hashes["adm1"],
            "crs": "EPSG:4326",
        },
        "districts": {},
    }

    for key, selection in SELECTIONS.items():
        source_feature = _single_feature(adm2_collection, selection)
        state_validation = _validate_state(source_feature["geometry"], adm1_collection, selection["state"])
        feature = {
            "type": "Feature",
            "properties": {
                **source_feature["properties"],
                "sparcRegionId": f"gbopen:district:{key}",
                "sparcDisplayName": selection["displayName"],
                "sparcPrototypeDisclaimer": PROTOTYPE_DISCLAIMER,
            },
            "geometry": source_feature["geometry"],
        }
        if selection.get("nameNote"):
            feature["properties"]["sparcNameNote"] = selection["nameNote"]

        boundary_path = output_boundary_dir / f"{key}.geojson"
        provenance_path = output_metadata_dir / f"{key}.provenance.json"
        gate_path = output_metadata_dir / f"{key}.boundary-gate.json"
        provenance = {
            "sourceName": "geoBoundaries gbOpen India ADM2; source: Pathways Data Pvt. Ltd., lgdirectory.gov.in",
            "sourceUrl": ADM2_RELEASE["archiveUrl"],
            "version": f"{ADM2_RELEASE['boundaryId']}; build {adm2_metadata.get('buildDate')}; commit {ADM2_RELEASE['commit']}",
            "license": "Open Data Commons Open Database License 1.0 (source-specific boundary metadata)",
            "attribution": "Contains modified geoBoundaries data (Runfola et al., 2020, https://doi.org/10.1371/journal.pone.0231866), sourced from Pathways Data Pvt. Ltd. and lgdirectory.gov.in; boundary source terms: ODbL 1.0.",
            "redistributionPermitted": True,
        }
        _write_json(boundary_path, feature)
        _write_json(provenance_path, provenance)
        gate_manifest = validate_boundary_gate(boundary_path, provenance_path)
        _write_json(gate_path, gate_manifest)
        result["districts"][key] = {
            "displayName": selection["displayName"],
            "providerProperties": source_feature["properties"],
            "validatedGeoJson": boundary_path.as_posix(),
            "provenance": provenance_path.as_posix(),
            "boundaryGate": gate_path.as_posix(),
            "geometryType": source_feature["geometry"]["type"],
            "bbox": _bbox(source_feature["geometry"]),
            "crs": "EPSG:4326",
            "stateValidation": state_validation,
            "sha256": gate_manifest["boundary"]["sha256"],
        }

    _write_json(output_metadata_dir / "release-metadata.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--adm2-archive",
        type=Path,
        default=Path("data/raw/boundaries/geoBoundaries-IND-ADM2-76128533/geoBoundaries-IND-ADM2-all.zip"),
    )
    parser.add_argument(
        "--adm1-archive",
        type=Path,
        default=Path("data/raw/boundaries/geoBoundaries-IND-ADM1-1811400/geoBoundaries-IND-ADM1-all.zip"),
    )
    parser.add_argument(
        "--output-boundary-dir",
        type=Path,
        default=Path("data/validated/boundaries/geoBoundaries-IND-ADM2-76128533"),
    )
    parser.add_argument(
        "--output-metadata-dir",
        type=Path,
        default=Path("data/metadata/boundaries/geoBoundaries-IND-ADM2-76128533"),
    )
    args = parser.parse_args()
    try:
        result = extract(
            adm2_archive=args.adm2_archive,
            adm1_archive=args.adm1_archive,
            output_boundary_dir=args.output_boundary_dir,
            output_metadata_dir=args.output_metadata_dir,
        )
    except BoundaryGateError as exc:
        parser.error(str(exc))
    print(f"Validated {len(result['districts'])} geoBoundaries district features")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
