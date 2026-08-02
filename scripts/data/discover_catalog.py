"""Metadata-only Sentinel-2 discovery against the official CDSE STAC API."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


STAC_ORIGIN = "https://stac.dataspace.copernicus.eu"
STAC_SEARCH = f"{STAC_ORIGIN}/v1/search"
COLLECTION = "sentinel-2-l2a"
REQUIRED_ASSETS = (
    "B02_10m",
    "B03_10m",
    "B04_10m",
    "B08_10m",
    "B11_20m",
    "B12_20m",
    "SCL_20m",
    "product_metadata",
)
MAX_PAGES = 30
MAX_ITEMS = 3_000
MAX_RESPONSE_BYTES = 32_000_000


@dataclass(frozen=True)
class Pilot:
    key: str
    name: str
    bbox: tuple[float, float, float, float]
    bbox_source: str
    periods: tuple[tuple[str, str], ...]


PILOTS = {
    "nagpur": Pilot(
        key="nagpur",
        name="Nagpur district",
        bbox=(78.25, 20.583333, 79.666667, 21.733333),
        bbox_source="https://gsda.maharashtra.gov.in/en-nagpur-district/",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    "bengaluru-urban": Pilot(
        key="bengaluru-urban",
        name="Bengaluru Urban district",
        bbox=(77.366667, 12.65, 77.866667, 13.3),
        bbox_source="https://dcmsme.gov.in/dips/Bangalore%20Urban%20District.pdf",
        periods=(("2019-01-15", "2019-03-15"), ("2024-01-15", "2024-03-15")),
    ),
}


def _safe_next_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "stac.dataspace.copernicus.eu":
        raise RuntimeError("STAC pagination attempted to leave the approved HTTPS host")
    if parsed.path != "/v1/search" or parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError("STAC pagination returned an unexpected URL")
    return value


class _ApprovedRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, _safe_next_url(newurl))


HTTP_OPENER = build_opener(_ApprovedRedirectHandler())


def _get_json(url: str, timeout_seconds: int = 60) -> dict[str, Any]:
    request = Request(
        _safe_next_url(url),
        headers={"Accept": "application/geo+json, application/json", "User-Agent": "SPARC/1.0 metadata-discovery"},
    )
    with HTTP_OPENER.open(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"application/json", "application/geo+json"}:
            raise RuntimeError(f"Unexpected STAC content type: {content_type}")
        content_length = response.headers.get("Content-Length")
        if content_length is not None and int(content_length) > MAX_RESPONSE_BYTES:
            raise RuntimeError("STAC response exceeded the byte safety limit")
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise RuntimeError("STAC response exceeded the byte safety limit")
        payload = json.loads(body)
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise RuntimeError("STAC response is not a FeatureCollection")
    return payload


def _sanitize_asset(key: str, asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": key,
        "mediaType": asset.get("type"),
        "sizeBytes": asset.get("file:size"),
        "checksum": asset.get("file:checksum"),
        "roles": asset.get("roles", []),
    }


def _sanitize_item(item: dict[str, Any]) -> dict[str, Any]:
    properties = item.get("properties") or {}
    assets = item.get("assets") or {}
    available = [key for key in REQUIRED_ASSETS if key in assets]
    return {
        "id": item.get("id"),
        "collection": item.get("collection"),
        "datetime": properties.get("datetime"),
        "bbox": item.get("bbox"),
        "cloudCoverPercent": properties.get("eo:cloud_cover"),
        "platform": properties.get("platform"),
        "gridCode": properties.get("grid:code"),
        "processingLevel": properties.get("processing:level"),
        "processingVersion": properties.get("processing:version"),
        "relativeOrbit": properties.get("sat:relative_orbit"),
        "requiredAssetsPresent": available,
        "assets": [_sanitize_asset(key, assets[key]) for key in available],
    }


def discover(pilot: Pilot, start: str, end: str) -> dict[str, Any]:
    query = urlencode(
        {
            "collections": COLLECTION,
            "bbox": ",".join(str(value) for value in pilot.bbox),
            "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
            "limit": "100",
        },
        safe=",:/",
    )
    next_url: str | None = f"{STAC_SEARCH}?{query}"
    items: list[dict[str, Any]] = []
    pages = 0
    while next_url is not None:
        pages += 1
        if pages > MAX_PAGES:
            raise RuntimeError("STAC result exceeded the page safety limit")
        payload = _get_json(next_url)
        features = payload.get("features")
        if not isinstance(features, list):
            raise RuntimeError("STAC response features must be an array")
        items.extend(_sanitize_item(item) for item in features)
        if len(items) > MAX_ITEMS:
            raise RuntimeError("STAC result exceeded the item safety limit")
        next_links = [link for link in payload.get("links", []) if link.get("rel") == "next"]
        if len(next_links) > 1:
            raise RuntimeError("STAC response contained multiple next links")
        next_url = _safe_next_url(next_links[0]["href"]) if next_links else None

    items.sort(key=lambda item: (item.get("datetime") or "", item.get("id") or ""))
    complete = [item for item in items if len(item["requiredAssetsPresent"]) == len(REQUIRED_ASSETS)]
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
        "catalog": {"provider": "CDSE", "endpoint": STAC_ORIGIN + "/v1/", "collection": COLLECTION},
        "summary": {
            "itemCount": len(items),
            "itemsWithAllRequiredAssets": len(complete),
            "minimumSceneCloudCoverPercent": min(cloud_values) if cloud_values else None,
            "maximumSceneCloudCoverPercent": max(cloud_values) if cloud_values else None,
            "distinctGridCodes": sorted({item["gridCode"] for item in items if item["gridCode"]}),
        },
        "items": items,
        "licenseAndAttribution": [
            "Copernicus Sentinel data; derived outputs must state: Contains modified Copernicus Sentinel data [year]."
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", choices=["all", *PILOTS], default="all")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/catalog-discovery"))
    args = parser.parse_args()

    selected = PILOTS.values() if args.pilot == "all" else (PILOTS[args.pilot],)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for pilot in selected:
        for start, end in pilot.periods:
            report = discover(pilot, start, end)
            target = args.output_dir / f"{pilot.key}-{start}-{end}.json"
            target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{target}: {report['summary']['itemCount']} items")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
