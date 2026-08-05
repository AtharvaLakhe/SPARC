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
| Delhi | IN | National Capital Territory of Delhi | Validated geoBoundaries gbOpen ADM1 polygon; EPSG:4326; checksum bound to `delhi.geojson` | `FULLY_SUPPORTED` (`delhi-p0-v2`) | `REPORT_GENERATION_ONLY` for this city pack |
| Chennai | IN | Tamil Nadu / Chennai district | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `chennai.geojson` | `FULLY_SUPPORTED` (`chennai-p0-v2`) | `REPORT_GENERATION_ONLY` for this city pack |
| Bhopal | IN | Madhya Pradesh / Bhopal district | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `bhopal.geojson` | `FULLY_SUPPORTED` (`bhopal-p0-v2`) | `REPORT_GENERATION_ONLY` for this city pack |
| New York | US | New York / New York City | Validated geoBoundaries gbOpen city polygon; EPSG:4326; checksum bound to `new-york.geojson` | `FULLY_SUPPORTED` (`new-york-p0-v2`) | `FULLY_SUPPORTED` for the verified U.S. EPA example |
| Washington DC | US | District of Columbia | Validated geoBoundaries gbOpen ADM1 polygon; EPSG:4326; checksum bound to `washington-dc.geojson` | `FULLY_SUPPORTED` (`washington-dc-p0-v2`) | `FULLY_SUPPORTED` for the verified U.S. EPA example |
| Tokyo | JP | Tokyo | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `tokyo.geojson` | `FULLY_SUPPORTED` (`tokyo-p0-v2`) | `UNSUPPORTED_JURISDICTION` |
| London | GB | England / London | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `london.geojson` | `FULLY_SUPPORTED` (`london-p0-v2`) | `FULLY_SUPPORTED` for the Environment Agency (England) example |
| Cairo | EG | Cairo Governorate | Validated geoBoundaries gbOpen ADM1 polygon; EPSG:4326; checksum bound to `cairo.geojson` | `FULLY_SUPPORTED` (`cairo-p0-v2`) | `UNSUPPORTED_JURISDICTION` |
| Sydney | AU | New South Wales / Sydney | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `sydney.geojson` | `FULLY_SUPPORTED` (`sydney-p0-v2`) | `UNSUPPORTED_JURISDICTION` |
| Rio de Janeiro | BR | Rio de Janeiro / Rio de Janeiro | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `rio-de-janeiro.geojson` | `FULLY_SUPPORTED` (`rio-de-janeiro-p0-v2`) | `UNSUPPORTED_JURISDICTION` |
| Reykjavik | IS | Capital Region / Reykjavik | Validated geoBoundaries gbOpen ADM2 polygon; EPSG:4326; checksum bound to `reykjavik.geojson` | `FULLY_SUPPORTED` (`reykjavik-p0-v2`) | `UNSUPPORTED_JURISDICTION` |

## Boundary and processing gates

All fourteen catalog entries now have a checked-in boundary gate, validated
GeoJSON, release metadata, and accepted precomputed contract files. The
expansion boundary registry separately records pinned, gated polygons for
Delhi, Chennai, Bhopal, New York City, Washington DC, Tokyo, Greater London,
Cairo, Sydney, Rio de Janeiro, and Reykjavík, plus a larger Mumbai City +
Mumbai Suburban scope.
The boundary release is geoBoundaries gbOpen India ADM2 release
`IND-ADM2-76128533` (commit `9469f09`, build 12 December 2023). Source-specific
boundary metadata is ODbL 1.0 and the source record permits redistribution;
the exact URLs, attribution, and checksums remain in the release/provenance
JSON files. Survey of India geometry is not used.

The expansion registry is the processing source of truth: each record is
pinned by release ID and selected feature ID or an exact complete feature-name
set, and has a separately gated GeoJSON, source provenance, licence, raw-source
checksum, and boundary checksum. A registry polygon is still suitable for
prototype analysis only and is not a legal or cadastral boundary. The global
Mumbai pack uses the pinned Mumbai City + Mumbai Suburban scope; it is distinct
from the existing `district:mumbai-city` compatibility pack.

`FULLY_SUPPORTED` analytical coverage means a contract-validated processing
pack is available; it does not mean independent accuracy or legal verification.
All current packs retain `quality: unknown` and documented limitations.
`REPORT_GENERATION_ONLY` remains available for future cities that have no pack:
the fallback contract uses null metrics, `NOT_RUN` quality, and an explicit
no-pack reason. SPARC does not insert fabricated numbers into the dashboard or
PDF. `UNSUPPORTED_JURISDICTION` means the report is preserved and exported
locally without a guessed authority or handoff URL.

Before changing the catalog, run the validator. It checks country codes,
unique IDs, centroid/bbox validity, boundary provenance fields and checksums,
validated geometry assets, global boundary-registry gates, precomputed
manifest checksums, pack/boundary bindings, fallback envelopes, coverage-state
consistency, and that every
referenced authority ID exists in a jurisdiction pack. Routing tests exercise
India, United States, Great Britain, and unsupported-country behavior through
the existing jurisdiction registry.
