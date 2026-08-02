# Two-developer implementation workplan

**Status:** Implementation-ready coordination baseline  
**Window:** Day 0 through Day 3; Day 4 is contingency only  
**Contract freeze:** End of Day 0  
**Primary pilot:** Nagpur district  
**Backup pilot:** Bengaluru Urban district

This workplan turns the accepted architecture into two independent workstreams that converge once per day. It does not claim that the planned application directories or runtime code already exist.

## 1. Roles and non-negotiable boundaries

| Workstream | Primary owner | Exclusive implementation paths | Shared boundaries requiring review |
|---|---|---|---|
| Backend, data and delivery | Codex | future `apps/api/**`, `services/geoprocessing/**`, `scripts/data/**`, `tests/api/**`, `tests/processing/**`, `infra/**` | `contracts/**`, `packages/contracts/**`, demo artifacts, root configuration |
| Browser experience | Claude | future `apps/web/**`, `tests/frontend/**`, UI documentation and optional 3D integration code | contract review, demo-artifact consumption, integration tests |
| Release and scientific communication | Shared | none | acceptance evidence, disclosure text, integration branch and release candidate |
| Earth and satellite model payloads | User | actual binary assets | asset approval, license, size and format decisions |

The full path rules are normative in [repository ownership](./repository-ownership.md), [Git workflow](./git-workflow.md), and [ADR-009](./decisions/ADR-009-two-developer-ownership.md). A primary owner is responsible for correctness and first review; ownership does not authorize unilateral changes to a shared interface.

## 2. Shared source of truth

The following artifacts freeze together at the end of Day 0:

1. [`contracts/openapi.yaml`](../contracts/openapi.yaml) — HTTP methods, URLs, inputs, status codes and response schemas.
2. [`packages/contracts/schemas/sparc.schema.json`](../packages/contracts/schemas/sparc.schema.json) — canonical reusable JSON Schema 2020-12 shapes.
3. [`contracts/examples/`](../contracts/examples/README.md) — synthetic, conspicuously marked interface fixtures.
4. [`docs/indicator-methodology.md`](./indicator-methodology.md) — indicator names, units, formula versions, quality limits and scientific wording.
5. [`.env.example`](../.env.example) — approved public and server-only environment-variable names.

Claude must not create a second handwritten API model. Codex must not return a shape that merely resembles a fixture. Future generated TypeScript and Python bindings must come from the same reviewed contract and must identify their generator and source version.

## 3. Common definition of done

A task is done only when all applicable statements are true:

- its owned files are reviewed by the path owner;
- contract-shaped JSON validates against the canonical schema;
- browser and server use the same field names, enum values, null behavior, units and HTTP semantics;
- normal, loading, empty, partial and error behavior is testable;
- mock values remain visibly marked and are never presented as environmental findings;
- secrets, provider tokens, signed URLs and raw exception details are absent from source, logs, mocks and browser output;
- data mode, generation time, provenance, quality and caveats remain visible to the user;
- the critical journey remains usable without live providers, a public basemap, WebGL or optional 3D;
- test evidence and any accepted limitation are recorded in the pull request or checkpoint log; and
- the daily integration candidate can still complete the primary demo journey.

## 4. Coordination cadence

| Time | Participants | Decision/output |
|---|---|---|
| Start of day, 15 minutes | Codex and Claude | Confirm the contract revision, owned files, dependencies, daily acceptance target and integrator |
| Midday, 10 minutes | Both | Exchange a compact handoff packet; flag only contract, artifact or environment blockers |
| Before integration, 15 minutes | Both | Freeze workstream tips, run owner checks and identify merge order |
| Integration window, 45–60 minutes | Assigned integrator with both owners available | Build `integration/day-N`, run the gate, assign defects to the owning layer |
| End of day, 10 minutes | Both | Record pass/fail evidence, accepted fallbacks, tomorrow's starting commit and unresolved risks |

The handoff packet contains: branch/commit, changed paths, contract revision, mock or real fixture used, tests run, expected caller behavior, known failure states, security impact and rollback commit. It must not contain credentials or copies of unapproved raw data.

## 5. Day 0 — contract and independence

### Codex lane

| Task | Output | Acceptance | Fallback |
|---|---|---|---|
| Verify data/boundary gates | Catalog and boundary evidence for Nagpur and Bengaluru Urban | Identifiers, periods, source, license/attribution and recovery source are recorded | Retain only approved precomputed artifacts |
| Freeze methodology | P0 water, vegetation and built-up proxy definitions; P1 LST | Names, units, periods and limitations agree across requirements and contract | Drop an unvalidated enhancement |
| Freeze contracts | OpenAPI, JSON Schema and every mock example | Specs parse; examples validate; error semantics are explicit | Reduce optional operations without weakening the P0 comparison shape |
| Freeze server configuration names | Safe `.env.example` | Browser-visible and server-only settings are separated | Run demo-only with no provider credentials |

### Claude lane

| Task | Output | Acceptance | Fallback |
|---|---|---|---|
| Map fixtures to screens | Fixture/state matrix in [frontend handoff](./frontend-handoff.md) | Every P0 screen has a fixture or an explicit client-only state | Render a static fixture repository |
| Define data boundary | Planned typed gateway with `ApiTransport` and `DemoTransport` | Components receive the same view-model shape in either mode | Use `DemoTransport` only |
| Define accessible shell | Screen inventory, focus order, status announcements and non-WebGL alternative | Keyboard and 360 px journey can be implemented without waiting for the API | Prioritize table/image output over map interaction |

### Day 0 shared checkpoint

- Both owners review the same contract commit.
- All examples are treated as synthetic and `meta.mock` is surfaced.
- Claude can explain how each P0 view loads from committed examples without a server process.
- Codex can explain how FastAPI will return the same payloads without raster processing in request handlers.
- No implementation branch starts from an unfrozen interface.

**Exit decision:** tag or record the exact Day 0 contract commit. After this point, use the breaking-change procedure in section 10.

## 6. Day 1 — parallel core slices

### Codex lane

1. Create the reproducible boundary/composite processing slice with pinned inputs, common-valid masking, provenance and checksum output.
2. Produce one representative contract-valid result for each P0 indicator.
3. Build the planned FastAPI read path for health, regions, metadata, comparison and allowlisted layer descriptors.
4. Keep raster computation outside request handlers; handlers read immutable, versioned results.
5. Add formula, CRS, unit, schema and error tests.

**Codex acceptance:** representative results validate; raw values, cleaned values, quality evidence and provenance are traceable; request handlers do not call arbitrary external URLs or accept free-form code/paths.

### Claude lane

1. Create the React + TypeScript + Vite shell in the browser-owned path.
2. Load the Day 0 fixture mapping through `DemoTransport`, not direct imports from presentation components.
3. Implement region/period controls, summary cards, indicator detail, layer shell, quality/provenance, and loading/error/empty/partial states.
4. Add accessible labels, status announcements, keyboard order, reduced-motion handling and static map/table fallback.
5. Keep the optional 3D showcase behind a lazy, isolated boundary with a neutral placeholder.

**Claude acceptance:** the Nagpur P0 journey works against mocks at desktop and 360 px; the user can see that values are mock/demo, which periods are compared, and why a value is unavailable.

### Day 1 handoff

- Codex provides one validated representative response plus its schema/test evidence.
- Claude provides the canonical request key used by the demo repository and a screenshot/state list without copying API models.
- Both report whether real and mock responses map to the same planned view model.

**Checkpoint:** both lanes work independently from the frozen contract; no shared file has competing edits.

## 7. Day 2 — full analytical journey

### Codex lane

- Produce immutable Nagpur district results and one QA-approved subdistrict result for the three P0 indicators. Hingna is only a provisional candidate until boundary/license/data QA passes.
- Produce a validated Bengaluru Urban backup pack.
- Include quality, provenance, interpretation, layer descriptors, manifests and checksums.
- Complete cache/demo hits, partial results, problem responses, idempotency and safe layer lookup.
- Keep live job creation disabled if authentication, bounds or operational limits are not ready.

### Claude lane

- Replace fixture-only assumptions with the common repository interface while preserving `DemoTransport`.
- Complete before/after or change layers, indicator comparisons, district summary and one QA-approved subdistrict drill-down. A Hingna label may be used only after approval; its presence in synthetic fixtures is not that approval.
- Render `metric` nulls as unavailable with `unavailableReason`; never coerce them to zero.
- Render `meta.partial`, `meta.warnings`, quality level/evidence, provenance, attribution and interpretation.
- Use static images/tables when WebGL, a layer asset or a basemap is unavailable.

### First full request flow

```text
User selects region, approved periods and indicators
→ React event handler performs basic completeness checks in the browser
→ typed repository creates a canonical ComparisonRequest
→ ApiTransport sends POST /api/v1/comparisons as JSON
→ planned FastAPI route validates schema and domain rules on the server
→ result repository resolves an immutable comparison
→ server returns 200 DistrictSummaryResponse, or 202 JobResponse for approved future live work
→ transport validates the response contract
→ shared mapper creates the dashboard view model
→ React renders metrics, mode, quality, provenance, warnings and safe layer descriptors
```

Demo mode replaces the network operation with canonical manifest lookup and checksum/schema validation, then joins the same mapper. It must not fork presentation logic.

### Day 2 integration checkpoint

Use [the integration plan](./integration-plan.md). The gate passes only when:

- API and demo transports produce equivalent view-model states for the same supported request;
- the primary and backup packs resolve every referenced local asset;
- a 422 problem, a partial comparison and a missing layer each produce a deliberate UI state;
- network/timeout/503 fallback changes the visible data-mode label; and
- validation, authentication or integrity errors do not silently switch datasets.

## 8. Day 3 — hardening and release

### Shared P0 work

1. Run scientific sampling, contract, security, accessibility, responsive and offline verification.
2. Build the immutable local HTTP demo bundle with a versioned manifest and checksum report.
3. Test Nagpur and Bengaluru Urban from a cold browser with the network disabled.
4. Force API, asset, WebGL and local-data failures and verify the documented recovery behavior.
5. Freeze features, preserve the last passing candidate and rehearse two complete 5–7 minute runs.

### Owner emphasis

- Codex owns processing reproducibility, server errors, bundle integrity, secret scan and optional cloud instructions.
- Claude owns responsive behavior, focus/announcement behavior, chart/table readability and presentation-state polish.
- Both sign the evidence log and accept or remove any failing enhancement.

**Checkpoint:** the local HTTP candidate completes the judged path without network, live processing, a database, WebGL, a public basemap or a 3D model.

## 9. Optional Day 4 — contingency, not a feature day

- Fix only critical release defects and rerun the affected gate plus the complete offline smoke test.
- Consider user-provided 3D assets only after the Day 3 candidate is preserved and only after format, size, license and browser-budget inspection.
- Do not create, convert, replace, redistribute or commit model payloads without explicit user approval.
- If the optional scene fails any budget, accessibility or fallback condition, keep the neutral poster/placeholder.
- No P0 task may be deferred to Day 4.

## 10. Breaking-change escalation

After Day 0, a newly required property, removed or renamed property, narrower enum, changed unit/meaning, or changed URL/status behavior is breaking.

1. Stop dependent merges; keep the last passing integration candidate intact.
2. Write the old shape, proposed shape, reason, affected consumers, data migration and rollback.
3. Obtain both Codex and Claude approval.
4. Update JSON Schema, OpenAPI, every affected mock, examples documentation and contract tests as one reviewed change.
5. Update server and browser adapters in the same integration window; regenerate bindings from the reviewed source.
6. Increase the schema version when compatibility or meaning changes.
7. Prove the old demo pack is migrated or rejected with an explicit incompatible-data state.

If the change cannot complete safely within the daily checkpoint, preserve v1 and defer it. An adapter or omission is preferable to a late, partially implemented contract break.

## 11. Failure ownership

| Failing layer | First owner | Evidence required before handoff |
|---|---|---|
| UI layout, focus, rendering or view-model mapping | Claude | failing state/fixture, browser error and reproduction steps |
| Browser transport, URL construction or response parsing | Claude | method/URL/status, sanitized response shape and contract revision |
| HTTP route, validation, status or server serialization | Codex | sanitized request, route/operation ID, server test and trace ID |
| Result lookup, manifest, checksum or layer allowlist | Codex | canonical request key, artifact version and failing integrity result |
| Formula, QA, CRS, zonal result or provenance | Codex | processing recipe/version, input IDs and focused test |
| Shared schema or semantic mismatch | Both | minimal conflicting payload and explicit compatibility decision |
| User-provided model compatibility | Claude after user approval | asset audit without modifying the original payload |

The owner fixes the smallest failing layer. Neither workstream masks a backend defect with fabricated browser values or a browser defect with a server-only presentation field.

## 12. Related handoffs

- [Frontend handoff](./frontend-handoff.md)
- [Integration plan](./integration-plan.md)
- [API contract architecture](./architecture/api-contract.md)
- [Offline demo strategy](./architecture/offline-demo-strategy.md)
- [Data pipeline](./architecture/data-pipeline.md)

Removing this document would remove the daily owner sequence, cross-workstream acceptance criteria and exact escalation point that allow the two developers to implement independently without drifting from the frozen contract.
