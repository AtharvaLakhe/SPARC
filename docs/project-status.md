# SPARC delivery status

**Assessed:** 2026-08-04
**Current stage:** Stage 4 of 5 — the mock-backed analytical dashboard is implemented and browser-verified; real-data and release gates remain open

This is an evidence-based delivery status, not a percentage derived from line count. A completed visual component does not substitute for a validated data result, and a completed data export does not substitute for a usable dashboard.

## Current position

| Stage | Status | Evidence | Exit condition |
|---|---|---|---|
| 1. Contract and safe mock API | Substantially complete | OpenAPI/schema tests pass; FastAPI serves only allowlisted synthetic fixtures with safe errors | Real immutable artifacts can be served through the same contract without weakening validation |
| 2. Boundary and P0 evidence | In progress | geoBoundaries Nagpur and Bengaluru Urban district gates passed. All three Nagpur P0 indicators have imported sensitivity evidence, which confirms substantial threshold/method uncertainty: water retains a net-loss direction while built proxy reverses direction. Bengaluru has all three imported reports and all documented P0 sensitivity records, but no independent validation. The weighted v1 Nagpur vegetation population export is rejected; corrected unweighted v2 is imported and records finite strata. The preregistration gate is implemented and correctly refuses the still-undecided allocation | Independent reference validation and a resolution/withholding decision exist for every public P0 result |
| 3. Result packaging and API integration | In progress | Schema-checked, non-overwritable local Nagpur and Bengaluru Urban pre-publication packs now exist; the API intentionally reads only synthetic fixtures | Contract-valid, immutable, attributable demo pack for Nagpur and Bengaluru Urban; no request-time raster work |
| 4. Analytical dashboard | Substantially complete against synthetic fixtures | `apps/web/` provides the location → period → summary → indicator journey, synthetic city picker, optional globe overlay, DemoTransport, ApiTransport, disclosures, non-WebGL path, and API-to-demo recovery | Same journey renders accepted immutable packs for Nagpur and Bengaluru Urban, with approved layer assets and no unreviewed claims |
| 5. Offline release and rehearsal | Started | The built bundle is served at `/app/` by `apps/web/serve.mjs`; demo, API recovery, viewport, keyboard, and static-server checks pass | Primary and backup journeys work from a frozen local HTTP release with offline, accessibility, security, and evidence checks |

## Delivery estimate

The following is a planning estimate for an honest P0 demo candidate, not a scientific quality score.

| Workstream | Approximate readiness | Why it is not further along |
|---|---:|---|
| Boundary and processing foundation | 70% | District geometry, representative P0 runs, all documented sensitivity records for both districts, and a three-indicator Bengaluru evidence pack now exist. The material Nagpur built-proxy reversal remains an explicit blocker; independent reference labels, formal accuracy analysis, and approved child geometry remain |
| Contract and API | 45% | The contract and read-only mock API are tested and the offline pre-publication pack boundary exists, but real immutable result-pack loading and data-mode handling do not exist |
| Analytical frontend | 70% | The mock-backed dashboard and failure recovery are browser-verified; it does not yet render accepted real/pre-publication packs, a Bengaluru journey, or approved local layer assets |
| Integration, offline bundle, and release verification | 30% | The static `/app/` bundle and API-to-demo recovery have passed browser checks, but the final local release, real data mapping, backup journey, and cold-start rehearsal remain |
| **Overall P0 demo candidate** | **about 45–50%** | The browser layer is materially further along, but data validation, result integration, backup coverage, and release evidence remain the dominant work |

Roughly **50–55% remains** before an honest P0 demo candidate. A public or production claim is further away because vegetation is threshold-sensitive, the two built-proxy methods reverse direction, and no indicator has formal independent validation.

## What exists today

### Processing and evidence

- Validated prototype district AOIs: Nagpur and Bengaluru Urban from geoBoundaries India ADM2, with source-specific ODbL handling and the non-authoritative-boundary disclaimer.
- Pre-publication Sentinel-2 P0 summaries: Nagpur water, vegetation, built candidate; Bengaluru Urban water, vegetation, and built candidate.
- Vegetation threshold sensitivity at NDVI 0.20, 0.30, and 0.40. Its net green-cover proxy change ranges from −27.03 km² to −487.10 km², so the default result remains `quality: unknown`.
- Water pooled-Otsu sensitivity: fixed-zero and pooled-Otsu outputs both show net loss (−8.50 and −10.16 km²), but this is not independent validation.
- Built-proxy IBI v2 sensitivity: the constrained-NDBI default shows +158.47 km² while IBI shows −361.52 km². This material reversal blocks any built-change finding; keep it only as an unstable pre-publication diagnostic.
- Bengaluru Urban sensitivity evidence is complete but is not validation: water is positive under the fixed-zero (+9.22 km²) and pooled-Otsu (+96.17 km²) rules; vegetation is positive at NDVI 0.20/0.30/0.40 (+30.51/+58.03/+51.76 km²); and the constrained-NDBI/IBI built diagnostics are both negative (−79.18/−5.08 km²). The magnitude differences remain material and every result remains `quality: unknown` until independent reference validation.
- A blinded, 100-point exploratory Nagpur vegetation label frame and controlled label template. It contains no independent labels and is not a validation result.
- Two separate blinded, 100-point exploratory built-up frames with checksum metadata: constrained-NDBI default (`04d61db1…e58686a7`) and IBI v2 (`a3f3e6a3…5b33958`). Their template gate verifies the declared rule but not environmental accuracy. They have no independent labels and do not resolve the built-method blocker.
- Ignored local Nagpur pre-publication packs: v1 records the earlier evidence boundary; v2 is schema-checked and preserves water, vegetation, and built sensitivity records. The latest Bengaluru Urban v2 pack is schema-checked and preserves all three reports plus water, vegetation, and built sensitivity records. None is an API response or deployable result.

### Server and contract

- A FastAPI read-only API with input limits, allowlisted identifiers, explicit CORS, safe RFC 9457-style errors, ETags, and tests.
- Canonical OpenAPI, JSON Schema, and clearly marked synthetic fixtures.
- No database, live job creation, provider request, or Earth Engine credential use in request handlers.

### Analytical dashboard

`apps/web/` is browser/client code. It runs a React/Vite dashboard over committed synthetic fixtures by default, validates responses against the canonical JSON Schema, and has a separate `ApiTransport` for the FastAPI mock service. The city picker and globe overlay added on 2026-08-04 are presentation features only: DemoTransport may expose generated city fixtures, but each has `meta.mock: true`; ApiTransport does not expose those generated cities. The bundled Nagpur fixture is also synthetic. Local Nagpur/Bengaluru pre-publication packs are not browser inputs.

```text
User chooses a bundled synthetic fixture (or an accepted future district pack)
→ user chooses the frozen same-season period pair when more than one exists
→ browser repository selects DemoTransport or ApiTransport
→ transport validates the contract-shaped response
→ view-model mapper applies unavailable/quality/provenance rules
→ summary or indicator detail renders
→ an API failure can switch the browser back to the offline demo pack
```

The dashboard's non-WebGL path is the default. `orbital-website/` remains a separate browser/client launch visual; under the combined static server it can open the dashboard panel and display a district overlay, but no analytical result depends on a 3D canvas. The overlay must not imply a raster, a cadastral boundary, or real data for a generated fixture.

## Frontend work remaining for P0

| Priority | Remaining browser work | Why it remains |
|---|---|---|
| P0 | Connect accepted immutable pack artifacts through a separately reviewed mapping | The current UI intentionally reads only clearly labelled synthetic fixtures; the local Nagpur pre-publication pack is not an HTTP response or public result |
| P0 | Add the Bengaluru Urban journey after its remaining sensitivity, validation, and reviewed mapping gates pass | A three-indicator pre-publication pack now exists, but the browser must not advertise an evidence-only, incompletely validated backup journey as an accepted result |
| P0 | Supply approved local layers/static alternatives for accepted results | Current fixture layer descriptors exercise disclosure and failure handling, but do not represent approved published evidence assets |
| P0 | Test the full Orbit-to-panel handoff and manual screen-reader/reduced-motion behavior | The standalone dashboard's keyboard, 360 px, 200% zoom, and non-colour path are automated; the cross-page 3D enhancement and assistive-technology review still need release evidence |
| P0 | Actual approved child-region drill-down | Hingna remains unapproved; the interface correctly states district-only scope until a separate boundary/data gate passes |
| P1, not P0 | Time series, LST/SUHI, live processing controls, and 3D data overlays | Keep these out of the core demo until real P0 results and release gates are stable |

The current dashboard is deliberately mock-labelled. It must not be switched to a pre-publication pack by changing a browser flag or by loosening the FastAPI demo-only restriction.

## Remaining data and release gates

1. Complete and validate the Nagpur vegetation probability plan with the new preregistration validator. Version 1 remains rejected because its weighted histogram gave fractional counts. The ledger establishes finite populations only; it must stay separate from initial label reviewers and does not alter any quality status.
2. Pre-register allocation, replacement policy, seed, and inclusion probability from that ledger; then create a **new** blinded probability frame. The existing 25-per-stratum Nagpur frames remain exploratory and cannot be promoted.
3. Obtain temporally appropriate independent reference labels, compute the design-based accuracy/area analysis, and make a retain-or-withhold decision. The Nagpur built-change result remains blocked because constrained-NDBI and IBI v2 reverse direction. The earlier IBI v1 CSV is excluded because it did not record the required denominator-validity footprint.
4. Create a separate Bengaluru Urban probability design and independent reference-labelling plan before treating its directionally consistent sensitivity evidence as more than a pre-publication diagnostic. Its evidence-only pack has no applicable label frame.
5. Resolve or remove the Nagpur child-region requirement. No unverified Hingna geometry may enter the demo.
6. Convert accepted immutable result reports into contract-valid demo artifacts, layers/static alternatives, manifests, checksums, and attribution records. The current local pre-publication pack is a safe input boundary, not a response to serve. Do not serve ignored working reports or claim pre-publication evidence is final.
7. Map accepted immutable packs to the frozen response contract, then test the existing dashboard against them without weakening the mock/pre-publication disclosure.
8. Add the Bengaluru backup journey, approved local layer assets, the Orbit-to-panel test, and manual accessibility evidence; then run the integrated offline, security, and presentation gates.

## Current next task

The dashboard is ready for synthetic-fixture use and has passed 40 current browser checks, including blocked-API recovery. The combined local server serves the supplied Orbit handoff link at `http://localhost:8123/app/#/locate?lat=19.0760&lon=72.8777`, after replacing the globe-only server that returned `404 app/`. The current city picker/browser additions are synthetic-interface work, not a real-time or national-data release; the browser suite checks that the bundled Nagpur card is explicitly a mock fixture. The Nagpur vegetation finite-population ledger is now imported, but no probability allocation or independent label exists. All three Nagpur sensitivities are in the schema-checked v2 pre-publication pack. The latest Bengaluru v2 evidence pack now contains all three P0 reports and all three documented sensitivity records; it deliberately records no label frame and no independent validation. Nagpur water retains a net-loss direction while its built default and IBI v2 result reverse direction; the latter is a **method blocker**, not a numerical detail. Separate 100-point exploratory frames now exist for each Nagpur built rule. The next unblocked task is to preregister a probability design, create a fresh blinded sample, and obtain independent labels. The input scenes, SCL mask, AOI, CRS and observation floor remain fixed; the IBI diagnostic separately reports zero-denominator exclusion. All results remain `quality: unknown` unless independent evidence supports a stronger conclusion.

The API must remain mock-only while this work is underway. Do not remove mock labels, introduce a `live` route, or publish the vegetation result as a confirmed environmental finding. A reviewed server-side mapping is required before the dashboard receives any pre-publication pack.
