# ADR-001: Multi-provider, STAC-based data access with precomputed demo assets

- **Status:** Superseded for primary Sentinel-2 processing by [ADR-009](ADR-009-earth-engine-processing.md); retained as the direct-CDSE fallback design
- **Date:** 2026-08-02
- **Decision owners:** Codex workstream, reviewed by Shared
- **Applies to:** Imagery discovery, source access, provenance and demo resilience

## Context

SPARC needs Sentinel-2 imagery for P0 water, vegetation and built-up proxy indicators, with Landsat and other official/reference data available where justified. A judged demonstration cannot depend on one external catalog, token service, quota, provider uptime, or venue internet connection.

The primary source must be authoritative and reproducible. At the same time, P0 preprocessing benefits from assets that support efficient range reads and do not require last-minute interactive authentication. The application must preserve dataset identity and attribution regardless of which authorized delivery provider supplied the bytes.

## Decision drivers

- Demonstration reliability within a 3-to-4-day build window.
- Open standards and provider portability.
- Authoritative source identity and defensible provenance.
- Server-side secret isolation.
- Efficient access to only the raster windows/bands needed.
- Compliance with dataset/provider terms.
- No required Google Earth Engine account, quota, or script runtime.

## Decision

1. Use a provider-neutral STAC adapter boundary for scene discovery and asset normalization.
2. Treat the current Copernicus Data Space Ecosystem STAC API at `https://stac.dataspace.copernicus.eu/v1/` as the primary authoritative Sentinel catalog.
3. Permit Earth Search as the operational P0 fallback or delivery source for anonymous, range-readable Sentinel-2 COG assets. Record Earth Search as delivery provider and retain the underlying Copernicus Item/data attribution. Its public service has no SLA and is not the sole production source.
4. Permit Microsoft Planetary Computer as a second STAC fallback. Store stable catalog/item/asset identity and re-sign asset URLs when needed; never persist temporary signed URLs as provenance.
5. Permit USGS Landsat as a sensor/provider fallback under a separately versioned sensor-specific method. Do not mix Sentinel and Landsat results without documenting resolution, band, scale/offset and methodology changes.
6. Do not make Google Earth Engine a runtime, preprocessing, or demo dependency. It may be used later only as an explicitly documented optional research/validation environment.
7. Do not treat the Bhuvan portal as generally open for derivative processing, copying, bulk download or redistribution. A Bhuvan dataset enters the pipeline only after its specific access and reuse permission is recorded.
8. Precompute and verify a primary and backup district package. Live/semi-live access is an enhancement; the critical demonstration uses the package.
9. Keep provider credentials and signing logic on the server/worker. The Vite browser bundle receives no private key, OAuth client secret, object-store credential, or signed provenance URL.

## Adapter contract

Each adapter must expose:

- provider ID and STAC root;
- logical-product-to-collection mapping;
- logical-band/quality-layer-to-asset-key mapping;
- authentication/signing strategy;
- query/filter capability mapping;
- Item normalization while preserving original metadata;
- dataset license, citation and attribution resolver; and
- stable asset identity separate from its current access URL.

Above this boundary, scene-selection, quality masking, indicator and publication code must not branch on provider-specific field names.

## Attribution and terms

- Published modified Sentinel outputs use the official wording `Contains modified Copernicus Sentinel data [Year]` with the applicable year or years.
- A provider endpoint, collection and Item IDs appear in provenance even when the underlying data license belongs to Copernicus.
- Landsat is public-domain US government data; SPARC will include the USGS acknowledgement requested by USGS.
- Each Planetary Computer collection may carry a different underlying dataset license; the collection metadata must be checked rather than assuming one platform-wide license.
- Bhuvan use requires a dataset-specific decision before download, derivative creation or redistribution.

## Options considered

| Option | Advantages | Reasons not selected as sole strategy |
|---|---|---|
| CDSE only | Authoritative Copernicus platform and current STAC API | Authentication/delivery paths, outage or throttling could block the event; one provider is an avoidable risk |
| Earth Search only | Anonymous STAC and COG access is operationally simple | Maintainer explicitly offers no SLA; not authoritative enough to be the only production dependency |
| Planetary Computer only | Public STAC and broad catalog | Throttling and expiring signed asset access require adapter logic; one provider remains a single point of failure |
| Google Earth Engine only | Mature catalog and scalable hosted analysis | Account/quota/runtime dependency and less portable pipeline; violates offline and provider-independence goals |
| Bhuvan-first | India-specific portal and thematic context | Portal-wide terms do not grant general derivative/bulk redistribution rights; dataset suitability/permission is unresolved |
| Direct manually coded provider calls | Lowest initial abstraction | Provider schemas/auth would leak through processing and contract code, making fallback and testing fragile |
| Provider-neutral STAC plus precomputed package | Standards-based, auditable and resilient | **Selected** despite the small adapter and normalization discipline it requires |

## Consequences

### Positive

- A provider outage does not invalidate the architecture or demonstration.
- Stable STAC identifiers improve reproducibility and citations.
- COG delivery can minimize transfer through HTTP range requests.
- Demo outputs remain available without credentials or internet.
- The pipeline can add providers without changing public API schemas.

### Negative and trade-offs

- Collection names, asset keys, auth and query extensions differ and require tested mappings.
- Equivalent products from different providers may not be byte-identical; provenance and checksum checks are required.
- Maintaining fallback support adds integration tests and provider health monitoring.
- Precomputed data are not live and must be visibly dated/labeled.

## Implementation constraints

- Pin one primary and one backup region, periods and source-item set before Day 1 processing.
- Use collection cloud metadata only for discovery; use product-specific pixel QA for masking.
- Bound requests by region, date span, item count and retry budget.
- Cache selected metadata and generated results, not credentials.
- Allowlist outbound hosts/protocols and reject arbitrary caller-supplied URLs.
- Record collection, Item IDs, acquisition times, asset keys, provider, processing baseline, algorithm version and parameters hash.
- Test each adapter with recorded metadata fixtures so catalog unavailability does not block unit/contract tests.

## Reversal conditions

Revisit the primary provider only if access terms, endpoint lifecycle, product availability, performance or reproducibility materially changes. Removing provider abstraction or demo precomputation would require evidence that a single external service meets the event and production reliability targets.

## Sources

Official sources were accessed on 2026-08-02.

- [Copernicus Data Space STAC documentation — European Commission](https://documentation.dataspace.copernicus.eu/APIs/STAC.html). Current endpoint and STAC 1.1.0 support; documents the retired legacy endpoint.
- [Copernicus Data Space terms and conditions — European Commission](https://dataspace.copernicus.eu/terms-and-conditions). Sentinel data access/use terms.
- [Copernicus Data Space FAQ — European Commission](https://documentation.dataspace.copernicus.eu/FAQ.html). Official attribution wording.
- [STAC specification — STAC community](https://stacspec.org/en/about/stac-spec/). Provider-neutral Catalog, Collection, Item and API model.
- [Earth Search repository — Element 84](https://github.com/Element84/earth-search). Public service status and no-SLA statement.
- [Sentinel-2 L2A COGs — Registry of Open Data on AWS](https://registry.opendata.aws/sentinel-2-l2a-cogs/). Anonymous COG/Earth Search access.
- [Planetary Computer documentation — Microsoft](https://planetarycomputer.microsoft.com/docs). Public STAC, throttling and asset-signing behavior.
- [Landsat data access — USGS](https://www.usgs.gov/landsat-missions/landsat-data-access). No-cost Landsat access.
- [Landsat public-domain FAQ — USGS](https://www.usgs.gov/faqs/are-landsat-data-cloud-still-considered-be-within-public-domain). Public-domain status and acknowledgement guidance.
- [Bhuvan terms — NRSC](https://bhuvan.nrsc.gov.in/terms.php). Default use and redistribution restrictions.
