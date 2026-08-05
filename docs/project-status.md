# SPARC delivery status

**Assessed:** 2026-08-05
**Current stage:** Stage 4 of 5 — the analytical dashboard, three validated precomputed packs (Nagpur, Bengaluru Urban, and Mumbai City), jurisdiction-agnostic reporting API, global city catalog, and report-package workflow are implemented; approved layers, Claude UI polish, registry-driven authority selection, acknowledgement UI, and final release gates remain open. Formal scientific validation is deferred for the hackathon track.

This is an evidence-based delivery status, not a percentage derived from line count. A completed visual component does not substitute for a validated data result, and a completed data export does not substitute for a usable dashboard.

## Current position

| Stage | Status | Evidence | Exit condition |
|---|---|---|---|
| 1. Contract and safe offline API | Substantially complete | OpenAPI/schema tests pass; FastAPI serves only allowlisted bounded fixtures with safe errors | Stable immutable artifacts can be served through the same contract without weakening safety |
| 2. Boundary and P0 evidence | Sufficient for hackathon presentation with explicit limits | geoBoundaries Nagpur, Bengaluru Urban, and Mumbai City district gates passed. Earth Engine produced imported sensitivity evidence for the P0 indicators. Water can be presented as an estimated surface-water change; the contradictory Nagpur built-up result remains unavailable. Formal independent validation is intentionally deferred. | Method conflicts remain withheld, provenance/limitations are visible, and no unsupported legal or causal claim is made |
| 3. Result packaging and API integration | In progress | Schema-checked, non-overwritable local Nagpur, Bengaluru Urban, and Mumbai City precomputed packs map through the API and generated static contract examples; final review/commit of the pack assets and release layers remains | Stable, contract-valid, attributable precomputed outputs for all three districts; no request-time raster work |
| 4. Analytical dashboard | Substantially complete; integration remains | `apps/web/` provides the location → period → summary → indicator journey, neutral estimate terminology, reporting workflow shell, disclosures, non-WebGL path, and API/offline transports | Same journey renders stable Nagpur, Bengaluru, and Mumbai City outputs, with the reporting wizard and approved layer/static assets |
| 5. Offline release and rehearsal | Started | The built bundle is served at `/app/` by `apps/web/serve.mjs`; demo, API recovery, viewport, keyboard, and static-server checks pass | Primary and backup journeys work from a frozen local HTTP release with offline, accessibility, security, and evidence checks |

### Supported-city catalog status

The quick-target picker now contains Nagpur, Bengaluru, Mumbai, Delhi, Chennai,
Bhopal, New York, Washington DC, Tokyo, London, Cairo, Sydney, Rio de Janeiro,
and Reykjavik
with ISO country codes, administrative areas, explicit boundary definitions,
coverage states, processing-pack/checksum metadata, and jurisdiction-pack
references. The catalog source is [`docs/city-catalog.md`](city-catalog.md) and
the machine-readable record is [`data/catalog/supported-cities.json`](../data/catalog/supported-cities.json).
The pinned expansion boundary registry is [`data/catalog/city-boundary-coverage.json`](../data/catalog/city-boundary-coverage.json)
with separate raw-source metadata, validated GeoJSON, gate manifests, and
checksums under `data/{raw,validated,metadata}/boundaries`.

Nagpur, Bengaluru Urban, and Mumbai City pass the boundary/pack/contract gates
and are the published satellite-analysis journeys. The other cities intentionally open a
report/export scope until Earth Engine packs are accepted. Their expansion
boundaries are now pinned and gate-validated, but their fallback response has
null metrics and `NOT_RUN` quality; it does not fabricate analytical values or
imply a published Earth Engine result. Routing coverage is independent of
analytical coverage: the verified U.S. EPA and England routes may be opened for
New York, Washington DC, and London, while report-generation-only or unsupported
routing states remain export-only. Unsupported countries retain local export
and do not receive guessed handoff links.

### Reporting feature status (P0 contract/server slice)

The offline-first “Report Environmental Concern” server slice is implemented as a bounded P0 contract path. It has versioned jurisdiction packs, universal issue/location fields, coverage states, submission-adapter interfaces, strict claim-safe evidence gating, deterministic PDF/ZIP artifacts, canonical manifests and SHA-256 checksums, bounded photo validation, 24-hour private temporary report workspaces, manual portal handoff, and user-entered acknowledgement tracking. The browser workflow now collects report details, optionally drafts neutral narrative text with Gemini using explicit consent, appends sensitive details locally, leaves a blank printable signature line, and downloads the generated report PDF/evidence package. The PDF is generated by SPARC; the upload control accepts photos only.

This does not mean reporting is production-ready. Authentication, durable encrypted storage, background expiry jobs, RBAC, accepted result-pack integration, and the Claude-owned wizard/accessibility implementation remain P1/shared work. No government credentials, CAPTCHA/OTP, portal automation, or allegation of illegality is supported.

## Delivery estimate

The following is a planning estimate for an honest P0 hackathon candidate, not a scientific quality score.

| Workstream | Approximate readiness | Why it is not further along |
|---|---:|---|
| Boundary and processing foundation | 82% | Three accepted district packs exist, and twelve expansion city polygons are now pinned and gate-validated. Earth Engine processing and pack review for the expansion registry remain; the Nagpur built-proxy reversal remains withheld |
| Contract and API | 70% | Reporting and analytical contracts plus the immutable precomputed-pack adapter are tested; deployment packaging and artifact/layer review remain |
| Analytical frontend | 84% | The dashboard now consumes generated Nagpur/Bengaluru/Mumbai City contract examples, uses district-specific periods, and preserves the neutral wording; approved layer assets and Claude reporting integration remain |
| Integration, offline bundle, and release verification | 40% | The static `/app/` bundle and API/offline paths build successfully, but the final local release, layer assets, handoff flow, and cold-start rehearsal remain |
| **Overall P0 hackathon candidate** | **about 65–70%** | Stable Nagpur/Bengaluru/Mumbai City result integration is now present; approved layers, reporting integration, and release evidence remain the dominant work |

Roughly **30–35% remains** before an honest hackathon P0 candidate. Formal validation is not on the critical hackathon path; unsupported claims, the contradictory built-up result, reporting handoff, approved layers, offline rehearsal, and presentation quality remain the practical gates.

## What exists today

### Processing and evidence

- Validated prototype district AOIs: Nagpur, Bengaluru Urban, and Mumbai City from geoBoundaries India ADM2, with source-specific ODbL handling and the non-authoritative-boundary disclaimer.
- Precomputed Sentinel-2 P0 summaries: Nagpur water, vegetation, and an unavailable built-up candidate; Bengaluru Urban and Mumbai City water, vegetation, and built candidates.
- The API and browser view-model both suppress Nagpur built-up metrics; direct indicator requests return an explicit `unavailable` state with the method-conflict reason.
- Vegetation threshold sensitivity at NDVI 0.20, 0.30, and 0.40. Its net green-cover proxy change ranges from −27.03 km² to −487.10 km², so the default result remains `quality: unknown`.
- Water pooled-Otsu sensitivity: fixed-zero and pooled-Otsu outputs both show net loss (−8.50 and −10.16 km²), but this is not independent validation.
- Built-proxy IBI v2 sensitivity: the constrained-NDBI default shows +158.47 km² while IBI shows −361.52 km². This material reversal blocks any built-change finding; the Nagpur built-up output remains unavailable.
- Bengaluru Urban sensitivity evidence is complete but is not validation: water is positive under the fixed-zero (+9.22 km²) and pooled-Otsu (+96.17 km²) rules; vegetation is positive at NDVI 0.20/0.30/0.40 (+30.51/+58.03/+51.76 km²); and the constrained-NDBI/IBI built diagnostics are both negative (−79.18/−5.08 km²). The magnitude differences remain material and every result remains `quality: unknown` until independent reference validation.
- A blinded, 100-point exploratory Nagpur vegetation label frame and controlled label template. It contains no independent labels and is not a validation result.
- Two separate blinded, 100-point exploratory built-up frames with checksum metadata: constrained-NDBI default (`04d61db1…e58686a7`) and IBI v2 (`a3f3e6a3…5b33958`). Their template gate verifies the declared rule but not environmental accuracy. They have no independent labels and do not resolve the built-method blocker.
- Local Nagpur precomputed packs: v1 records the earlier evidence boundary; v2 is schema-checked and preserves water, vegetation, and built sensitivity records. The latest Bengaluru Urban and Mumbai City v2 packs are schema-checked and preserve all three reports plus sensitivity records. The API adapter generates contract examples with a SHA-256 manifest, and the runtime API serves those static artifacts in `SPARC_DATA_MODE=precomputed`; the source packs remain ignored processing inputs.

### Server and contract

- A FastAPI read-only API with input limits, allowlisted identifiers, explicit CORS, safe RFC 9457-style errors, ETags, and tests.
- Canonical OpenAPI, JSON Schema, and precomputed contract fixtures with provenance and limitations.
- No database, live job creation, provider request, or Earth Engine credential use in request handlers.

### Analytical dashboard

`apps/web/` is browser/client code. It runs a React/Vite dashboard over bounded offline analysis inputs by default, validates responses against the canonical JSON Schema, and has a separate `ApiTransport` for the FastAPI service. In API mode, the picker now lists both mapped districts and selects their district-specific frozen periods. The default offline path still needs packaged copies of the accepted pack responses.

```text
User chooses a stable district output (or an accepted future district pack)
→ user chooses the frozen same-season period pair when more than one exists
→ browser repository selects DemoTransport or ApiTransport
→ transport validates the contract-shaped response
→ view-model mapper applies unavailable/quality/provenance rules
→ summary or indicator detail renders
→ an API failure can switch the browser back to the offline analysis package
```

The dashboard's non-WebGL path is the default. `orbital-website/` remains a separate browser/client launch visual; under the combined static server it can open the dashboard panel and display a district overlay, but no analytical result depends on a 3D canvas. The overlay must not imply a raster, a cadastral boundary, or real data for a generated fixture.

## Frontend work remaining for P0

| Priority | Remaining browser work | Why it remains |
|---|---|---|
| P0 | Review and commit the generated Nagpur/Bengaluru/Mumbai City artifacts for the offline browser path | `contracts/examples/precomputed/` now supplies all three districts to `DemoTransport`; approved layer/static assets and release review remain |
| P0 | Review the Bengaluru Urban journey and add approved layer/static alternatives | The three-indicator journey is mapped; release still needs layer assets and the same evidence review as Nagpur |
| P0 | Supply approved local layers/static alternatives for accepted results | Current fixture layer descriptors exercise disclosure and failure handling, but do not represent approved published evidence assets |
| P0 | Test the full Orbit-to-panel handoff and manual screen-reader/reduced-motion behavior | The standalone dashboard's keyboard, 360 px, 200% zoom, and non-colour path are automated; the cross-page 3D enhancement and assistive-technology review still need release evidence |
| P0 | Claude polish and registry-driven browser reporting | Codex integration creates the report package and opens the server-returned handoff URL; Claude still needs reviewed `EvidenceQualityGate`, accessibility/focus handling, translations, registry-driven authority choices, and acknowledgement UI |
| P0 | Actual approved child-region drill-down | Hingna remains unapproved; the interface correctly states district-only scope until a separate boundary/data gate passes |
| P1, not P0 | Time series, LST/SUHI, live processing controls, and 3D data overlays | Keep these out of the core demo until real P0 results and release gates are stable |

The primary dashboard uses concise estimate terminology. Source dataset, acquisition periods, method version, thresholds, boundary provenance, processing date, quality status, and limitations remain available in methodology/provenance views. The contradictory Nagpur built-up result must remain unavailable.

## Remaining data and release gates

1. Review and commit the generated contract examples and manifest for the offline browser bundle.
2. Keep the contradictory Nagpur built-up result unavailable; expose the water output only as an estimated surface-water change and keep reporting language neutral.
3. Add the Bengaluru backup journey and approved layer/static alternatives.
4. Have Claude polish the integrated wizard, consume the jurisdiction registry, add acknowledgement tracking, and complete accessibility/localization tests.
5. Run integrated offline, security, accessibility, presentation, and Q&A rehearsal gates.
6. Formal preregistration, blinded sampling, independent labels, and publication-level accuracy metrics are deferred and must not block the hackathon release track.

### 2026-08-05 expansion run

The twelve requested expansion city boundaries are now source-pinned and
gate-validated. Earth Engine batch requests for Mumbai, Delhi, Chennai, Bhopal,
New York, Washington DC, Tokyo, London, Cairo, Sydney, Rio de Janeiro, and
Reykjavík were prepared with the configured `orbitwatch-503717` project. No
Drive export was started and no result CSV or contract pack was imported. The
project returned the noncommercial compute-quota restricted-mode warning, so
the next data action requires the project owner to confirm quota and an
approved Drive destination. The run manifest and request checksums are in
[`data/metadata/earth-engine-p0-expansion-run.json`](../data/metadata/earth-engine-p0-expansion-run.json).

## Current next task

The dashboard is ready for the hackathon integration track and has passed 40 current browser checks, including blocked-API recovery. The combined local server serves the supplied Orbit handoff link at `http://localhost:8123/app/#/locate?lat=19.0760&lon=72.8777`, after replacing the globe-only server that returned `404 app/`. Nagpur, Bengaluru Urban, and Mumbai City precomputed packs contain the current Earth Engine outputs and sensitivity records. Water may be presented as an estimated surface-water change. The contradictory Nagpur built-up methods reverse direction and remain unavailable; Mumbai City’s built-up methods agree in direction and its estimate is available with quality status unknown. Formal preregistration, blinded sampling, independent labels, and publication-level accuracy metrics are explicitly deferred for the hackathon track.

The API remains bounded to precomputed/offline results while this work is underway. Do not introduce request-time raster processing or publish unsupported legal, causal, pollution, deforestation, or encroachment findings. The generated responses are bound to the reviewed pack and boundary checksums; release still requires the asset review below.

The next task is release integration: review/commit the generated pack assets, add approved static layers, finish the reporting components (`EvidenceQualityGate`, `ComplaintWizard`, `OfficialPortalHandoff`, and `SubmissionTracker`), verify artifact downloads and manual handoff for all three validated districts plus report-only cities, then rehearse the offline presentation. The city-picker contract and fallback behavior are documented in [`docs/reporting/frontend-migration-note.md`](reporting/frontend-migration-note.md).
