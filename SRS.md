# SPARC Software Requirements Specification

**Version:** 0.1 planning baseline  
**Status:** Proposed for Day 0 freeze  
**Date:** 2026-08-02

## 1. Purpose

This SRS defines the testable requirements for the SPARC prototype: a district-level environmental decision-support dashboard using satellite-derived proxy indicators. It governs the future browser application, API, precomputed data pack, geospatial processing, provenance, validation, accessibility, deployment, and optional user-provided 3D showcase.

## 2. Scope

The P0 prototype covers Nagpur district, a Bengaluru Urban backup, same-season before/after comparison, surface-water-area, vegetation/green-cover, and built-up-area proxies, district summaries, at least one subdistrict drill-down, plain-language interpretation, provenance, quality evidence, responsive presentation, and an internet-independent demonstration path.

Land-surface temperature, surface urban heat island, time series, automated scene discovery, live processing, raster tiles, reports, and supplied 3D models are P1. Accounts, predictive modelling, automated policy recommendations, and national-scale operations are outside the prototype.

## 3. Definitions

| Term | Meaning in SPARC |
|---|---|
| Proxy indicator | A satellite-derived environmental signal related to an SDG topic but not asserted to implement the official UN methodology |
| Baseline period | The earlier, bounded acquisition/composite window |
| Comparison period | The later, bounded acquisition/composite window |
| Common valid footprint | Pixels valid in both periods after QA masking and alignment |
| Data quality | Observable evidence such as valid coverage, scene count, sensitivity, and validation—not an invented correctness probability |
| Demo mode | Local immutable results served without live provider calls |
| Live mode | Catalog discovery and processing or retrieval performed after a request |
| Region | District, subdistrict/tahsil, or block represented by an opaque stable ID |
| P0/P1/P2 | Required prototype / strong enhancement / optional future scope |

## 4. Product Perspective and Architecture Boundary

The planned browser is a React/TypeScript/Vite client. It may consume the same schemas through either a local demo transport or an HTTP API transport. The planned FastAPI server validates requests and returns results; geospatial processing is a separate module/CLI and does not run as unbounded work inside synchronous handlers. P0 runtime results are immutable files, not a concurrent database.

### Code classifications

| Planned area | Classification | Responsibility |
|---|---|---|
| `apps/web/**` | Browser/client code | User interaction, local validation, transport selection, maps, charts, explanations, accessible fallbacks |
| `apps/api/**` | Server/backend code | HTTP validation, result lookup, response/error semantics, restricted job control |
| `services/geoprocessing/**` | Server/offline processing code | Catalog adapters, raster/vector processing, zonal statistics, provenance generation |
| `packages/contracts/**` | Shared code/schema | Canonical data shapes and future generated bindings |
| `scripts/data/**`, build configs | Build/processing configuration | Reproducible acquisition/precomputation and packaging |
| `data/demo/**` | Static runtime data | Immutable offline response and layer assets |

## 5. Users and Operating Environment

### User classes

- District and subdistrict administrators seeking a quick environmental summary.
- NGOs and community organizations preparing local evidence or prioritizing field checks.
- CSR and environmental-consulting teams screening locations and communicating trends.
- Researchers, reviewers, and judges examining methods, provenance, quality, and scalability.

### Operating environment

- Current desktop Chrome, Edge, Firefox, and Safari where MapLibre requirements are met.
- Responsive layouts down to a 360 CSS-pixel viewport.
- A local HTTP server for the offline demonstration; `file://` is not supported.
- Future server execution in a pinned Linux container with compatible GDAL/Rasterio/NumPy versions.

## 6. Assumptions and Constraints

- Nagpur is the primary pilot and Bengaluru Urban is the backup.
- P0 uses precomputed real results once implementation begins; the current contract examples remain explicitly synthetic.
- Internet access, provider credentials, and WebGL may be unavailable during the demonstration.
- Google Earth Engine is the primary offline-processing dependency. Its authenticated project and credentials are server/worker-only; the released demo remains independent of it.
- User-provided Earth and satellite models are unavailable for inspection and cannot be assumed compatible with any runtime.
- Boundary and dataset redistribution require a verified dataset-specific license and attribution record.
- Scientific results describe observed association, not causation.

## 7. Functional Requirements

### Region and comparison selection

- **FR-REGION-001:** The system shall list every available district and child region with an opaque ID, name, type, parent ID where applicable, bounding box, centroid, and supported indicators.
- **FR-REGION-002:** The P0 data pack shall contain Nagpur district and at least one Nagpur subdistrict; acceptance requires a successful district-to-subdistrict navigation.
- **FR-REGION-003:** The offline pack shall contain a separately selectable Bengaluru Urban backup and shall not require a contract change to add another region.
- **FR-REGION-004:** Unknown or unavailable region IDs shall produce a structured `404` response or an accessible client error without rendering stale data from another region.
- **FR-PERIOD-001:** A comparison request shall contain explicit inclusive start and end dates for baseline and comparison periods.
- **FR-PERIOD-002:** The server and demo manifest shall reject a start date after its end date and unsupported period combinations.
- **FR-PERIOD-003:** The interface shall display both composite windows and their season labels next to every result.
- **FR-PERIOD-004:** If periods fail the same-season policy, the result shall carry a visible comparability warning and shall not receive a high quality grade.

### Surface water

- **FR-WATER-001:** The P0 system shall report baseline area, comparison area, absolute change, percentage change when defined, gain, loss, common-valid coverage, effective resolution, method version, and units for the open-surface-water proxy.
- **FR-WATER-002:** The P0 method shall use Sentinel-2 L2A MNDWI on a 20 m analytical grid, with one frozen decision rule applied to both periods.
- **FR-WATER-003:** The method record shall expose the primary threshold and at least one documented sensitivity or corroboration result.
- **FR-WATER-004:** When baseline water area is zero, percentage change shall be `null` with an explanatory reason rather than NaN or infinity.
- **FR-WATER-005:** User-facing text shall state that the proxy does not measure water volume, groundwater, water quality, every wetland, or causation.

### Vegetation and green cover

- **FR-VEG-001:** The P0 system shall report median NDVI for both periods, median change, a labelled green-cover proxy where configured, common-valid coverage, and effective 10 m resolution.
- **FR-VEG-002:** NDVI shall be calculated per valid Sentinel-2 observation before same-season compositing.
- **FR-VEG-003:** A binary green-cover threshold shall be recorded as a prototype heuristic, kept identical across periods, and accompanied by sensitivity information.
- **FR-VEG-004:** User-facing and API text shall not equate NDVI or green-cover proxy change with forest loss.
- **FR-VEG-005:** Agriculture, rainfall, irrigation, phenology, harvest, soil background, and residual cloud shall be represented as possible limitations.

### Built-up area

- **FR-BUILT-001:** The P0 system shall report baseline, comparison, gain, loss, net, and percentage change for a satellite-derived built-up-area proxy.
- **FR-BUILT-002:** The no-Earth-Engine P0 method shall use a documented Sentinel-2 spectral consensus with NDBI/IBI diagnostics and vegetation/water exclusions.
- **FR-BUILT-003:** Thresholds and cleanup rules shall be calibrated or pooled once and then kept fixed across periods.
- **FR-BUILT-004:** Results shall disclose bare soil, dry vegetation, construction, reflective roofs, mixed pixels, and minimum-mapping-unit limitations.
- **FR-BUILT-005:** Dynamic World, WorldCover, or GHSL agreement shall be identified as corroboration and not represented as independent ground truth.

### Land-surface temperature and surface UHI

- **FR-LST-001:** P1 LST shall use Landsat 8/9 Collection 2 Level-2 Surface Temperature with QA and documented scaling.
- **FR-LST-002:** The interface shall identify the measurement as surface temperature and shall not present it as air temperature or direct heat exposure.
- **FR-LST-003:** A surface-UHI result shall document its persistent urban mask, rural reference definition, acquisition dates, and uncertainty/quality evidence.
- **FR-LST-004:** A one-scene period shall be labelled a low-quality snapshot.
- **FR-LST-005:** Sentinel-2 shall not be listed as a thermal data source.

### Summary, maps, layers, and interpretation

- **FR-SUMMARY-001:** The district summary shall present the three P0 proxy results, periods, quality grades, data mode, and last-generation time on one responsive screen.
- **FR-MAP-001:** A result shall provide a layer descriptor with type, representation, bounds, legend, attribution, content version/checksum, and offline availability.
- **FR-MAP-002:** The client shall resolve layers by opaque `layerId` and shall not request a user-provided remote raster URL.
- **FR-MAP-003:** Every map-only pattern shall have a text/table alternative that communicates the same result.
- **FR-MAP-004:** The dashboard shall remain usable when WebGL is unavailable by showing a static map/image and region/result controls.
- **FR-INTERP-001:** Every result shall include a deterministic plain-language summary, caveats, and rule/version identifier.
- **FR-INTERP-002:** Interpretations shall use observational wording such as “the mapped proxy increased” and shall not claim a cause or prescribe policy as fact.
- **FR-PROVENANCE-001:** Every result shall expose dataset/provider, mission, collection/product, source item identity, acquisition dates, license/citation, algorithm version, parameters hash, analysis CRS, and generation time.
- **FR-PROVENANCE-002:** Provenance shall not store an expiring signed asset URL or a secret-bearing request.

### Demo and live modes

- **FR-DEMO-001:** The P0 critical journey shall complete with the network disconnected after the local bundle has started.
- **FR-DEMO-002:** Demo and API transports shall produce data that validates against the same canonical schemas.
- **FR-DEMO-003:** Demo mode shall display a persistent badge, data-generation date, dataset version, and provenance.
- **FR-DEMO-004:** Automatic live-to-demo fallback shall occur only for documented connectivity, timeout, or service-unavailable failures and shall be disclosed.
- **FR-DEMO-005:** Validation, authentication, authorization, or unsupported-request errors shall not trigger automatic fallback to unrelated demo data.
- **FR-DEMO-006:** A backup-region demo pack shall pass the same manifest, checksum, schema, and offline checks as the primary pack.
- **FR-LIVE-001:** A future live request shall first check an immutable deterministic result key before starting processing.
- **FR-LIVE-002:** Expensive live processing shall return `202` with a status location rather than block an HTTP request until completion.

### 3D assets

- **FR-3D-001:** The analytical dashboard shall not import, wait for, or require either user-provided 3D model.
- **FR-3D-002:** No runtime shall be selected until format, hierarchy, coordinate system, animation, textures, file size, license, and rendering tests are recorded.
- **FR-3D-003:** The 3D showcase shall be lazy-loaded, optional, reduced-motion aware, keyboard bypassable, and paired with an equivalent 2D action.
- **FR-3D-004:** WebGL, load, format, or budget failure shall show a 2D/poster fallback without blocking region selection.
- **FR-3D-005:** Mobile devices shall receive the fallback when the approved mobile transfer or performance budget is exceeded.

## 8. API and Data Requirements

- **FR-API-001:** The API shall use `/api/v1` path versioning and JSON encoded as UTF-8.
- **FR-API-002:** Response metadata shall contain schema version, request ID, generation time, data mode, partial flag, and warnings.
- **FR-API-003:** API failures shall use `application/problem+json` and RFC 9457 fields plus stable `code`, `traceId`, and invalid-parameter details where safe.
- **FR-API-004:** A precomputed/cache comparison hit shall return `200`; accepted asynchronous work shall return `202` with `Location`.
- **FR-API-005:** A usable partial result shall return `200` with `meta.partial=true`; `206` shall not represent partial scientific completeness.
- **FR-API-006:** `POST /comparisons` shall support an idempotency key and reject conflicting reuse with `409`.
- **FR-API-007:** The OpenAPI document and all committed examples shall validate against the canonical shared schemas.
- **FR-API-008:** Every endpoint shall document method, URL, caller, request headers/body/query, authentication, validation, business behavior, dependencies, success, errors, status meanings, and security concerns.
- **FR-DATA-001:** Dates shall use ISO `YYYY-MM-DD`; timestamps shall use UTC RFC 3339.
- **FR-DATA-002:** GeoJSON exchange coordinates shall follow longitude/latitude order, while area computation shall use the recorded projected CRS.
- **FR-DATA-003:** JSON numeric fields shall never contain NaN or infinity; unavailable metrics shall be `null` plus a machine-readable reason.
- **FR-DATA-004:** Every immutable demo asset shall have a media type, byte size, cryptographic checksum, content version, and relative path in the manifest.

## 9. Validation and Quality Requirements

- **FR-QUALITY-001:** Each indicator result shall contain a quality level of `high`, `medium`, `low`, or `unknown`, a method version, reasons, warnings, and evidence components.
- **FR-QUALITY-002:** A high grade shall require a prespecified independent validation target; agreement with another satellite-derived product alone is insufficient.
- **FR-QUALITY-003:** The system shall report common-valid coverage, cloud/nodata coverage, scene counts, acquisition dates, and threshold/method sensitivity where applicable.
- **FR-VALIDATION-001:** Threshold-tuning and validation samples shall be separate.
- **FR-VALIDATION-002:** Change validation shall distinguish stable target, stable non-target, gain, and loss classes.
- **FR-VALIDATION-003:** Formal validation shall report an area-weighted confusion matrix, user's and producer's accuracy, omission, commission, and confidence intervals when sample design supports them.
- **FR-VALIDATION-004:** If independent validation is incomplete, the UI and API shall say so and shall not imply measured local accuracy.

## 10. Non-functional Requirements

### Performance and reliability

- **NFR-PERF-001:** A cached/demo summary JSON request shall target a 95th-percentile response below 500 ms on the demo laptop after startup.
- **NFR-PERF-002:** The critical dashboard shall target meaningful content within 3 seconds from local HTTP on the demo laptop.
- **NFR-PERF-003:** P0 map assets shall avoid a required tile server; any static layer exceeding the documented package budget shall be simplified or replaced with an image fallback.
- **NFR-PERF-004:** Optional 3D transfer shall target at most 10 MB compressed on desktop and 3 MB on mobile before the fallback policy applies.
- **NFR-RELIABILITY-001:** Primary and backup demo journeys shall pass with internet disabled.
- **NFR-RELIABILITY-002:** A health check shall not make external provider or database calls.
- **NFR-RELIABILITY-003:** No essential P0 capability shall be scheduled exclusively for optional Day 4.
- **NFR-RELIABILITY-004:** Provider, tile, 3D, and basemap failures shall be isolated from summary metrics and provenance.

### Accessibility and responsive design

- **NFR-ACCESS-001:** The planned interface shall target WCAG 2.2 AA for keyboard access, focus visibility, semantics, labels, contrast, motion, errors, and alternatives.
- **NFR-ACCESS-002:** All interactive controls shall be operable without a pointer and have a visible focus state.
- **NFR-ACCESS-003:** Charts and maps shall have adjacent headings, summaries, units, legends, and accessible data tables.
- **NFR-ACCESS-004:** Status, quality, gain/loss, and severity shall not be conveyed by color alone.
- **NFR-ACCESS-005:** Layout and critical actions shall work at 360 px width and 200% browser zoom without two-dimensional page scrolling.
- **NFR-ACCESS-006:** `prefers-reduced-motion` shall disable nonessential camera movement, orbit, and animated transitions.

### Security and privacy

- **NFR-SEC-001:** No private token, credential, password, database URL, or signed URL shall appear in browser code, committed files, logs, provenance, or error responses.
- **NFR-SEC-002:** Only non-secret configuration may use a `VITE_` prefix.
- **NFR-SEC-003:** API inputs shall have enum/format validation, maximum body and date-span limits, approved region/indicator IDs, and request timeouts.
- **NFR-SEC-004:** CORS shall allow exact configured browser origins rather than `*` when credentials or restricted endpoints exist.
- **NFR-SEC-005:** Outbound provider hosts and local data roots shall be allowlisted; request values shall not become filesystem paths, shell commands, SQL, or fetch URLs.
- **NFR-SEC-006:** Public comparison creation shall be rate-limited; processing-job creation shall be disabled in P0 and later restricted.
- **NFR-PRIVACY-001:** P0 shall collect no accounts, personal profiles, precise user locations, or user-authored content.
- **NFR-PRIVACY-002:** Operational logs shall use request IDs and coarse diagnostics without IP retention beyond hosting necessity or provider credentials.

### Maintainability, portability, and provenance

- **NFR-MAINT-001:** OpenAPI and canonical JSON Schemas shall be the single source for future generated frontend/backend types.
- **NFR-MAINT-002:** Generated files shall name their source and tool version and shall not be edited manually.
- **NFR-MAINT-003:** Geospatial dependencies and native libraries shall be pinned as a tested compatibility matrix before event implementation.
- **NFR-PORT-001:** The demo bundle shall use relative URLs and local HTTP and shall not require a vendor account at runtime.
- **NFR-PROVENANCE-001:** A result shall remain traceable to immutable source identities, processing parameters, algorithm version, and checksum after upstream signed URLs expire.
- **NFR-PROVENANCE-002:** Dataset and map attribution shall be visible in the interface and preserved in exported material.

## 11. Deployment Requirements

- **NFR-DEPLOY-001:** The primary release procedure shall produce a self-contained local demo bundle and verification report.
- **NFR-DEPLOY-002:** Cloud deployment shall be optional and shall not be the sole recovery path.
- **NFR-DEPLOY-003:** Runtime writes shall not be required for immutable demo results because common cloud filesystems are ephemeral.
- **NFR-DEPLOY-004:** The planned API container shall expose a cheap liveness endpoint and fail startup on missing required production configuration without printing secret values.

## 12. Acceptance Criteria

The P0 prototype is accepted only when:

1. Nagpur and the Bengaluru Urban backup complete the critical journey using local HTTP with internet disabled.
2. Water, vegetation, and built-up proxy results show periods, units, changes, quality evidence, provenance, plain-language meaning, and limitations.
3. At least one Nagpur subdistrict drill-down works.
4. API responses and bundled demo payloads validate against the same frozen contract.
5. Normal, invalid, empty, partial, upstream-failure, server-failure, and unauthorized-job scenarios have defined behavior and tests.
6. Keyboard-only, 360 px, 200% zoom, reduced-motion, no-WebGL, and non-color alternatives pass.
7. No required network, remote basemap, live provider, database, or 3D asset exists in the critical path.
8. All sources, licenses, attributions, mock status, and proxy limitations are visible and accurate.
9. A secret scan, contract validation, offline verification, and demo rehearsal pass from a clean release bundle.

## 13. Out of Scope

- Official UN indicator reporting or certification.
- Causal attribution of environmental change.
- National-scale or unrestricted user-defined processing.
- Accounts, saved views, collaboration, payments, or personal data.
- Predictive models or AI-generated policy recommendations.
- A required globe/3D workflow, external model acquisition, or unapproved model conversion.
- Real-time guarantees, complex queues, Kubernetes, or a P0 operational spatial database.

## 14. Future Enhancements

After P0 validation: additional districts, validated block coverage, same-season time series, Landsat surface-UHI, downloadable reports, provider-neutral live jobs, COG/CDN tile delivery, managed PostGIS metadata, calibrated local classifiers, model-inspected 3D enhancement, accounts only if a validated need emerges, and production monitoring/cost controls.
