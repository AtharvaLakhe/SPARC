# Frontend implementation handoff

**Owner:** Claude  
**Reviewers:** Codex for contract/server assumptions; shared review for scientific wording  
**Status:** Planned implementation; no frontend runtime is created by this document

This handoff is the browser workstream's implementation boundary. It is deliberately contract-first: the React application can be built against committed synthetic examples before FastAPI exists, then switch transports without changing presentation components.

## 1. What exists and what is planned

At this planning checkpoint, the repository contains contracts, examples and documentation, not an implemented web application. Paths below marked “planned” must not be described as current code.

| Classification | Artifact | Runs where | Purpose |
|---|---|---|---|
| Shared contract | [`contracts/openapi.yaml`](../contracts/openapi.yaml) | Validation/build input | Defines HTTP operations, parameters, status codes and operation-specific schemas |
| Shared contract | [`packages/contracts/schemas/sparc.schema.json`](../packages/contracts/schemas/sparc.schema.json) | Validation/build input and optionally a browser boundary validator | Canonical JSON Schema 2020-12 response/request shapes |
| Shared fixtures | [`contracts/examples/`](../contracts/examples/README.md) | Development/test input | Synthetic interface examples; they are not environmental results |
| Browser/client, planned | `apps/web/**` | Browser after Vite build | React UI, browser-side input checks, data gateway, view-model mapping and accessibility |
| Build/configuration, planned | `apps/web/vite.config.*`, TypeScript configuration | Developer machine/CI | Bundles browser code and injects public `VITE_*` values |
| Server/backend, planned | `apps/api/**` | FastAPI process | Performs authoritative request validation and serves immutable results |
| Database code | none in P0 | nowhere | P0 uses immutable files/manifests; no browser or server database dependency is planned |
| External API code, planned | provider adapter under the Codex lane | Server/data-processing process only | Optional catalog/acquisition; never called directly by the browser |

The browser is untrusted. Client validation improves feedback but does not authorize a region, period, layer or processing job. FastAPI must repeat all security and domain validation for live requests.

## 2. Canonical inputs and precedence

When two artifacts appear inconsistent, stop and escalate; do not guess. Use this precedence:

1. OpenAPI is authoritative for method, URL, headers, request body and status behavior.
2. JSON Schema is authoritative for reusable data shape, nullability, enums and required properties.
3. Mock files demonstrate supported UI states but cannot loosen the schema.
4. [Indicator methodology](./indicator-methodology.md) controls scientific names, units and caveats.
5. This handoff controls frontend composition and state behavior only.

The Day 0 contract revision is frozen. Generated or validated TypeScript types must identify the source revision and tool version; never edit generated output by hand or copy a handwritten interface into multiple components.

## 3. Planned frontend boundaries

Use a small feature-oriented structure under the future `apps/web/src/`. Exact filenames may follow the established scaffold once it exists, but responsibilities must remain separated.

| Planned responsibility | Classification | Receives | Produces/calls | Removal impact |
|---|---|---|---|---|
| Application bootstrap and routes | Browser/client | Vite entry, public config | Top-level error boundary and screens | No browser application starts |
| `config` reader | Browser/client | `import.meta.env` public values | Validated data-mode/base-URL configuration | Mode selection becomes implicit and unsafe |
| Contract types/validators | Shared/generated or build output | Frozen contract | Typed boundary checks for transports | Drift or malformed payloads can reach UI |
| Data gateway/repository | Browser/client | Canonical requests | Chosen transport and typed results | Components become coupled to URLs/files |
| `ApiTransport` | Browser/client | Canonical request, public API base URL, abort signal | HTTP `/api/v1` operations | Live/cache mode is unavailable |
| `DemoTransport` | Browser/client | Canonical request key, local manifest | Contract-shaped local responses | Offline/demo mode is unavailable |
| View-model mapper | Browser/client | Validated response | Presentation-safe metrics, labels and state | Components duplicate null/quality/mode logic |
| Feature screens/components | Browser/client | View models and callbacks | Accessible HTML, map/chart/table shells | The user journey is unavailable |
| Map/layer adapter | Browser/client | Validated allowlisted layer descriptor | MapLibre or static image/table fallback | Spatial view is unavailable, but metrics must remain |
| Optional 3D boundary | Browser/client, lazy P1 | User-approved asset descriptor | Isolated scene or neutral placeholder | Core analysis must remain unchanged |

Presentation components must not import JSON fixtures directly, assemble API URLs, read provider tokens, interpret arbitrary `href` values, or decide whether a scientific result is valid.

## 4. Planned repository operations

The UI should call one typed repository facade. These are responsibility names, not existing function claims:

| Planned operation | P0/P1 | Live HTTP source | Demo source | Result shape |
|---|---:|---|---|---|
| `listRegions(filters)` | P0 | `GET /api/v1/regions` | manifest region index | array of `RegionRef` in the standard envelope |
| `getRegion(regionId)` | P0 | `GET /api/v1/regions/{regionId}` | region record | `RegionRef` envelope |
| `getRegionSummary(selection)` | P0 | `GET /api/v1/regions/{regionId}/summary` with four required date queries | canonical request-key lookup | `DistrictSummaryResponse` |
| `listRegionIndicators(selection, indicatorId?)` | P0 | `GET /api/v1/regions/{regionId}/indicators` with four required date queries | summary-list lookup | array of `IndicatorSummary` in the standard envelope |
| `getIndicatorComparison(selection, indicatorId)` | P0 | `GET /api/v1/regions/{regionId}/indicators/{indicatorId}` with four required date queries | indicator fixture/artifact lookup | `IndicatorComparisonResponse` |
| `resolveComparison(request)` | P0 | `POST /api/v1/comparisons` | canonical request-key lookup | `DistrictSummaryResponse` on `200`; future `JobResponse` on `202` |
| `getComparison(comparisonId)` | P0 | `GET /api/v1/comparisons/{comparisonId}` | immutable comparison lookup | `DistrictSummaryResponse` |
| `getLayer(layerId)` | P0 | `GET /api/v1/layers/{layerId}` | local descriptor lookup | `LayerResponse` |
| `listDatasetMetadata()` | P0 | `GET /api/v1/metadata/datasets` | packaged metadata | array of `DatasetSource` in the standard envelope |
| `listIndicatorMetadata()` | P0 | `GET /api/v1/metadata/indicators` | packaged metadata | array of `IndicatorRef` in the standard envelope |
| `getTimeSeries(request)` | P1 | `GET /api/v1/regions/{regionId}/timeseries` | time-series fixture/artifact | `TimeSeriesResponse` |
| `getLayerTileJson(layerId)` | P1 | `GET /api/v1/layers/{layerId}/tilejson.json` | packaged TileJSON when approved | restricted application-controlled TileJSON |
| `getJob(jobId)` | P1 | `GET /api/v1/processing/jobs/{jobId}` | no P0 polling | `JobResponse` |

Do not expose the restricted `POST /api/v1/processing/jobs` in the public P0 browser. It requires future administrative authentication and is disabled for the primary scope.

### Comparison input

The canonical `ComparisonRequest` contains:

- `regionId`: required opaque string; select only from returned/packaged regions;
- `baselinePeriod`: required `startDate` and `endDate` in `YYYY-MM-DD`;
- `comparisonPeriod`: required `startDate` and `endDate` in `YYYY-MM-DD`;
- `indicatorIds`: one to five unique values from the contract enum: `surface-water`, `vegetation`, `built-up`, `lst`, or `suhi`; the P0 UI exposes only the first three, while heat indicators remain P1.
- `modePreference`: required `auto`, `demo`, or `live`; it requests a mode but does not override server capability, authorization, integrity checks or visible mode disclosure.

The browser checks completeness, allowed visible choices and date ordering for immediate feedback. The server remains authoritative for ID existence, supported windows, authorization and live-processing limits.

For the primary P0 demo, use 2019-10-15 through 2019-12-15 and 2024-10-15 through 2024-12-15. The optional LST example uses 2019-03-01 through 2019-05-15 and 2024-03-01 through 2024-05-15; do not mix those seasonal windows into one comparison.

## 5. Exact fixture consumption

All files below are synthetic and must show a visible mock/demo label derived from metadata or the test harness.

| Fixture | Canonical schema | Frontend state/purpose | Required assertions |
|---|---|---|---|
| [`district-summary.mock.json`](../contracts/examples/district-summary.mock.json) | `DistrictSummaryResponse` | Dashboard summary, P0 happy path | Three P0 cards; dates/units preserved; `meta.mock=true` visible |
| [`water-comparison.mock.json`](../contracts/examples/water-comparison.mock.json) | `IndicatorComparisonResponse` | Water detail | Quality, MNDWI-derived proxy wording, image layer, interpretation and attribution shown |
| [`vegetation-comparison.mock.json`](../contracts/examples/vegetation-comparison.mock.json) | `IndicatorComparisonResponse` | Vegetation detail | NDVI unit retained; caveats not converted into a causal claim |
| [`built-up-comparison.mock.json`](../contracts/examples/built-up-comparison.mock.json) | `IndicatorComparisonResponse` | Built-up detail | Low quality remains visible; GeoJSON layer representation is handled |
| [`partial-data.mock.json`](../contracts/examples/partial-data.mock.json) | `IndicatorComparisonResponse` | Usable partial/unavailable comparison | Nulls are “Unavailable,” not `0`; reason/warnings shown; no layer assumed |
| [`block-results.mock.json`](../contracts/examples/block-results.mock.json) | `BlockResultsResponse` | Generic subdistrict table design only | The current OpenAPI does not bind this schema to an operation, so do not invent a production URL for it. Fixture names such as Hingna/Kamptee are synthetic interface labels only; the P0 subdistrict remains subject to boundary/license/data QA |
| [`layer-descriptor.mock.json`](../contracts/examples/layer-descriptor.mock.json) | `LayerResponse` | Layer adapter test | Relative URL only; legend and attribution remain visible; referenced file is intentionally absent in planning |
| [`api-error.mock.json`](../contracts/examples/api-error.mock.json) | `ProblemDetails` | `422` domain-validation state | User-safe detail plus field issue; `traceId` available for support, not exposed as a secret |
| [`lst-comparison.mock.json`](../contracts/examples/lst-comparison.mock.json) | `IndicatorComparisonResponse` | P1 LST disclosure | P1 label, separate dates and “surface temperature is not air temperature” caveat shown |
| [`time-series.mock.json`](../contracts/examples/time-series.mock.json) | `TimeSeriesResponse` | P1 series/missing point | Missing 2021 point remains a gap; it is not interpolated silently |
| [`processing-job.mock.json`](../contracts/examples/processing-job.mock.json) | `JobResponse` | P1 queued-state design only | It cannot make live job creation appear enabled in P0 |

Do not fetch referenced mock image/GeoJSON files during planning; the fixture warns that the layer asset is not included. The component should enter the same missing-layer fallback used for an HTTP 404.

`BlockResultsResponse` is currently a shared schema/example without an OpenAPI operation. For the frozen P0 contract, drill into the QA-approved subdistrict using its `RegionRef` and the existing region summary/detail operations. Adding a bulk subdistrict-results endpoint later is a contract proposal, not a frontend assumption.

## 6. Response-to-view-model rules

Every normal response uses `data`, `meta`, and `links`. Map it once at the repository boundary.

| Contract field | View behavior |
|---|---|
| `meta.dataMode` | Persistent `Live`, `Cached`, or `Precomputed demo data` badge |
| `meta.generatedAt` | “Generated” timestamp in provenance/status area |
| `meta.mock` | Conspicuous synthetic-data label; mock values cannot appear in judged evidence |
| `meta.partial` and `meta.warnings` | Partial banner and accessible warning list; do not hide completed metrics |
| `data.region` and periods | Page title, selection summary and map bounds; IDs stay opaque |
| `metric.*Value` | Format only when non-null; use the contract unit, not a UI-assumed unit |
| `metric.unavailableReason` | Required explanation beside unavailable metrics |
| `data.status` | `complete`, `partial`, `unavailable` or `failed` screen/component state |
| `quality.level`, `basis`, `reasons`, `warnings`, `evidence` | Visible quality summary with expandable evidence; color is not the only signal |
| `provenance.sources` | Dataset/provider, mission/collection, item IDs, acquisition times, processing baseline, source link, citation and license |
| `provenance.algorithm*`, CRS, resolution, parameter hash | Technical provenance; do not expose local paths or credentials |
| `interpretation` | Render supplied summary, caveats and suggested actions as disclosed guidance; do not infer causation |
| `layers[]` | Pass only to the safe layer adapter; preserve bounds, opacity, legend, attribution and offline flag |
| `links` | Navigation hints only after same-origin/base-path validation; never execute or inject them as markup |

Do not calculate a missing server metric in the browser. Formatting and view-state derivation belong in the mapper; scientific computation and validation do not.

## 7. Complete request flows

### P0 live/cache comparison

```text
User chooses Nagpur, the approved period pair and P0 indicators
→ React selection handler checks that visible fields are complete
→ repository builds a ComparisonRequest and, when live acceptance is enabled, creates a per-action idempotency key
→ ApiTransport sends POST /api/v1/comparisons with Content-Type: application/json
→ planned FastAPI route validates JSON, IDs, dates, indicator list and supported scenario
→ server-side result repository resolves immutable processed artifacts
→ server returns 200 DistrictSummaryResponse
→ ApiTransport validates content type and response shape
→ mapper creates mode, metrics, warnings, links and navigation state
→ React renders the summary and requests indicator detail/layers on demand
```

The same idempotency key may be retried with the same canonical body. Reusing it with a different body can return `409`; the browser must create a new key for a genuinely new user action. P0 should normally resolve synchronously; if a future approved live path returns `202`, the UI shows the queued job resource and polls only its provided/validated `Location`.

### Offline/demo comparison

```text
User makes the same selection
→ repository creates the same canonical request
→ DemoTransport canonicalizes it into a manifest request key
→ local manifest entry and referenced payload are size/hash checked
→ response is validated against the same schema
→ the same mapper creates the same view model
→ React renders with a persistent precomputed/mock or real-demo label
```

### Allowed fallback

```text
ApiTransport health/request fails due to connectivity, timeout or documented 503
→ gateway applies the explicit fallback policy
→ DemoTransport resolves the exact supported canonical request
→ UI announces and displays the changed data mode
→ user continues with precomputed data carrying its own generation time and provenance
```

Never silently fall back after `400`, `401`, `403`, `409`, `422`, schema/integrity failure, or a response for a scientifically different request.

## 8. UI state model and failures

| Condition | User-visible state | Retry/fallback |
|---|---|---|
| No selection yet | Guided empty state | None |
| Request in progress | Non-blocking loading state; preserve selection; disable duplicate submit | Abort stale request when selection changes |
| `200`, complete | Metrics, layers, quality, provenance and interpretation | Normal navigation |
| `200`, partial | Completed content plus partial banner and unavailable reasons | User may choose another supported scenario |
| `202` | Queued state with progress/status from `JobResponse` | Bounded polling only for approved P1 |
| `400` | Malformed-request message | Fix client construction; do not auto-retry |
| `401` | Authentication required | P1 admin only; never ask public users for provider credentials |
| `403` | Not permitted | Do not retry or reveal protected details |
| `404` | Region/result/layer unavailable | Keep metrics when only a layer is missing; offer supported selection |
| `409` | Request/idempotency conflict | Preserve form and start a new user action after explanation |
| `410` | Job expired | Stop polling; offer a supported fresh request if authorized |
| `422` | Valid JSON but unsupported/invalid domain input | Show `invalidParams` near relevant controls |
| `429` | Rate limited | Honor bounded `Retry-After`; no tight polling loop |
| `502` | Approved upstream failed | Explain temporary source failure; explicit demo option if policy allows |
| `503` | Service unavailable | Announce retry or disclosed demo fallback |
| `500` or invalid response | Unexpected error with safe trace ID | Do not show raw stack/response; use last verified demo path when policy permits |
| Asset 404/hash mismatch | Map/layer unavailable | Static image if verified, otherwise metric/table and attribution |
| WebGL/context loss | Interactive map unavailable | Static image plus table/text; no loss of core result |

Use an error boundary for unexpected rendering failures, but still model transport/domain failures as ordinary typed states. A blanket “Something went wrong” is insufficient when `ProblemDetails` supplies a safe, specific explanation.

## 9. Environment and security rules

Approved public variables are documented in [`.env.example`](../.env.example):

- `VITE_API_BASE_URL` — public base URL only; normalize it once and restrict operations to known SPARC paths.
- `VITE_DATA_MODE` — public `demo`/approved mode selector; never use it as authorization.

`VITE_*` values are compiled into browser assets and are visible to every user. Therefore:

- never use `EARTH_ENGINE_PROJECT`, Earth Engine credentials, bearer/admin tokens, database URLs or signed provider URLs in frontend code or `VITE_*` variables;
- never call Copernicus, USGS or another secret-bearing provider directly from the browser;
- do not log entire provenance/provider responses if they could contain transient URLs;
- do not accept an arbitrary URL, local path, HTML snippet, expression or command from a response or query string;
- resolve layer/navigation URLs against the expected same-origin/app base and supported media types;
- render API text as text, never untrusted HTML;
- use opaque IDs; do not infer disk paths or database keys;
- abort stale requests and cap retries/polling to prevent request amplification; and
- keep attribution visible even when the analytical layer fails.

FastAPI owns CORS. `SPARC_ALLOWED_ORIGINS` is server-only and should list the exact browser origin; wildcard credentials behavior is not an acceptable shortcut.

## 10. Accessibility and responsive acceptance

- The entire selection-to-result path works with keyboard only, at 200% zoom and at 360 px width.
- Loading, mode changes, partial results, validation errors and job status changes are announced without repeatedly interrupting screen-reader users.
- Every chart has a data table or equivalent text; every map has a meaningful static/text fallback.
- Quality and change direction use text/icon/pattern as well as color.
- Focus moves deliberately after submit/error and returns predictably from drawers/dialogs.
- Reduced-motion preference disables decorative movement and optional 3D auto-animation.
- Controls keep programmatic labels, descriptions and error associations.

## 11. Optional user-provided 3D

3D is a showcase, not an analytical data source or navigation dependency. The original Earth/satellite payloads remain user-owned and must not be generated, edited, converted, committed or redistributed without approval. After asset inspection, Claude may implement a lazy isolated adapter only if:

- the format, license, source, size and device budget are approved;
- no model request occurs on the critical dashboard path;
- load/time/WebGL errors produce the neutral placeholder or accessible 2D poster;
- reduced motion and keyboard behavior are usable; and
- removing the entire 3D module leaves P0 routes, bundle and data untouched.

## 12. Frontend acceptance matrix

| Test | Input | Expected evidence |
|---|---|---|
| Happy path | District summary plus three P0 comparisons | Correct values/units, period labels, layer legends, mode and provenance |
| Empty input | Submit before a required selection | Browser feedback; no request sent |
| Invalid/unsupported period | Problem fixture / `422` | Field-level reason and no silent fallback |
| Partial data | Partial fixture | Nulls shown unavailable, warnings present, no fake chart point/layer |
| Server unavailable | Forced network/timeout/503 | Visible disclosed demo transition or deliberate retry state |
| Schema mismatch | Remove a required field in a test copy | Incompatible-data state; presentation components do not render it |
| Missing layer | Planning descriptor with absent asset | Metrics/table remain; safe layer fallback appears |
| Unauthorized admin operation | Attempt restricted P1 creation | Browser has no public control/token; `401/403` is not bypassed |
| WebGL unavailable | Disable WebGL | Static/text/table path completes |
| Mock disclosure | Any committed example | Synthetic/mock label cannot be missed |

## 13. Handoff back to Codex

When reporting an integration issue, Claude supplies the operation ID, method/URL, sanitized request shape, status, response schema name, contract revision, fixture or artifact version and failing UI state. Do not send provider credentials, full authorization headers, raw signed URLs or user-local paths.

If the API response is contract-valid but the UI is wrong, Claude owns the fix. If the response violates OpenAPI/JSON Schema, Codex owns the server fix. If the contract itself is ambiguous or wrong, both stop and use the breaking-change procedure in [the workplan](./two-developer-workplan.md#10-breaking-change-escalation).

## 14. Related documents

- [API contract architecture](./architecture/api-contract.md)
- [Offline demo strategy](./architecture/offline-demo-strategy.md)
- [3D asset integration](./architecture/3d-asset-integration.md)
- [Integration plan](./integration-plan.md)

Removing this handoff would remove the exact mock-to-screen mapping, browser/server security boundary and transport equivalence rules needed for independent frontend implementation.
