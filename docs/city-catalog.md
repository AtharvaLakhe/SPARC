# SPARC supported-city catalog

**Catalog version:** `2026-08-05.3`
**Frozen API/browser contract:** `1.0.0-alpha.1`  
**Source of truth:** [`data/catalog/supported-cities.json`](../data/catalog/supported-cities.json)  
**Expansion boundary registry:** [`data/catalog/city-boundary-coverage.json`](../data/catalog/city-boundary-coverage.json)
**Validation command:** `\.venv\Scripts\python.exe scripts/validate_city_catalog.py`

The quick-target picker exposes the following fixed set. Country codes are
ISO 3166-1 alpha-2. A city is not treated as an analytical district merely
because its name appears in the picker.

| City | Code | Administrative area | Boundary definition | Analytical coverage | Routing coverage |
|---|---|---|---|---|---|
| Nagpur | IN | Maharashtra / Nagpur district | Validated geoBoundaries gbOpen India ADM2 polygon; EPSG:4326; checksum bound to `nagpur.geojson` | `FULLY_SUPPORTED` (`nagpur-p0-v2`) | `FULLY_SUPPORTED` for verified Maharashtra routes |
| Bengaluru | IN | Karnataka / Bengaluru Urban district | Validated geoBoundaries gbOpen India ADM2 polygon; EPSG:4326; checksum bound to `bengaluru-urban.geojson` | `FULLY_SUPPORTED` (`bengaluru-urban-p0-v2`) | `FULLY_SUPPORTED` for verified Karnataka routes |
| Mumbai City | IN | Maharashtra / Mumbai City district | Validated geoBoundaries gbOpen India ADM2 polygon (`shapeName=Mumbai`); EPSG:4326; checksum bound to `mumbai-city.geojson` | `FULLY_SUPPORTED` (`mumbai-city-p0-v2`) | `FULLY_SUPPORTED` for verified Maharashtra state routes; no municipal route is inferred |
| Delhi | IN | National Capital Territory of Delhi | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `REPORT_GENERATION_ONLY` for this city pack |
| Chennai | IN | Tamil Nadu / Chennai | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `REPORT_GENERATION_ONLY` for this city pack |
| Bhopal | IN | Madhya Pradesh / Bhopal | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `REPORT_GENERATION_ONLY` for this city pack |
| New York | US | New York / New York City | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `FULLY_SUPPORTED` for the verified U.S. EPA example |
| Washington DC | US | District of Columbia | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `FULLY_SUPPORTED` for the verified U.S. EPA example |
| Tokyo | JP | Tokyo | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `UNSUPPORTED_JURISDICTION` |
| London | GB | England / London | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `FULLY_SUPPORTED` for the Environment Agency (England) example |
| Cairo | EG | Cairo Governorate | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `UNSUPPORTED_JURISDICTION` |
| Sydney | AU | New South Wales / Sydney | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `UNSUPPORTED_JURISDICTION` |
| Rio de Janeiro | BR | Rio de Janeiro / Rio de Janeiro | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `UNSUPPORTED_JURISDICTION` |
| Reykjavik | IS | Capital Region / Reykjavik | WGS84 catalog centroid/bbox envelope; not an ADM boundary | `REPORT_GENERATION_ONLY` | `UNSUPPORTED_JURISDICTION` |

## Boundary and processing gates

Nagpur, Bengaluru Urban, and Mumbai City are the entries with a checked-in
boundary gate, validated GeoJSON, release metadata, and accepted precomputed
contract files. The expansion boundary registry separately records pinned,
gated polygons for Delhi, Chennai, Bhopal, New York City, Washington DC,
Tokyo, Greater London, Cairo, Sydney, Rio de Janeiro, and Reykjavík, plus a
larger Mumbai City + Mumbai Suburban scope for a future city-level pack.
The boundary release is geoBoundaries gbOpen India ADM2 release
`IND-ADM2-76128533` (commit `9469f09`, build 12 December 2023). Source-specific
boundary metadata is ODbL 1.0 and the source record permits redistribution;
the exact URLs, attribution, and checksums remain in the release/provenance
JSON files. Survey of India geometry is not used.

The browser/API catalog keeps report-only fallback behavior for expansion
cities until an Earth Engine pack is accepted. The expansion registry is the
processing source of truth: each record is pinned by release ID and selected
feature ID or an exact complete feature-name set, and has a separately gated
GeoJSON, source provenance, licence, raw-source checksum, and boundary
checksum. A registry polygon is still suitable for prototype analysis only
and is not a legal or cadastral boundary. The current Mumbai City pack remains
the existing single-district journey; the expansion Mumbai scope is not
silently substituted into that pack.

`FULLY_SUPPORTED` analytical coverage means a validated processing pack is
available. `REPORT_GENERATION_ONLY` means no numerical satellite estimate is
published: the fallback contract uses null metrics, `NOT_RUN` quality, and an
explicit no-pack reason. SPARC does not insert fabricated numbers into the
dashboard or PDF. `UNSUPPORTED_JURISDICTION` means the report is preserved and
exported locally without a guessed authority or handoff URL.

Before changing the catalog, run the validator. It checks country codes,
unique IDs, centroid/bbox validity, boundary provenance fields and checksums,
validated geometry assets, global boundary-registry gates, precomputed
manifest checksums, pack/boundary bindings, fallback envelopes, coverage-state
consistency, and that every
referenced authority ID exists in a jurisdiction pack. Routing tests exercise
India, United States, Great Britain, and unsupported-country behavior through
the existing jurisdiction registry.
