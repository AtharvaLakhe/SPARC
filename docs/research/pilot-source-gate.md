# Pilot source and boundary gate

**Run date:** 2026-08-02  
**Task:** D0-C-001  
**Status:** Earth Engine catalogue pass; boundary redistribution and polygon QA blocked

## Google Earth Engine Sentinel-2 metadata discovery

The reproducible metadata-only query is implemented in `scripts/data/discover_earth_engine.py`. It uses the authenticated offline worker and `COPERNICUS/S2_SR_HARMONIZED`, accepts only the two approved pilot keys, bounds results to 500 images and stores no provider URLs or credentials. `discover_catalog.py` remains the direct-CDSE fallback.

The search envelopes are documented government-published coordinate extents, not analytical district polygons. Counts therefore represent products intersecting the envelope, not products proven to overlap every part of the district.

| Pilot | Period | Items | Items with every required asset | Scene cloud ≤20% | Grid codes |
|---|---:|---:|---:|---:|---|
| Nagpur | 2019-10-15–2019-12-15 | 215 | 215 | 140 | 43QHC, 43QHD, 43QHE, 44QKH, 44QKJ, 44QKK, 44QLH, 44QLJ, 44QLK |
| Nagpur | 2024-10-15–2024-12-15 | 221 | 221 | 140 | same nine grids |
| Bengaluru Urban | 2019-01-15–2019-03-15 | 48 | 48 | 39 | 43PGP, 43PGQ, 43PHP, 43PHQ |
| Bengaluru Urban | 2024-01-15–2024-03-15 | 48 | 48 | 36 | same four grids |

Required bands are B2, B3, B4, B8, B11, B12 and SCL. Scene-level cloud percentage is only a discovery filter; it does not establish clear AOI coverage.

Raw reports are stored under the Git-ignored `data/raw/earth-engine-discovery/` directory. Their SHA-256 hashes are:

| Report | SHA-256 |
|---|---|
| `nagpur-2019-10-15-2019-12-15.json` | `4ef8d5ab4ab15111bd4fd630aff1a0a5abf9c623b4441bfd4ef4f022b7658222` |
| `nagpur-2024-10-15-2024-12-15.json` | `f6206e07120d79423857be30a235db5ccce9d8afdeb24293625652f4871692bf` |
| `bengaluru-urban-2019-01-15-2019-03-15.json` | `89661ac48e9eb724c5f55185b12c46a43fb3c2e1ab741fbb494be279ee83ca97` |
| `bengaluru-urban-2024-01-15-2024-03-15.json` | `fdb4b83080a9f58fb3ff41e4dee4c4033a61f18a05b88b8879d8b87e00038d46` |

## Survey of India boundary metadata

The official 38,879-byte `Metadata_ABDB.zip` was downloaded from the Survey of India ABDB page and inspected without modifying the four workbooks. Archive SHA-256: `1a14716b73f00fc8391f2708a7975c2f2c1ad4a4e91aafb6dce6546a039e9514`.

Confirmed district/subdistrict metadata:

- dataset identifiers `SOI/ABDB/VECTOR/50000/2025/DISTRICT/INDIA` and `SOI/ABDB/VECTOR/50000/2025/SUBDISTRICT/INDIA`;
- edition 2025, published 2026-05-06, temporal lineage 2022–2025;
- nominal scale 1:50,000 and stated horizontal RMSE ±12.5 m;
- horizontal reference recorded as `LCC- WGS84; EPSG7755`;
- Maharashtra and Karnataka boundaries recorded as harmonized with ORGI in 2025;
- owner and required credit: Survey of India;
- access and use constraints both recorded as `copyright`, with Geospatial Guidelines 2021 required.

The pan-India geometry archive is 202,524,438 bytes and was not downloaded. Free access is not permission to redistribute it. No SOI geometry may enter a public repository or release bundle until the applicable product terms explicitly permit that use.

The official OGD Platform India `Admin Boundaries` catalog was also checked as a fallback. It describes state, district and block boundaries and identifies the publishing department, but its catalog API and ZIP download were disabled at inspection time. Without an accessible versioned resource, fields, checksum and geometry cannot be verified, so it is not yet an approved substitute.

## Gate result

| Gate | Result | Consequence |
|---|---|---|
| Candidate Sentinel-2 products exist for all four fixed windows | Pass | Continue metadata and acquisition design |
| Every discovered product exposes required P0 assets | Pass | Asset-key mapping can be frozen |
| Exact district intersection and common-valid coverage | Pending | Requires approved district polygons and per-pixel SCL analysis |
| Boundary version and technical metadata | Pass | 2025 SOI ABDB is the current candidate |
| Boundary redistribution basis | Blocked | Do not download/package geometry as a distributable project asset |
| OGD boundary fallback artifact | Blocked | Catalog exists, but no downloadable/API resource was available to validate |
| Nagpur child-region identity and geometry QA | Pending | Hingna remains provisional; district-only fallback remains active |

D0-C-001 remains incomplete until the redistribution basis and exact geometry checks are resolved. D1 raster processing must not substitute a search envelope for the district polygon.

## Sources

- Google Earth Engine Sentinel-2 L2A collection: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- Google Earth Engine access: https://developers.google.com/earth-engine/guides/access
- CDSE STAC fallback: https://stac.dataspace.copernicus.eu/v1/
- Nagpur government coordinate extent: https://gsda.maharashtra.gov.in/en-nagpur-district/
- Bengaluru Urban Government of India district profile: https://dcmsme.gov.in/dips/Bangalore%20Urban%20District.pdf
- Survey of India ABDB: https://surveyofindia.gov.in/pages/administrative-boundary-data-base-abdb-
- Survey of India metadata package: https://surveyofindia.gov.in/documents/Metadata_ABDB.zip
- OGD Platform India Admin Boundaries catalog: https://www.data.gov.in/catalog/admin-boundaries
- Government Open Data License - India: https://data.gov.in/sites/default/files/NDSAP_OpenDataLicense.pdf
