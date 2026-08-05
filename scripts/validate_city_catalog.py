"""Validate the versioned quick-target city catalog before a release.

The catalog deliberately distinguishes a validated district/processing pack
from a city envelope used only to start report generation. This command refuses
to let a fallback envelope be labelled as an ADM boundary or a processing
pack, and binds the two published packs to their checked-in manifests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


EXPECTED_SLUGS = {
    "nagpur", "bengaluru", "mumbai", "delhi", "chennai", "bhopal",
    "new-york", "washington-dc", "tokyo", "london", "cairo", "sydney", "rio-de-janeiro", "reykjavik",
}
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
ANALYTICS_STATES = {"FULLY_SUPPORTED", "REPORT_GENERATION_ONLY"}
ROUTING_STATES = {"FULLY_SUPPORTED", "REPORT_GENERATION_ONLY", "UNSUPPORTED_JURISDICTION"}


class CityCatalogError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CityCatalogError(message)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fallback_geometry(bbox: list[float]) -> dict[str, Any]:
    west, south, east, north = bbox
    return {
        "type": "Polygon",
        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
    }


def _validate_city(
    city: dict[str, Any],
    root: Path,
    manifest: dict[str, str],
    release: dict[str, Any],
    authority_ids: set[str],
) -> None:
    for field in ("slug", "regionId", "name", "countryCode", "country", "story", "analyticsCoverage", "routingCoverage", "boundary", "processingPack", "jurisdiction"):
        _require(field in city, f"{city.get('slug', '<unknown>')}: missing {field}")
    slug = city["slug"]
    _require(isinstance(slug, str) and slug in EXPECTED_SLUGS, f"unexpected city slug: {slug!r}")
    _require(isinstance(city["countryCode"], str) and COUNTRY_RE.fullmatch(city["countryCode"]), f"{slug}: invalid countryCode")
    centroid = city["centroid"]
    bbox = city["bbox"]
    _require(isinstance(centroid, list) and len(centroid) == 2, f"{slug}: centroid must be [longitude, latitude]")
    _require(isinstance(bbox, list) and len(bbox) == 4, f"{slug}: bbox must be [west, south, east, north]")
    _require(all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in centroid + bbox), f"{slug}: coordinates must be finite numbers")
    west, south, east, north = bbox
    _require(-180 <= west < east <= 180 and -90 <= south < north <= 90, f"{slug}: invalid bbox")
    _require(west <= centroid[0] <= east and south <= centroid[1] <= north, f"{slug}: centroid is outside bbox")

    boundary = city["boundary"]
    _require(
        boundary.get("kind") in {"validated-adm2", "validated-adm1", "validated-city", "catalog-envelope"},
        f"{slug}: invalid boundary kind",
    )
    _require(boundary.get("status") in {"VALIDATED", "CATALOG_ONLY"}, f"{slug}: invalid boundary status")
    for field in ("sourceName", "license", "attribution", "definition"):
        _require(isinstance(boundary.get(field), str) and boundary[field].strip(), f"{slug}: boundary {field} required")
    parsed = urlparse(boundary.get("sourceUrl", ""))
    _require(parsed.scheme == "https" and parsed.netloc, f"{slug}: boundary sourceUrl must be HTTPS")
    _require(isinstance(boundary.get("sha256"), str) and SHA256_RE.fullmatch(boundary["sha256"]), f"{slug}: boundary checksum invalid")
    _require(boundary.get("crs") == "EPSG:4326", f"{slug}: boundary CRS must be EPSG:4326")

    pack = city["processingPack"]
    _require(pack.get("status") in {"VALIDATED", "NOT_AVAILABLE"}, f"{slug}: invalid processing pack status")
    if pack["status"] == "VALIDATED":
        _require(
            boundary["status"] == "VALIDATED"
            and boundary["kind"] in {"validated-adm2", "validated-adm1", "validated-city"},
            f"{slug}: a validated pack requires a validated boundary",
        )
        _require(city["analyticsCoverage"] == "FULLY_SUPPORTED", f"{slug}: validated pack must be fully supported")
        _require(isinstance(pack.get("packId"), str) and pack["packId"], f"{slug}: packId required")
        _require(isinstance(pack.get("files"), dict) and pack["files"], f"{slug}: pack files required")
        _require(isinstance(pack.get("checksums"), dict) and set(pack["files"]) == set(pack["checksums"]), f"{slug}: pack files/checksums must match")
        for key, filename in pack["files"].items():
            path = root / "contracts" / "examples" / "precomputed" / filename
            _require(path.is_file(), f"{slug}: missing pack file {filename}")
            expected = pack["checksums"][key]
            _require(isinstance(expected, str) and SHA256_RE.fullmatch(expected), f"{slug}: invalid checksum for {key}")
            _require(expected.removeprefix("sha256:") == manifest.get(filename), f"{slug}: manifest checksum mismatch for {filename}")
        _require(isinstance(boundary.get("geometryAsset"), str) and boundary["geometryAsset"], f"{slug}: validated geometryAsset required")
        asset = root / boundary["geometryAsset"]
        _require(asset.is_file(), f"{slug}: validated geometry asset is missing")
        _require(_sha256(asset) == boundary["sha256"].removeprefix("sha256:"), f"{slug}: geometry checksum mismatch")
        _require(pack.get("boundarySha256") == boundary["sha256"], f"{slug}: pack/boundary checksum mismatch")
        release_key = {"bengaluru": "bengaluru-urban", "mumbai": "mumbai-city"}.get(slug, slug)
        release_entry = release.get("districts", {}).get(release_key)
        _require(isinstance(release_entry, dict) and release_entry.get("sha256") == boundary["sha256"].removeprefix("sha256:"), f"{slug}: release metadata checksum mismatch")
    else:
        _require(city["analyticsCoverage"] == "REPORT_GENERATION_ONLY", f"{slug}: report-only boundary must be report-generation-only")
        _require(
            pack.get("packId") is None
            and pack.get("manifest") is None
            and pack.get("files") == {}
            and pack.get("checksums") == {},
            f"{slug}: report-only boundary must not claim a processing pack",
        )
        if boundary["status"] == "CATALOG_ONLY":
            _require(boundary["kind"] == "catalog-envelope", f"{slug}: catalog-only boundary must use a catalog envelope")
            _require("not an ADM boundary" in boundary.get("definition", ""), f"{slug}: fallback boundary definition must say it is not an ADM boundary")
            expected = "sha256:" + hashlib.sha256(json.dumps(_fallback_geometry(bbox), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            _require(boundary["sha256"] == expected, f"{slug}: fallback envelope checksum mismatch")
            _require(boundary.get("geometryAsset") is None, f"{slug}: fallback must not claim a geometry asset")
            _require(pack.get("boundarySha256") is None, f"{slug}: catalog-only boundary must not claim a boundary checksum")
        else:
            _require(
                boundary["kind"] in {"validated-adm2", "validated-adm1", "validated-city"},
                f"{slug}: validated report-only boundary has an invalid kind",
            )
            _require(isinstance(boundary.get("geometryAsset"), str) and boundary["geometryAsset"], f"{slug}: validated geometryAsset required")
            asset = root / boundary["geometryAsset"]
            _require(asset.is_file(), f"{slug}: validated geometry asset is missing")
            _require(_sha256(asset) == boundary["sha256"].removeprefix("sha256:"), f"{slug}: validated geometry checksum mismatch")
            _require(pack.get("boundarySha256") == boundary["sha256"], f"{slug}: report-only boundary checksum mismatch")
            gate_path = root / boundary.get("boundaryGate", "")
            _require(gate_path.is_file(), f"{slug}: validated boundary gate is missing")
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
            _require(gate.get("boundary", {}).get("sha256") == boundary["sha256"].removeprefix("sha256:"), f"{slug}: boundary gate checksum mismatch")
            global_release_path = root / "data" / "metadata" / "boundaries" / "global" / "release-metadata.json"
            _require(global_release_path.is_file(), f"{slug}: global boundary release metadata is missing")
            global_release = json.loads(global_release_path.read_text(encoding="utf-8"))
            release_entry = global_release.get("cities", {}).get(slug)
            _require(isinstance(release_entry, dict) and release_entry.get("boundarySha256") == boundary["sha256"].removeprefix("sha256:"), f"{slug}: global release metadata checksum mismatch")

    _require(city["analyticsCoverage"] in ANALYTICS_STATES, f"{slug}: invalid analytics coverage state")
    _require(city["routingCoverage"] in ROUTING_STATES, f"{slug}: invalid routing coverage state")
    _require(isinstance(city["jurisdiction"].get("pack"), str) and city["jurisdiction"]["pack"], f"{slug}: jurisdiction pack required")
    _require(isinstance(city["jurisdiction"].get("authorityIds"), list), f"{slug}: authorityIds must be a list")
    _require(
        all(isinstance(item, str) and item in authority_ids for item in city["jurisdiction"]["authorityIds"]),
        f"{slug}: jurisdiction references an unknown authority id",
    )
    if city["routingCoverage"] == "UNSUPPORTED_JURISDICTION":
        _require(city["jurisdiction"]["pack"] == "generic" and not city["jurisdiction"]["authorityIds"], f"{slug}: unsupported jurisdictions must use the generic empty authority pack")


def _validate_boundary_registry(path: Path, root: Path) -> None:
    registry = json.loads(path.read_text(encoding="utf-8"))
    _require(registry.get("registryVersion") == "2026-08-05.3", "city boundary registry version is not frozen")
    cities = registry.get("cities")
    _require(isinstance(cities, dict), "city boundary registry cities must be an object")
    expected = EXPECTED_SLUGS - {"nagpur", "bengaluru"}
    _require(set(cities) == expected, "city boundary registry does not contain exactly the twelve requested expansion cities")
    release_path = root / "data" / "metadata" / "boundaries" / "global" / "release-metadata.json"
    _require(release_path.is_file(), "global boundary release metadata is missing")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    for slug, record in cities.items():
        _require(record.get("status") == "VALIDATED", f"{slug}: global boundary registry record is not validated")
        _require(record.get("kind") in {"validated-adm1", "validated-adm2", "validated-city"}, f"{slug}: invalid global boundary kind")
        _require(isinstance(record.get("geometryAsset"), str), f"{slug}: global geometryAsset is required")
        asset = root / record["geometryAsset"]
        _require(asset.is_file(), f"{slug}: global geometry asset is missing")
        _require(isinstance(record.get("sha256"), str) and SHA256_RE.fullmatch(record["sha256"]), f"{slug}: global boundary checksum is invalid")
        _require(_sha256(asset) == record["sha256"].removeprefix("sha256:"), f"{slug}: global geometry checksum does not match")
        gate_path = root / record.get("boundaryGate", "")
        _require(gate_path.is_file(), f"{slug}: global boundary gate is missing")
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        _require(gate.get("boundary", {}).get("sha256") == record["sha256"].removeprefix("sha256:"), f"{slug}: global boundary gate checksum does not match")
        release_record = release.get("cities", {}).get(slug)
        _require(isinstance(release_record, dict) and release_record.get("boundarySha256") == record["sha256"].removeprefix("sha256:"), f"{slug}: global release checksum does not match")
        source_url = urlparse(record.get("sourceUrl", ""))
        _require(source_url.scheme == "https" and source_url.netloc, f"{slug}: global sourceUrl must be HTTPS")
        _require(isinstance(record.get("selectedShapeNames"), list) and record["selectedShapeNames"], f"{slug}: global feature selection is missing")


def validate_city_catalog(path: Path, root: Path | None = None) -> dict[str, Any]:
    root = (root or path.parents[2]).resolve()
    catalog = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(catalog, dict), "city catalog must be an object")
    _require(catalog.get("contractVersion") == "1.0.0-alpha.1", "city catalog contractVersion is not the frozen browser/API contract")
    registry_ref = catalog.get("boundaryRegistry")
    _require(registry_ref == "data/catalog/city-boundary-coverage.json", "city catalog boundaryRegistry is not the frozen global registry")
    _validate_boundary_registry(root / registry_ref, root)
    cities = catalog.get("cities")
    _require(isinstance(cities, list), "city catalog cities must be an array")
    _require({item.get("slug") for item in cities} == EXPECTED_SLUGS, "city catalog does not contain exactly the requested city set")
    _require(len({item.get("regionId") for item in cities}) == len(cities), "city catalog regionIds must be unique")
    manifest_data = json.loads((root / "contracts" / "examples" / "precomputed" / "manifest.json").read_text(encoding="utf-8"))
    manifest = {item["name"]: item["sha256"] for item in manifest_data["files"]}
    release = json.loads((root / "data" / "metadata" / "boundaries" / "geoBoundaries-IND-ADM2-76128533" / "release-metadata.json").read_text(encoding="utf-8"))
    authority_ids: set[str] = set()
    for pack_path in (root / "apps" / "api" / "reporting" / "jurisdictions").glob("**/*.json"):
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        authority_ids.update(row.get("authorityId") for row in pack.get("records", []) if isinstance(row.get("authorityId"), str))
    for city in cities:
        _validate_city(city, root, manifest, release, authority_ids)
    return {"catalogVersion": catalog.get("catalogVersion"), "cities": len(cities), "validatedPacks": sum(item["processingPack"]["status"] == "VALIDATED" for item in cities)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog/supported-cities.json"))
    args = parser.parse_args()
    result = validate_city_catalog(args.catalog)
    print(f"City catalog passed: {result['cities']} cities, {result['validatedPacks']} validated packs ({result['catalogVersion']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
