# SPARC delivery status

**Assessed:** 2026-08-03
**Current stage:** Stage 2 of 5, entering Stage 3 — district evidence is packaged for integration preparation; not a release candidate

This is an evidence-based delivery status, not a percentage derived from line count. A completed visual component does not substitute for a validated data result, and a completed data export does not substitute for a usable dashboard.

## Current position

| Stage | Status | Evidence | Exit condition |
|---|---|---|---|
| 1. Contract and safe mock API | Substantially complete | OpenAPI/schema tests pass; FastAPI serves only allowlisted synthetic fixtures with safe errors | Real immutable artifacts can be served through the same contract without weakening validation |
| 2. Boundary and P0 evidence | In progress | geoBoundaries Nagpur and Bengaluru Urban district gates passed; water, built-candidate, vegetation, vegetation sensitivity, and a blinded vegetation label frame exist | Every public P0 result has completed sensitivity and independent validation, with required provenance |
| 3. Result packaging and API integration | In progress | A schema-checked, non-overwritable local Nagpur pre-publication pack was built from three validated report digests; the API intentionally reads only synthetic fixtures | Contract-valid, immutable, attributable demo pack for Nagpur and Bengaluru Urban; no request-time raster work |
| 4. Analytical dashboard | Not started | `orbital-website/` is a separate Three.js globe/targeting reference, not an SPARC data client | Accessible dashboard implements the P0 journey against demo and API transports |
| 5. Offline release and rehearsal | Not started | Unit/contract/API tests pass, but no integrated demo bundle exists | Primary and backup journeys work from local HTTP with offline, accessibility, security, and evidence checks |

## Delivery estimate

The following is a planning estimate for an honest P0 demo candidate, not a scientific quality score.

| Workstream | Approximate readiness | Why it is not further along |
|---|---:|---|
| Boundary and processing foundation | 55% | District geometry and representative P0 runs exist, but water/built sensitivity, independent reference labels, formal accuracy analysis, approved child geometry, and a full backup pack remain |
| Contract and API | 45% | The contract and read-only mock API are tested and the offline pre-publication pack boundary exists, but real immutable result-pack loading and data-mode handling do not exist |
| Analytical frontend | 15% | The Orbital showcase has polished globe targeting, but no SPARC dashboard, data transport, result rendering, or accessible fallback exists |
| Integration, offline bundle, and release verification | 15% | A local Nagpur pre-publication pack now exists, but it is not connected to a browser journey and no cold-start offline rehearsal has occurred |
| **Overall P0 demo candidate** | **about 35–40%** | The remaining work is weighted toward integration, accessible UI, real-result packaging, and evidence gates rather than more visual polish |

Roughly **60–65% remains** before an honest P0 demo candidate. A public or production claim is further away because the current vegetation result is threshold-sensitive and no indicator has formal independent validation.

## What exists today

### Processing and evidence

- Validated prototype district AOIs: Nagpur and Bengaluru Urban from geoBoundaries India ADM2, with source-specific ODbL handling and the non-authoritative-boundary disclaimer.
- Pre-publication Sentinel-2 P0 summaries: Nagpur water, vegetation, built candidate, and Bengaluru Urban water.
- Vegetation threshold sensitivity at NDVI 0.20, 0.30, and 0.40. Its net green-cover proxy change ranges from −27.03 km² to −487.10 km², so the default result remains `quality: unknown`.
- A blinded, 100-point exploratory Nagpur vegetation label frame and controlled label template. It contains no independent labels and is not a validation result.
- An ignored local `nagpur-p0-v1.json` pre-publication pack built from the three Nagpur reports. Its SHA-256 is `95e3c9befc774a91f74d29c165f1d834e0bbf92ad5ab2bc6b8e50bd448afb4d2`; it records report checksums, fixed periods, method controls, threshold sensitivity, `quality: unknown`, validation state, and the mandatory boundary disclaimer. It is not an API response or deployable result.

### Server and contract

- A FastAPI read-only API with input limits, allowlisted identifiers, explicit CORS, safe RFC 9457-style errors, ETags, and tests.
- Canonical OpenAPI, JSON Schema, and clearly marked synthetic fixtures.
- No database, live job creation, provider request, or Earth Engine credential use in request handlers.

### Existing frontend

`orbital-website/` is browser/client code that provides a local Three.js Earth, satellite targeting, offline gazetteer search, responsive HUD behaviour, and reduced-motion handling. It makes no API request and renders no SPARC indicator, period, quality, provenance, or layer data.

## Analytical frontend still required for P0

| Priority | Missing browser capability | Existing starting point | Definition of done |
|---|---|---|---|
| P0 | Application shell and route/state model | No `apps/web/` application exists | A user can enter the SPARC analytical journey without interacting with a 3D scene |
| P0 | DemoTransport and ApiTransport | Contract fixtures and FastAPI endpoints exist; Orbital performs no `fetch()` | Both transports yield one validated view model for the same supported request |
| P0 | Constrained region, period, and indicator controls | Orbital accepts arbitrary global places | UI exposes Nagpur/Bengaluru and frozen P0 windows; browser checks are repeated by the server |
| P0 | District summary and three indicator cards | No analytical cards | Shows proxy label, unit, baseline, comparison, change, coverage, status, and caveat without inventing accuracy |
| P0 | Indicator detail view | No result renderer | Shows water, vegetation, and built-proxy interpretation, sensitivity/quality evidence, and `Unavailable` states rather than zeroes |
| P0 | Spatial layer or accessible static alternative | Globe textures are decorative, not analytical layers | Layer can be inspected with a non-WebGL table/image fallback; attribution and bounds remain visible |
| P0 | Quality, provenance, and limitation panel | No SPARC disclosure panel | Data mode, `mock`/pre-publication state, common-valid coverage, method, sources, attribution, warnings, and boundary disclaimer are visible |
| P0 | Loading, invalid-input, partial, missing-layer, API-down, and offline states | Only targeting-query errors exist | Each contract/client failure state has visible, keyboard-accessible recovery behaviour |
| P0 | Responsive and accessibility verification | Orbital has limited mobile/reduced-motion support | Keyboard-only, 360 px, 200% zoom, reduced motion, no-WebGL, and non-colour tests pass for the analytical journey |
| P0 | Actual approved child-region drill-down | Hingna remains unapproved | Ship only after a separate child-boundary and data gate passes; otherwise display district-only scope honestly |
| P1, not P0 | Time series, LST/SUHI, live processing controls, 3D data overlays | None | Keep out of the core demo until P0 is stable |

The existing Three.js experience may remain as an optional launch/selection visual only after the dashboard has a complete non-WebGL analytical path. It must not become the sole way to select or understand data.

## Remaining data and release gates

1. Obtain temporally appropriate independent reference labels for the vegetation sample frame, calculate known inclusion probabilities and stratum populations, and run the planned accuracy analysis. The current frame is exploratory only.
2. Run and import water and built-candidate sensitivity analyses; investigate any material instability.
3. Complete a provenance-complete Bengaluru Urban pack for the three P0 indicators, not water alone.
4. Resolve or remove the Nagpur child-region requirement. No unverified Hingna geometry may enter the demo.
5. Convert accepted immutable result reports into contract-valid demo artifacts, layers/static alternatives, manifests, checksums, and attribution records. The current local pre-publication pack is a safe input boundary, not a response to serve. Do not serve ignored working reports or claim pre-publication evidence is final.
6. Implement and test the analytical frontend against mocks first, then the immutable pack/API.
7. Run the integrated offline, accessibility, security, and presentation gates.

## Current next task

The pre-publication result-pack boundary is implemented and the local Nagpur pack has been built. The next unblocked delivery task is **water and built-candidate sensitivity design and processing**. It must use documented alternative thresholds or methods, retain the same scenes, masks, CRS, and common-valid footprint, and remain `quality: unknown` unless the evidence supports a stronger conclusion.

The API must remain mock-only while this work is underway. Do not remove mock labels, introduce a `live` route, or publish the vegetation result as a confirmed environmental finding. The analytical dashboard may begin against synthetic fixtures, but it must visibly distinguish mock and pre-publication evidence before it is connected to a result pack.
