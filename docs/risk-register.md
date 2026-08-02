# SPARC risk register and fallback ladder

**Status:** active planning register  
**Review cadence:** beginning and end of each implementation day, plus before release freeze

## 1. Risk policy

A fallback protects a trustworthy smaller result; it is not permission to hide a failure. When a scientific, licensing, integrity or secret gate fails, the correct response may be to withhold a result or stop publication. Availability fallbacks must visibly disclose mode and dataset age.

Ratings are qualitative planning judgements (`Low`, `Medium`, `High`) because no implementation telemetry exists. Owners must update triggers and ratings with evidence during implementation.

## 2. Global fallback ladder

Apply the first safe level that preserves the affected claim:

1. **Retry a bounded transient operation** only when it is idempotent and the failure is connectivity, timeout or explicit temporary capacity.
2. **Use the approved equivalent provider adapter** with the same underlying product/bands and preserve provider/product provenance.
3. **Use preselected local source inputs** and reproduce the frozen pipeline.
4. **Use the verified immutable Nagpur precomputed pack** with a visible data-mode/generation label.
5. **Use a static layer plus metrics/table** when interactive mapping or one layer fails.
6. **Use the independently verified Bengaluru Urban pack** when the primary pack itself is unavailable.
7. **Reduce scope** to the simplest scientifically supported district result; omit child-region, P1, live, cloud, dynamic map and 3D work.
8. **Withhold the affected claim or stop the demo** when integrity, licensing, secrecy or scientific validity cannot be preserved.

Validation, authentication, authorization, contract incompatibility and corrupt-integrity errors skip automatic live-to-demo substitution. They require correction, an explicitly matching backup, or withholding.

## 3. Risk register

| ID | Risk and trigger | Likelihood | Impact | Owner | Prevention / early evidence | Required fallback and release effect |
|---|---|---:|---:|---|---|---|
| R-DATA-01 | Copernicus catalog unavailable, times out or throttles during discovery | Medium | High | Codex | Day 0 metadata inventory; cache stable item IDs; bounded retries; provider adapter | Use approved equivalent catalog preserving Sentinel product identity, then retained local inputs; judged path uses precomputed pack |
| R-DATA-02 | Candidate Sentinel-2 scenes/bands or processing metadata are missing | Medium | High | Codex | Verify item IDs, bands, processing baseline, offsets and QA before download | Reject affected item; use an approved provider or retained input within the fixed Nagpur windows; otherwise downgrade/withhold indicator |
| R-DATA-03 | Cloud/residual-haze coverage leaves inadequate common-valid footprint | Medium | High | Codex | Scene-count and common-valid dry run; identical masks/grid across periods | Use approved additional same-season scenes symmetrically; report coverage; district-only or low-quality result; withhold if stop rule fails |
| R-DATA-04 | Baseline/comparison seasons are not comparable | Medium | High | Shared | Fixed Nagpur windows, candidate backup windows, season labels and compositing policy | Do not switch Nagpur dates; withhold its public change claim. Bengaluru is admitted only if its candidate windows pass QA; a later period redesign is a new documented method/version, not this release |
| R-DATA-05 | Boundary geometry, names or hierarchy fail QA | Medium | High | Codex | Geometry validity, CRS, overlap/gap, area, identifier and child-parent checks | Keep district only; Hingna remains merely a provisional candidate until it passes; select another validated Nagpur child only with documented QA |
| R-LIC-01 | Exact boundary redistribution terms are unavailable or restrictive | Medium | Critical | Shared | Record dataset-specific license/terms and attribution before packaging; Survey of India ABDB only after exact terms are recorded | Do not redistribute the unapproved boundary; use only a separately verified permitted source/artifact or omit geometry; never assume a GODL/LGD alternative without verification |
| R-LIC-02 | Satellite/context/model license or attribution is incomplete | Medium | Critical | Shared | Source register, NOTICE and manifest attribution audit | Remove affected distributable asset/claim; retain permitted derived summaries only if terms explicitly allow; optional 3D remains absent |
| R-METH-01 | MNDWI threshold is unstable across sensitivity runs | Medium | High | Codex | Fixed rule, pooled calibration, sensitivity and confusion-risk review | Show low/medium quality and sensitivity; use simpler frozen rule; withhold policy-facing water claim if conclusion changes |
| R-METH-02 | NDVI/green proxy is misread as forest loss | Medium | High | Shared | Proxy wording, crop/rain/irrigation/phenology caveats in API and UI | Replace claim with observed vegetation-activity/green-cover wording; withhold causal/forest conclusion |
| R-METH-03 | Built-up spectral proxy confuses bare soil, construction or bright roofs | High | High | Codex | Exclusions, fixed calibration, risk strata, sensitivity and visual review | Display low quality/confusion caveat; use corroboration as context only; withhold precise expansion claim if validation fails |
| R-METH-04 | Formal scientific validation is incomplete or fails | High | Critical | Codex/scientific reviewer | Separate calibration/held-out sample; probability design; preregistered targets | Label `NOT_RUN`, `EXPLORATORY_ONLY` or `FORMAL_FAILED`; never claim high quality; present method prototype or withhold affected public finding |
| R-METH-05 | Percentage change divides by zero baseline | Low | Medium | Codex | Unit fixture for zero baseline | Return `null` with `BASELINE_ZERO`/explanation; UI displays “not defined,” never infinity/0% |
| R-LST-01 | Landsat LST has one clear scene, missing ST metadata or no defensible rural reference | High | Medium | Codex | P1 gate, QA/scene inventory, source product scaling tests | Remove LST/SUHI from release or label a low-quality surface-temperature snapshot; never call it air temperature |
| R-CON-01 | OpenAPI, JSON Schema, mocks, API and browser types drift | Medium | Critical | Shared | Day 0 freeze, one canonical schema, examples and daily contract gate | Stop integration; fix canonical source plus both consumers in one checkpoint; use last matching immutable release |
| R-CON-02 | Breaking contract change arrives after freeze | Medium | High | Shared | Change note, both reviews, schema-version policy | Keep v1 unchanged or use an adapter; defer P1 behavior instead of destabilizing release |
| R-CON-03 | Old browser shell loads incompatible new/old data pack | Medium | High | Shared | Minimum app/schema version in manifest; versioned immutable paths | Reject as incompatible; load a matching preserved app-and-pack pair; never best-effort ambiguous fields |
| R-API-01 | FastAPI unavailable or health check times out | Medium | High | Codex | Cheap health endpoint and explicit transport state | On connectivity/timeout/`503` only, visibly select DemoTransport; complete local journey |
| R-API-02 | Internal repository/server exception | Medium | High | Codex | Fixture failures, sanitized problem responses, request IDs | Show safe error and retry; use disclosed matching demo pack if policy allows; no stack trace/path/secret |
| R-API-03 | Upstream returns invalid response, outage or rate limit | High | High | Codex | Adapter validation, bounded timeout/retry, cache, `502/503/429` semantics | `502` invalid upstream; `503` temporary unavailable; honor retry budget; use precomputed mode visibly; never hang request |
| R-API-04 | Expensive raster processing blocks request handler | Medium | High | Codex | Read-only P0; deterministic lookup; restricted `202` job contract | Disable live creation and serve immutable results; defer queue/worker to P1 |
| R-SEC-01 | Secret enters Git, browser bundle, screenshot, fixture or log | Low | Critical | Shared | `.gitignore`, server-only names, secret scan and redaction tests | Stop release; remove exposure, revoke/rotate, inspect history/logs and rebuild. Demo data is not a substitute for rotating a leaked secret |
| R-SEC-02 | Caller-controlled URL/path causes SSRF or traversal | Medium | Critical | Codex | Opaque IDs, length limits, allowlisted root/hosts, no arbitrary AOI/URL/path fields | Reject before I/O with safe `4xx`; disable affected route until fixed; never proxy the requested URL |
| R-SEC-03 | Protected job endpoint is enabled without reliable auth/rate limit | Medium | Critical | Codex | P0 disabled state; `401/403/429` tests; authorization before work | Disable job creation; retain read-only API/demo operations |
| R-SEC-04 | CORS/public binding exposes development service | Medium | High | Codex | Loopback default; explicit origins; no wildcard with credentials | Stop public service, correct binding/origins and re-test; local static demo remains loopback-only |
| R-SEC-05 | Untrusted upstream asset triggers driver confusion, file/network access, parser exploitation or resource exhaustion | Medium | Critical | Codex | Separate acquisition from parsing; explicit driver restriction; byte/dimension/band/time limits; isolated credential-free worker; quarantine and verified publication | Stop acquisition; quarantine input and derived output; rebuild only from a verified source under the hardened process |
| R-SEC-06 | Raster parser can access catalogue credentials or published output | Medium | High | Codex | Separate acquisition/parser/publisher processes; no secrets or unrestricted egress in parser; least-privilege filesystem access | Revoke exposed credentials, rebuild the worker environment, invalidate affected output and reprocess |
| R-BUILD-01 | Geospatial native dependency/version mismatch breaks reproducibility | High | High | Codex | Pin tested GDAL/Rasterio/PROJ matrix; clean-room build before event | Use verified container/environment or retained precomputed pack; do not install during presentation |
| R-BUILD-02 | Vite/API clean build fails late | Medium | High | Shared | Locked dependencies, daily clean build and preserved candidate | Use last verified release; remove the latest optional change rather than edit frozen copy |
| R-PACK-01 | Primary manifest/asset missing, corrupt or contains mock placeholder | Low | Critical | Shared | Path/size/hash/mock gate before freeze | Refuse affected values; restore verified Nagpur copy or select independently verified Bengaluru pack; never present mock as real |
| R-PACK-02 | Demo bundle contains a required remote font, CDN, basemap or public tile call | Medium | High | Claude/shared | Remote-origin scan; network-disabled cold start | Bundle approved asset or remove dependency; use neutral local context/static background |
| R-PACK-03 | Bundle/repository grows too large with raw rasters or tiles | Medium | High | Codex | Ignore raw/interim data; size-bounded publishable pack and zooms | Remove raw/reproducible intermediates and unnecessary zooms; retain summaries/static layers and hashes |
| R-DEMO-01 | Local launcher or expected port fails | Low | Critical | Shared | Package and rehearse exact loopback launcher on two devices | Use separately tested immutable copy/device; do not switch to `file://` or improvise install/network service |
| R-DEMO-02 | Internet or public basemap fails at venue | High | Low | Shared | No required external origin/public basemap in P0 | Continue complete local journey with neutral bundled context and visible attribution |
| R-DEMO-03 | WebGL context unavailable/lost | Medium | High | Claude | Static image/table alternative; forced-loss test | Continue with static layer, legend, metrics and table; no reload required |
| R-DEMO-04 | One image/tile/layer fails | Medium | Medium | Claude | Per-layer error boundary and asset check | Preserve metrics/table/provenance; announce missing spatial layer and continue |
| R-DEMO-05 | Entire primary device fails | Low | Critical | Shared | charged backup device and separately verified copy | Switch to backup device/copy with the same script; if unavailable, use reviewed evidence screens and disclose limitation |
| R-3D-01 | User assets are missing, unlicensed, unsafe, too large or incompatible | High | Low | User/Claude | Do not assume format; inspect hash, references, license, performance and accessibility only after supply | Keep neutral 2D placeholder/poster; optional showcase is omitted with no analytical impact |
| R-3D-02 | 3D runtime/context/animation fails during demo | Medium | Low | Claude | Lazy isolated route, reduced-motion path, disposal and timeout | Fall back to still 3D, then accessible 2D poster/dashboard; skip showcase |
| R-UX-01 | Critical flow fails at 360 px, 200% zoom or keyboard-only | Medium | High | Claude | Test from Day 1; semantic controls and logical focus | Remove decorative layout/map dependence; use stacked controls, tables and text; block release if journey remains inaccessible |
| R-UX-02 | Color/map/chart is the only carrier of meaning | Medium | High | Claude | Table/text equivalents and non-color cues | Display equivalent numeric/text summary and legend; omit inaccessible visualization if necessary |
| R-PERF-01 | Large layers or frontend bundle cause slow/crashing presentation | Medium | High | Claude/shared | Size report, representative-device timing, lazy P1/3D chunks | Use static WebP/PNG, fewer zooms and tables; remove optional runtime chunks |
| R-TEAM-01 | Two developers edit shared paths/lockfiles concurrently | Medium | High | Shared | Path ownership, announced editor, short branches and daily integration | Stop competing edits; primary owner recreates smallest change; resolve from canonical contract and re-run both consumers |
| R-TEAM-02 | Time pressure causes P1 work before P0 reliability | High | High | Shared | Daily P0 checkpoints and scope-cut order | Cut 3D, cloud, live jobs, LST, dynamic tiles and animation—in that order; never defer first P0 implementation to Day 4 |
| R-CLAIM-01 | Presenter calls proxies official SDG indicators, “real-time,” causal or policy proof | Medium | Critical | Shared | Reviewed script, visible proxy/data-mode labels and Q&A cards | Correct immediately; show methodology/provenance/limitations; withdraw unsupported statement from submission materials |
| R-BIZ-01 | Business model or market-size hypothesis is presented as validated demand | Medium | Medium | Shared | Label assumptions; customer interviews and willingness-to-pay tests | Present model as plausible experiment, not traction; avoid invented TAM/revenue claims |
| R-CLOUD-01 | Optional cloud deployment fails, incurs unexpected cost or changes behavior | Medium | Low | Codex | Deploy only after local freeze; immutable artifact promotion and spend limits | Do not deploy or roll back compatible app/data pair; demonstrate locally |

## 4. Named fallback coverage

This table makes every fallback requested for the prototype explicit. A later column may be used only when the earlier option is unavailable and scientific, integrity, license, and security gates still pass.

| Failure | Primary method | Secondary method | Precomputed method | Static/offline fallback |
|---|---|---|---|---|
| Bhuvan unavailable or permission unclear | Do not depend on Bhuvan; use the approved CDSE/Sentinel and boundary sources | Use a specifically identified Bhuvan dataset only after its own permission is verified | Retain already approved, attributable outputs only | Omit Bhuvan context; core dashboard remains complete |
| Copernicus/CDSE unavailable | Bounded retry against the current official endpoint | Earth Search or Planetary Computer adapter for the same underlying Copernicus product, with full provenance | Retained source inputs and independently verified immutable district results | Local demo pack with no provider call |
| Google Earth Engine unavailable | No action: it is not a runtime, build, preprocessing, or demo dependency | Omit optional Dynamic World comparison | Use an already permitted export only as labelled context | Core three-indicator path continues without it |
| Provider authentication failure | Correct server-side credential/configuration without logging values | Approved anonymous or alternate provider path for the same product | Retained local inputs/results | Demo pack; never move credentials into the browser |
| Quota or rate limit | Honor bounded backoff/`Retry-After` and stop at retry budget | Approved provider adapter | Immutable cached/precomputed result | Local pack; no repeated background polling |
| Cloud-heavy imagery | Add approved same-season scenes under the frozen composite rule | Symmetrically adjust both year windows through a recorded method decision | Use a pack that already passed common-valid coverage | Show low/partial quality or withhold the change; a static picture cannot repair invalid data |
| No suitable imagery | Run the documented primary gate once; do not relax QA or change Nagpur dates | Use Bengaluru Urban only if its candidate 2019-01-15–2019-03-15 versus 2024-01-15–2024-03-15 windows pass their own catalog/data QA | Use a previously verified pack whose provenance matches the claim | Present methodology/architecture only and disclose that the environmental result was withheld |
| Boundary data/license failure | Repair only under recorded topology and terms; recheck area/hash | Use another authority-, version-, code-, and license-verified source | Use a permitted, already verified district pack | Remove child drill-down/map geometry or keep boundary local and non-redistributed as terms require |
| Thermal processing failure | Correct Landsat L2SP QA/scaling/rural-reference issue | Publish only a clearly low-quality surface-temperature snapshot if its own gate passes | Use a validated P1 LST pack | Omit LST/SUHI; never substitute Sentinel-2 or call it air temperature |
| Tile server/layer failure | Retry the allowlisted local descriptor/asset once | Use packaged image/GeoJSON instead of dynamic tiles | Load the immutable layer from the demo pack | Keep metric, legend, attribution, provenance, accessible table, and reviewed static image |
| Backend deployment failure | Run the verified loopback API candidate | Switch visibly to DemoTransport | Serve identical immutable contract payloads | Static local web bundle; cloud backend is not required |
| Frontend deployment failure | Serve the verified build over local HTTP | Use the preserved candidate on the backup device | Load the same local app/data pair | Reviewed static evidence screens are last-resort presentation evidence, disclosed as such |
| Internet failure | Continue the already started local-HTTP journey | Select the local DemoTransport explicitly | Nagpur and Bengaluru packs contain critical JSON/layers/fonts | Static image/table path; no remote basemap, CDN, font, provider, or 3D dependency |
| 3D asset incompatibility | Inspect actual format/extensions/textures before selecting a runtime | With user approval, use an inspected compatible export or still render only | Use an approved poster generated from user-supplied material only if rights permit | Neutral 2D placeholder; omit the showcase with no analytical effect |
| WebGL failure | Isolate/recover the context without discarding result state | Disable interactive map and 3D | Packaged before/after image/GeoJSON representation | Accessible metrics, legend, table, provenance, and 2D poster |
| Large 3D asset | Enforce transfer/GPU/performance gate and lazy loading | Use a user-approved inspected lower-detail/exported variant | Load no 3D payload on the analytical route | 2D poster/placeholder; never delay P0 for model optimization |
| Merge conflict | Stop competing edits; primary path owner recreates the smallest change from current integration | Pair-resolve meaning from OpenAPI/schema/ADR and rerun both consumers | Preserve last verified integration candidate | Release the preserved candidate; omit the conflicting optional change |
| Contract drift | Fail the gate and correct canonical schema/OpenAPI/examples plus both consumers together | Use a reviewed adapter without changing v1 meaning | Load the last compatible app-and-pack pair | Freeze on verified mocks/demo pack; do not guess missing fields |
| Delayed backend | Continue frontend development against frozen mocks and DemoTransport | Implement only read-only immutable-result routes | Package contract-valid precomputed responses | Complete judged journey without FastAPI; disclose precomputed mode |
| Delayed frontend | Cut decorative/3D/P1 work and build the smallest accessible summary/comparison flow | Use contract-valid plain tables/static layers before interactive maps | Bind the verified mock/real demo pack to that minimal flow | Use reviewed static evidence only if the executable UI cannot be recovered, and disclose incompleteness |
| Incomplete validation | Complete the preregistered independent sample and report uncertainty | Downgrade quality and label `EXPLORATORY_ONLY` or `NOT_RUN` | Use only a result whose recorded validation is still applicable | Withhold the affected public finding; show method and limitations rather than an unsupported claim |

## 5. Daily risk gates

### End of Day 0

- [ ] Provider/product metadata and exact boundary terms are known enough to proceed, or the allowed fallback is explicit.
- [ ] No method, period or API meaning is ambiguous between workstreams.
- [ ] Every P0 item has a Day 1–3 owner; none begins only on Day 4.
- [ ] No browser-exposed variable can contain a private key.

### End of Day 1

- [ ] Representative outputs reveal coverage/threshold risks early.
- [ ] Browser failure states work from synthetic examples.
- [ ] Clean builds and native dependency versions are recorded.
- [ ] Any scientific stop rule has a release decision, not only a bug ticket.

### End of Day 2

- [ ] Nagpur and Bengaluru packs pass schema/integrity checks or release scope is reduced.
- [ ] Both transports map to the same view-model semantics.
- [ ] All critical integration defects have one named owner.
- [ ] The current integration candidate remains demo-runnable.

### End of Day 3

- [ ] No critical/high risk lacks a tested fallback or explicit acceptance by the user/team.
- [ ] Primary and recovery copies have passed cold offline runs.
- [ ] Security/licensing/integrity blockers are zero.
- [ ] Remaining P1 risks result in feature removal, not weakened P0 claims.

## 6. Residual-risk communication

Every released result must expose the limitations that remain after mitigation: common-valid coverage, scene counts, threshold sensitivity, validation status, source/product versions, seasonal comparability and known class confusion. The presentation must state that satellite-derived proxy changes do not establish cause and are not official UN SDG values.

Related documents: [validation plan](validation-plan.md), [offline strategy](architecture/offline-demo-strategy.md), [3D integration](architecture/3d-asset-integration.md), [testing plan](testing-plan.md), [deployment guide](deployment-guide.md) and [demo script](demo-script.md).
