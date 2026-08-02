# SPARC testing plan

**Status:** test specification; test runners and application code do not exist yet  
**Applies to:** P0 release candidate, primary and backup demo packs, and any P1 feature admitted before feature freeze

## 1. Purpose and evidence rule

Testing is split because one passing category cannot substitute for another:

- contract tests prove payload shape and HTTP semantics;
- unit tests prove arithmetic and local logic;
- integration tests prove browser/server/data boundaries;
- scientific validation tests a mapped claim against independent reference evidence;
- accessibility and offline tests prove the judged experience remains usable;
- security checks look for unsafe trust, secret and path behavior.

No test has run merely because it is described here. Exact automated commands cannot be confirmed from the current codebase because no package manifests, application modules or test-runner configuration exist. The implementing developer must add the real commands to the root README and release evidence after scaffolding; placeholder commands are not acceptable as proof.

## 2. Test levels and ownership

| Level | Planned location | Owner | Input | Required evidence |
|---|---|---|---|---|
| Contract/schema | `tests/contract/**` | Codex; shared review | OpenAPI, canonical schema, mocks and release payloads | parse report, reference resolution and per-example validation |
| Processing unit | `tests/processing/**` | Codex | synthetic arrays/geometries and pinned fixtures | formula, mask, area, scale/offset and determinism results |
| API unit/integration | `tests/api/**` | Codex | immutable repository fixture and HTTP requests | status, media type, body, headers, redaction and authorization |
| Browser unit/component | `tests/frontend/**` or colocated test files | Claude | mock transport and accessibility states | rendering, keyboard, error, partial and transport tests |
| End-to-end | `tests/integration/**` | Shared | built browser, optional API and demo pack | full primary/backup journeys and screenshots/logs without secrets |
| Scientific validation | versioned validation workspace outside browser bundle | Codex/scientific reviewer | probability sample and independent reference labels | error matrix, adjusted areas, intervals and release decision |
| Release/manual | immutable release directory | Shared | clean presentation devices | cold-start, offline, WebGL, recovery and rehearsal record |

## 3. Test-data policy

1. Files under `contracts/examples/` are synthetic mocks. They test shape and UI states, not environmental truth.
2. Synthetic raster fixtures must be small, deterministic and designed to isolate one rule.
3. Real pilot output must carry `mock: false`, a dataset version, item IDs, method version, processing baseline where known, checksums and provenance.
4. Secrets, provider responses containing signed URLs, raw private paths and bearer values must never enter fixtures, snapshots or logs.
5. A scientific validation sample must remain separate from threshold-calibration samples. Changing a method after seeing held-out results requires a new version and new held-out evaluation.

## 4. Contract and schema suite

### Required static checks

- [ ] Parse `contracts/openapi.yaml` as OpenAPI 3.1.
- [ ] Resolve every internal and external `$ref` to `packages/contracts/schemas/sparc.schema.json`.
- [ ] Validate all files in `contracts/examples/` against their intended `$defs` type.
- [ ] Reject unexpected properties because the canonical response objects use `additionalProperties: false`.
- [ ] Confirm all date/date-time/URI formats and enum values.
- [ ] Confirm JSON never contains NaN, infinity or an expiring/signed provider URL.
- [ ] Confirm each operation documents every status the implementation emits.
- [ ] Confirm browser-generated or validated types come from the canonical source rather than copied handwritten interfaces.
- [ ] Validate every release-pack JSON/GeoJSON file before checksums are frozen.

### Required examples

| Example | Intended coverage |
|---|---|
| `district-summary.mock.json` | complete three-indicator summary |
| `water-comparison.mock.json` | water metric, quality, provenance and layers |
| `vegetation-comparison.mock.json` | NDVI/green-proxy state |
| `built-up-comparison.mock.json` | low-quality built-proxy caveats |
| `lst-comparison.mock.json` | P1 Landsat surface-temperature shape |
| `partial-data.mock.json` | usable partial response and warnings |
| `block-results.mock.json` | child-region collection |
| `time-series.mock.json` | P1 same-method time series |
| `layer-descriptor.mock.json` | allowlisted relative layer resolution |
| `processing-job.mock.json` | queued/running/completed job representation |
| `api-error.mock.json` | RFC 9457-style problem response |

## 5. API behavior suite

The canonical endpoint details are in [API contract](architecture/api-contract.md). The test server must use an isolated immutable fixture repository; no test depends on a live catalog unless explicitly marked upstream-integration.

### P0 endpoint matrix

| Method and URL | Normal case | Invalid/empty case | Failure case | Security assertion |
|---|---|---|---|---|
| `GET /api/v1/health` | `200`, `status=ok`, version and data mode | N/A; accepts no input | sanitized `500` if route fails | no configuration, credential or dependency detail |
| `GET /api/v1/regions` | `200` region list | invalid `type` → `400`; unmatched valid filter → `200` with empty list | sanitized `500` | no large private geometry or filesystem path |
| `GET /api/v1/regions/{regionId}` | `200` known opaque ID | empty path cannot match route; unknown non-empty ID → `404` | sanitized `500` | ID is allowlisted/length-bounded; no traversal resolution |
| `GET /api/v1/regions/{regionId}/summary` | `200` complete or declared partial result | missing/malformed dates → `422`; unknown ID → `404` | upstream `502/503`; internal `500` | server repeats period/ID validation; no silent demo substitution for `422` |
| `GET /api/v1/regions/{regionId}/indicators` | `200` supported results | invalid indicator/date → `422`; unknown region → `404`; valid no-results case remains explicit | `503` when required data unavailable | unavailable indicators are not silently omitted |
| `GET /api/v1/regions/{regionId}/indicators/{indicatorId}` | `200` metric, quality, provenance, interpretation and layers | unsupported enum/date → `422`; unknown stored result → `404` | upstream `502/503` | layer references are opaque relative IDs, never caller URLs |
| `POST /api/v1/comparisons` | `200` immutable hit or `202` restricted accepted job | malformed JSON → `400`; empty/missing/wrong fields → `422`; reused key with different body → `409` | rate limit `429`; upstream `502/503` | rejects arbitrary AOI, URL, local path, command and extra properties |
| `GET /api/v1/comparisons/{comparisonId}` | `200` complete/partial summary | unknown/empty identifier → `404` or route miss; expired transient resource → `410` | sanitized `500/503` | does not disclose another tenant/user concept if auth is added later |
| `GET /api/v1/layers/{layerId}` | `200` allowlisted descriptor | unknown ID → `404`; expired transient layer → `410` | sanitized `500/503` | no SSRF, path traversal, signed URL or provider credential |
| `GET /api/v1/metadata/datasets` | `200` source/citation/license records | N/A | sanitized `500/503` | stable catalog identity only, not temporary asset authorization |
| `GET /api/v1/metadata/indicators` | `200` method metadata | N/A | sanitized `500/503` | proxy wording and versions are immutable evidence |

P1 time-series, TileJSON and job-status paths receive the same treatment if enabled. A P0 release may leave restricted job creation disabled; it must not expose an unprotected stub that accepts work.

### Exact comparison request cases

The following values use mock identifiers and test contract behavior only.

#### Successful immutable lookup

```http
POST /api/v1/comparisons HTTP/1.1
Content-Type: application/json
Idempotency-Key: mock-key-00000001

{
  "regionId": "mock:district:nagpur",
  "baselinePeriod": {"startDate": "2019-10-15", "endDate": "2019-12-15"},
  "comparisonPeriod": {"startDate": "2024-10-15", "endDate": "2024-12-15"},
  "indicatorIds": ["surface-water", "vegetation", "built-up"],
  "modePreference": "demo"
}
```

Expected: `200 application/json`, a `DistrictSummaryResponse`, `meta.mock=true` for the fixture, and no upstream call.

#### Empty body

Send an empty request body with `Content-Type: application/json`.

Expected: `422 application/problem+json` because the required request body is missing; `invalidParams` identifies the body requirement, no repository/provider work runs, and no stack trace is returned. A non-empty syntactically malformed JSON body is a separate `400` case.

#### Well-formed but invalid body

```json
{
  "regionId": "",
  "baselinePeriod": {"startDate": "2024-12-16", "endDate": "2024-10-15"},
  "comparisonPeriod": {"startDate": "not-a-date", "endDate": "2024-12-15"},
  "indicatorIds": [],
  "modePreference": "unknown",
  "upstreamUrl": "http://127.0.0.1/private"
}
```

Expected: `422 application/problem+json`, `invalidParams` names the rejected fields, `additionalProperties: false` rejects `upstreamUrl`, and no repository/provider work runs.

#### Unsupported but structurally valid scenario

Use a valid opaque region and valid dates that are absent from the frozen demo manifest.

Expected: a typed unsupported/unavailable response (`422` for domain rule or `503` for temporarily unavailable data, according to the implementation decision), never unrelated demo values. The selected status and error code must be fixed before integration.

#### Server failure

Configure the fixture repository to throw after valid input.

Expected: `500 application/problem+json`, stable public error code and trace ID; no exception, local path, environment value or source response appears. The browser displays a retry/demo choice only under the explicit fallback policy.

#### Upstream failure

In an explicitly enabled live integration test, make the approved provider adapter return invalid content, timeout/unavailability and rate limiting.

Expected: invalid upstream response → `502`; temporary provider/capacity outage → `503` plus `Retry-After` when known; bounded retry only for safe transient conditions. Demo fallback may occur for documented connectivity/timeout/`503`, is visible, and never occurs for validation/auth errors.

### Authentication and authorization cases

Only `POST /api/v1/processing/jobs` is protected in the current contract and is P1/disabled in P0. A safe job-status representation may be read only from the server-provided opaque location; it must expose no request parameters, provider details, secret or authorization state.

| Case | Request | Expected |
|---|---|---|
| Missing credential | no `Authorization` header | `401 application/problem+json`; no job or provider call |
| Malformed/invalid credential | `Authorization: Bearer invalid-test-token` | `401`; value never echoed or logged |
| Valid identity, wrong role/scope | test principal without admin permission | `403`; no job created |
| Valid authorized principal | server-side test token and approved recipe | `202`, `Location: /api/v1/processing/jobs/{opaque-id}` |
| Browser attempts to read secret | any static bundle inspection | no admin/provider token present; credentials are not `VITE_*` values |

`401` means the caller has not established a valid identity. `403` means identity is known but the operation is not allowed. These are not connectivity failures and must never trigger demo-data fallback.

## 6. Processing verification suite

These tests prove implementation arithmetic, not scientific validity. The complete scientific protocol is in [validation plan](validation-plan.md).

- [ ] Sentinel-2 DN zero becomes nodata.
- [ ] `BOA_ADD_OFFSET` and `QUANTIFICATION_VALUE` are applied from metadata in the documented order.
- [ ] Every configured Sentinel-2 Scene Classification Layer value has an isolated accept/reject fixture.
- [ ] Categorical masks use nearest-neighbor resampling.
- [ ] NDVI and MNDWI denominator zero or near-zero becomes nodata rather than infinity.
- [ ] MNDWI uses `(B03 - B11) / (B03 + B11)` on the 20 m analysis grid.
- [ ] NDVI uses `(B08 - B04) / (B08 + B04)` per valid observation before temporal median.
- [ ] Built-up proxy uses the frozen NDBI/IBI diagnostics plus documented vegetation/water exclusions; bare-soil fixtures remain a named confusion case.
- [ ] One method version applies the identical threshold and cleanup rule to baseline and comparison.
- [ ] A pixel invalid in either period cannot become gain or loss.
- [ ] A known projected synthetic polygon returns expected square-metre area within a declared numeric tolerance.
- [ ] Baseline area zero returns `percentChange: null` and an explanatory reason.
- [ ] Common-valid coverage, cloud/nodata and scene-count values reconcile with masks.
- [ ] Re-running identical inputs, versions and seed reproduces checksums.
- [ ] Provenance and attribution survive every export.
- [ ] If P1 LST is enabled, known `ST_B10` DN fixtures apply Landsat Collection 2 Level-2 scale/offset correctly and each QA bit is isolated.

### Stop-rule tests

Force each condition and confirm the result is downgraded or withheld rather than silently widened:

- coverage below the documented minimum;
- fewer than two usable optical observations for most of the AOI;
- missing source metadata or reflectance offsets;
- irreconcilable grid/product versions;
- sensitivity changes exceeding the quality policy;
- no independent validation for a claimed high grade;
- only one P1 LST scene or no defensible rural reference;
- redistribution terms not approved.

## 7. Scientific validation gates

- [ ] Freeze AOI, periods, products, grids, masks, threshold candidates and seed before labelling.
- [ ] Build stable target, stable non-target, gain and loss strata on the common-valid footprint.
- [ ] Draw a probability sample with recorded inclusion probabilities; exploratory convenience review is labelled `EXPLORATORY_REVIEW_ONLY`.
- [ ] Keep reference labellers blind to threshold distance/confidence on initial review.
- [ ] Use temporally appropriate independent evidence and keep global satellite products as corroboration, not ground truth.
- [ ] Report user's accuracy, producer's accuracy, omission, commission, adjusted area and 95% intervals by relevant class/change.
- [ ] Apply the preregistered pilot release target in [validation plan](validation-plan.md), or mark `FORMAL_FAILED`/`NOT_SUITABLE_FOR_PUBLIC_CLAIM`.
- [ ] Never report a quality label as a probability of correctness.

## 8. Browser and end-to-end cases

### User-flow cases

1. **Normal success:** cold-start local HTTP, select Nagpur, frozen dates and each P0 indicator; inspect summary, detail, child region, quality and provenance. Expected: no console-blocking error, all visible values match payloads, static/table alternatives agree.
2. **Empty list:** transport returns a valid empty region/result collection. Expected: accessible “no available scenarios” state, no stale Nagpur values and no blank canvas.
3. **Invalid user input:** clear a required period or reverse dates. Expected: inline browser feedback; if request is forced, server returns `422` and UI renders named field errors.
4. **Partial data:** load `partial-data.mock.json`. Expected: visible partial badge/warning, available indicators remain usable, unavailable values are not shown as zero.
5. **Unknown region/layer:** return `404`. Expected: focused error with a route back to district selection; prior region values are cleared.
6. **Server failure:** return sanitized `500`. Expected: error state, retry action and disclosed demo option only when policy permits.
7. **Upstream outage:** return `503`/timeout in live mode. Expected: visible transition to precomputed demo mode when approved; generation date and mode remain shown.
8. **Unauthorized/forbidden:** simulate `401` and `403` on the protected job route. Expected: no automatic retry loop or demo substitution; browser never contains a private credential.
9. **WebGL loss:** disable WebGL or lose context. Expected: reviewed static image, legend, metrics and table; controls remain keyboard usable.
10. **Missing image/tile:** force one layer asset to 404. Expected: metric/table and warning remain; no entire-page crash.
11. **Contract mismatch:** change schema version/invalidate a fixture. Expected: typed incompatible-data screen; no best-effort rendering of ambiguous fields.
12. **Reduced motion:** enable `prefers-reduced-motion`. Expected: no continuous/parallax/auto-rotation behavior; 3D remains optional.

### Accessibility acceptance

- [ ] Complete critical flow keyboard-only with visible focus and logical order.
- [ ] All controls have programmatic names; status/errors are announced without repeated interruption.
- [ ] Map, chart and color encodings have equivalent text/table information.
- [ ] At 360 CSS pixels, no required control or evidence panel is lost.
- [ ] At 200% browser zoom, content reflows without two-dimensional scrolling for ordinary text regions.
- [ ] Contrast and non-color cues meet the agreed WCAG 2.2 AA review target.
- [ ] Touch targets, focus restoration after dialogs and escape/close behavior are verified.
- [ ] Optional 3D can be skipped and does not trap scroll, keyboard or focus.

## 9. Offline and deployment verification

Run from the immutable candidate, not a developer tree:

1. verify manifest paths, media types, byte sizes and SHA-256;
2. scan application assets for required remote origins and secret patterns;
3. disconnect Wi-Fi/network before cold browser start;
4. start the approved loopback launcher and open the recorded URL;
5. complete Nagpur, restart browser/server and repeat;
6. complete Bengaluru Urban from its independent pack;
7. stop FastAPI and prove DemoTransport remains complete;
8. disable WebGL and remove one noncritical layer to prove fallbacks;
9. corrupt a copy of the primary manifest and confirm refusal plus backup selection;
10. repeat on the backup presentation device.

Opening `index.html` through `file://` is not an accepted test or fallback.

## 10. Security suite

- [ ] Search tracked and release files for `API_KEY`, `apiKey`, `api_key`, `Bearer`, `Authorization`, `NEXT_PUBLIC_`, `VITE_`, `sk-`, token, password and database URL patterns; review matches rather than printing values in shared logs.
- [ ] Confirm `.env`/credential/private-key files and raw caches remain ignored while `.env.example` contains names and safe non-secrets only.
- [ ] Confirm every `VITE_*` value is safe for public browser exposure.
- [ ] Test path traversal strings, overlong IDs, encoded separators and unknown layer IDs; all remain within an allowlisted root.
- [ ] Test caller-supplied URL and loopback/private-network values; APIs reject them before outbound I/O.
- [ ] Confirm errors/logs redact tokens, signed URLs, stack traces and absolute filesystem paths.
- [ ] Confirm demo server binds loopback and serves a fixed directory read-only with no listing/upload/execution.
- [ ] Confirm CORS uses explicit approved origins for API mode and never credentials with wildcard origin.
- [ ] Confirm job authorization occurs before rate-expensive work and authorization failure creates no state.

If a real secret is discovered, stop publication, remove it from current artifacts, revoke and rotate it, inspect history/logs and rebuild the candidate. Deleting the current file alone does not make a committed credential safe.

## 11. Exit criteria and test record

The release record must contain:

```text
candidateVersion
sourceCommit
datasetVersion
schemaVersion
testEnvironment
automatedCommandsActuallyRun[]
automatedResults[]
manualScenarios[]
scientificValidationStatus
knownLimitations[]
manifestChecksum
reviewers[]
timestamp
```

Release is blocked by any P0 contract drift, untraceable result, unapproved redistribution, exposed secret, official/causal misclaim, missing offline backup, or critical-flow accessibility failure. P1 failure removes the P1 feature; it does not weaken a P0 gate.

Related documents: [development roadmap](development-roadmap.md), [offline strategy](architecture/offline-demo-strategy.md), [deployment guide](deployment-guide.md), [risk register](risk-register.md) and [demo script](demo-script.md).
