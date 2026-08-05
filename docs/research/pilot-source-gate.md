# Pilot source and boundary gate

**Run date:** 2026-08-03
**Task:** D0-C-001  
**Status:** district boundary gate passed; controlled P0 processing started; publication gate remains blocked on sensitivity and independent validation

## Google Earth Engine Sentinel-2 metadata discovery

The reproducible metadata-only query is implemented in `scripts/data/discover_earth_engine.py`. It uses the authenticated offline worker and `COPERNICUS/S2_SR_HARMONIZED`, accepts only the three approved district keys, bounds results to 500 images and stores no provider URLs or credentials. `discover_catalog.py` remains the direct-CDSE fallback.

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

## Historical Survey of India research (rejected for geometry)

This section documents the earlier research only. It is not an approved source: no Survey of India ABDB geometry was downloaded, used, redistributed, or included in SPARC.

Confirmed district/subdistrict metadata:

- dataset identifiers `SOI/ABDB/VECTOR/50000/2025/DISTRICT/INDIA` and `SOI/ABDB/VECTOR/50000/2025/SUBDISTRICT/INDIA`;
- edition 2025, published 2026-05-06, temporal lineage 2022–2025;
- nominal scale 1:50,000 and stated horizontal RMSE ±12.5 m;
- horizontal reference recorded as `LCC- WGS84; EPSG7755`;
- Maharashtra and Karnataka boundaries recorded as harmonized with ORGI in 2025;
- owner and required credit: Survey of India;
- access and use constraints both recorded as `copyright`, with Geospatial Guidelines 2021 required.

The pan-India geometry archive was not downloaded. Free access is not permission to redistribute it. No SOI geometry may enter a SPARC repository or release bundle.

The official OGD Platform India `Admin Boundaries` catalog was also checked as a fallback. It describes state, district and block boundaries and identifies the publishing department, but its catalog API and ZIP download were disabled at inspection time. Without an accessible versioned resource, fields, checksum and geometry cannot be verified, so it is not yet an approved substitute.

## geoBoundaries gbOpen India ADM2 boundary evidence

**Selected release:** `IND-ADM2-76128533`, ADM2, represented year 2021, build 2023-12-12, pinned geoBoundaries repository commit `9469f09`.

- Release API: https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/
- Pinned raw archive: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IND/ADM2/geoBoundaries-IND-ADM2-all.zip
- Raw archive SHA-256: `ce028c89b89b62558f52c35c820710ab8a7084fd4cbce46e913e8a78413e6021`
- Release-source attribution: Pathways Data Pvt. Ltd. and `lgdirectory.gov.in`.
- License decision: geoBoundaries presents gbOpen generally as CC BY 4.0, but this release’s own source metadata records Open Data Commons Open Database License 1.0. SPARC follows the source-specific ODbL record and its applicable attribution/share-alike obligations; the selected geometry is not described as CC BY-only.

| SPARC region | Exact ADM2 feature | Geometry / CRS | State-location validation | Validated GeoJSON SHA-256 |
|---|---|---|---|---|
| Nagpur district | `Nagpur`, `shapeID` `76128533B3026318797185` | `Polygon`, EPSG:4326 | Representative point `79.08797740597822, 21.176853476440222` contained by geoBoundaries ADM1 `Mahārāshtra` | `f811022adbe26c7634ba4d884db3251c53bd2d23b8d55e18f6d24fe3cb3b2b33` |
| Bengaluru Urban backup | Legacy provider name `Bangalore`, `shapeID` `76128533B76927648517269`; distinct from `Bangalore Rural` | `Polygon`, EPSG:4326 | Representative point `77.58283692418445, 12.949137851366181` contained by geoBoundaries ADM1 `Karnātaka` | `613c9f5da9e207d2acec5796488754abf0d2e48a6b341f5c0de25cbdc3ffa67a` |
| Mumbai City district | `Mumbai`, `shapeID` `76128533B16442413169750` | `MultiPolygon`, EPSG:4326 | Representative point `72.8338038241462, 18.98076517780284` contained by geoBoundaries ADM1 `Mahārāshtra` | `c49e599f12d917e2f38ac236207cbb0a75037b389b178641e25babf45ef93fa0` |

The raw archive is retained under Git-ignored `data/raw/boundaries/`; one-feature validated GeoJSON files are under `data/validated/boundaries/`; provenance, release metadata, and existing boundary-validator manifests are under `data/metadata/boundaries/`. The release metadata declares 736 ADM2 features while the downloaded GeoJSON contains 735; this discrepancy is recorded as a warning and the two selected features were individually verified.

Every use must display this disclaimer: **This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.**

## P0 common-valid coverage and processing start

The worker `scripts/data.process_earth_engine_p0` validates the local boundary gate and SHA-256 before querying `COPERNICUS/S2_SR_HARMONIZED`. It accepts SCL classes 4/5/6, requires two valid observations per period, calculates each index per observation before a per-period median, and compares only the common-valid footprint. It uses UTM EPSG:32644 for Nagpur and EPSG:32643 for Bengaluru Urban and Mumbai City.

| Region / indicator | Result | Common-valid fraction | Status |
|---|---:|---:|---|
| Nagpur / surface water | completed; fixed-zero and pooled-Otsu sensitivity CSVs imported | 0.9996252842573716 | Both methods show net loss (−8.50 and −10.16 km²); independent validation remains required |
| Bengaluru Urban / surface water | completed | 0.9980801049781208 | Pre-publication; sensitivity and independent validation pending |
| Nagpur / built candidate | completed; constrained-NDBI default and IBI v2 sensitivity CSV imported | 0.9996252842573716 | Material directional disagreement (+158.47 versus −361.52 km² net); withhold a built-change finding pending independent validation and method review |
| Nagpur / vegetation | completed through guarded 10 m full-resolution CSV batch exports; default plus 0.20/0.30/0.40 sensitivity rows imported into the local pre-publication manifest | 0.9996252931776228 | Sensitivity is material (net −27.03, −277.40, and −487.10 km² respectively); independent validation remains required; method and scale were not relaxed |
| Nagpur / vegetation validation frame | completed blinded exploratory sample export | 100 points | Up to 25 points per mapped stable non-target, stable target, gain, and loss stratum; no map labels or NDVI values exported; independent reference labels remain absent |
| Mumbai City / surface water | completed through the Earth Engine pre-publication pack; pooled-Otsu sensitivity imported | 0.9988461038606286 | Default net −0.7923 km²; pooled-Otsu net −0.8909 km²; same loss direction; quality remains `unknown` |
| Mumbai City / vegetation | completed through the Earth Engine pre-publication pack; 0.20/0.30/0.40 sensitivity imported | 0.998921367253273 | Default net −0.9398 km²; all documented thresholds show loss; quality remains `unknown` |
| Mumbai City / built-up | completed through the Earth Engine pre-publication pack; built-IBI sensitivity imported | 0.998846103860629 | Default net −1.4371 km²; IBI net −10.9685 km²; same direction, so the estimate is available with quality `unknown` |

## Gate result

| Gate | Result | Consequence |
|---|---|---|
| Candidate Sentinel-2 products exist for all four fixed windows | Pass | Continue metadata and acquisition design |
| Every discovered product exposes required P0 assets | Pass | Asset-key mapping can be frozen |
| Exact district intersection and common-valid coverage | Pass for completed water/built/vegetation runs | Validated AOIs, per-pixel SCL analysis, and checksum/CRS/method/area-math validated default, vegetation threshold rows, water pooled-Otsu, and built IBI v2 batch imports |
| Boundary version and technical metadata | Pass | Pinned geoBoundaries `IND-ADM2-76128533`; selected features, CRS, state containment, provenance, and checksums verified |
| Boundary redistribution basis | Conditional pass | ODbL attribution and applicable share-alike obligations must accompany any committed, redistributed, or deployed geometry; not CC BY-only |
| OGD boundary fallback artifact | Not used | geoBoundaries release resolves the district-boundary blocker |
| Independent vegetation validation | Pending | A 100-point blinded exploratory frame and label template exist, but no temporally appropriate independent labels, inclusion-probability calculation, or design-consistent accuracy analysis exists |
| Nagpur child-region identity and geometry QA | Pending | Hingna remains provisional; district-only fallback remains active |

D0-C-001 passes for the three district AOIs. D1 raster processing has begun against validated district polygons, never search envelopes. P0 publication remains blocked on independent validation. The 10 m vegetation results and their fixed 0.20/0.30/0.40 sensitivity rows were produced with controlled batch/export processing and imported only after their boundary checksum, CRS, method settings, and area arithmetic matched the approved requests. The sensitivity ranges are material, so the default results remain `quality: unknown`.

## Sources

- Google Earth Engine Sentinel-2 L2A collection: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- Google Earth Engine access: https://developers.google.com/earth-engine/guides/access
- geoBoundaries India ADM2 release API: https://www.geoboundaries.org/api/current/gbOpen/IND/ADM2/
- geoBoundaries gbOpen collection: https://www.geoboundaries.org/
- Open Data Commons Open Database License 1.0: https://opendatacommons.org/licenses/odbl/1.0/
- CDSE STAC fallback: https://stac.dataspace.copernicus.eu/v1/
- Nagpur government coordinate extent: https://gsda.maharashtra.gov.in/en-nagpur-district/
- Bengaluru Urban Government of India district profile: https://dcmsme.gov.in/dips/Bangalore%20Urban%20District.pdf
- Survey of India ABDB: https://surveyofindia.gov.in/pages/administrative-boundary-data-base-abdb-
- Survey of India metadata package: https://surveyofindia.gov.in/documents/Metadata_ABDB.zip
- OGD Platform India Admin Boundaries catalog: https://www.data.gov.in/catalog/admin-boundaries
- Government Open Data License - India: https://data.gov.in/sites/default/files/NDSAP_OpenDataLicense.pdf
