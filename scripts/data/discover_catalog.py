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
    "mumbai-city": Pilot(
        key="mumbai-city",
        name="Mumbai City district",
        bbox=(72.79167, 18.88684, 72.88584, 19.05543),
        bbox_source="https://mumbaicity.gov.in/",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    # The following quick targets use the separately gated global city
    # boundaries under data/validated/boundaries/global.  Periods are fixed
    # same-season comparison windows; they are processing inputs, not claims
    # of scientific validation.
    "mumbai": Pilot(
        key="mumbai",
        name="Mumbai City and Mumbai Suburban districts",
        bbox=(72.77589, 18.88684, 72.98404, 19.26932),
        bbox_source="data/metadata/boundaries/global/mumbai.boundary-gate.json",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    "delhi": Pilot(
        key="delhi",
        name="Delhi National Capital Territory",
        bbox=(76.8389449587462, 28.40469199328046, 77.34736061800483, 28.883807228409715),
        bbox_source="data/metadata/boundaries/global/delhi.boundary-gate.json",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    "chennai": Pilot(
        key="chennai",
        name="Chennai district",
        bbox=(80.18339, 12.96704, 80.3101, 13.1489),
        bbox_source="data/metadata/boundaries/global/chennai.boundary-gate.json",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    "bhopal": Pilot(
        key="bhopal",
        name="Bhopal district",
        bbox=(77.16788, 23.07004, 77.65068, 23.89278),
        bbox_source="data/metadata/boundaries/global/bhopal.boundary-gate.json",
        periods=(("2019-10-15", "2019-12-15"), ("2024-10-15", "2024-12-15")),
    ),
    "new-york": Pilot(
        key="new-york",
        name="New York City five borough counties",
        bbox=(-74.26061251699997, 40.496111205000034, -73.70002135199996, 40.91758530000004),
        bbox_source="data/metadata/boundaries/global/new-york.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
    ),
    "washington-dc": Pilot(
        key="washington-dc",
        name="District of Columbia",
        bbox=(-77.11976132299998, 38.79165276400005, -76.90939725499999, 38.99511780500006),
        bbox_source="data/metadata/boundaries/global/washington-dc.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
    ),
    "tokyo": Pilot(
        key="tokyo",
        name="Tokyo prefecture",
        bbox=(138.9428648, 24.224733, 153.9865637, 35.8983844),
        bbox_source="data/metadata/boundaries/global/tokyo.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
    ),
    "london": Pilot(
        key="london",
        name="Greater London boroughs and the City of London",
        bbox=(-0.509720585402481, 51.28676013985681, 0.333995664733011, 51.69187276890297),
        bbox_source="data/metadata/boundaries/global/london.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
    ),
    "cairo": Pilot(
        key="cairo",
        name="Cairo Governorate",
        bbox=(31.2208221, 29.7483062, 31.9090054, 30.3209168),
        bbox_source="data/metadata/boundaries/global/cairo.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
    ),
    "sydney": Pilot(
        key="sydney",
        name="City of Sydney local government area",
        bbox=(151.17498844400006, -33.92431947799997, 151.23372087400003, -33.853499316999944),
        bbox_source="data/metadata/boundaries/global/sydney.boundary-gate.json",
        periods=(("2019-01-15", "2019-03-15"), ("2024-01-15", "2024-03-15")),
    ),
    "rio-de-janeiro": Pilot(
        key="rio-de-janeiro",
        name="Rio de Janeiro municipality",
        bbox=(-43.795410155999946, -23.07501220699993, -43.10198974599996, -22.749328612999932),
        bbox_source="data/metadata/boundaries/global/rio-de-janeiro.boundary-gate.json",
        periods=(("2019-01-15", "2019-03-15"), ("2024-01-15", "2024-03-15")),
    ),
    "reykjavik": Pilot(
        key="reykjavik",
        name="Reykjavíkurborg municipality",
        bbox=(-21.98383292304192, 63.98984905235025, -21.40194315708577, 64.31510866202072),
        bbox_source="data/metadata/boundaries/global/reykjavik.boundary-gate.json",
        periods=(("2019-06-15", "2019-08-15"), ("2024-06-15", "2024-08-15")),
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
