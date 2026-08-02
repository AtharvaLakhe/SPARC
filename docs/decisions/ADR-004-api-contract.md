# ADR-004: OpenAPI-first, versioned contract shared by live and demo modes

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Shared; Codex is primary contract editor
- **Applies to:** Browser/backend integration, mock data, demo data and future clients

## Context

Two developers and separate coding agents must work in parallel. The frontend needs reliable mock responses before the backend exists, while the backend and geospatial pipeline need stable output requirements. Live/semi-live and precomputed demo modes must render the same UI without divergent domain models.

Independent handwritten TypeScript and Python interfaces would drift. A loosely described endpoint list would not define nullability, error states, quality/provenance requirements, async behavior or breaking changes.

## Decision drivers

- Day 0 frontend/backend parallelism.
- Machine-verifiable schemas and examples.
- One semantic model across live, cache and demo data.
- Explicit scientific quality/provenance fields.
- Safe asynchronous-job and error semantics.
- Evolvable public contract without exposing storage/provider details.

## Decision

1. `contracts/openapi.yaml` is the normative API description using OpenAPI 3.1 semantics.
2. The current OpenAPI publication is 3.1.2. The documentation-phase contract declares `openapi: 3.1.0` for planned FastAPI/tool compatibility while using OpenAPI 3.1/JSON Schema 2020-12 semantics. This exact patch choice must be proven against the selected validator/generator; compatibility is tested, not assumed.
3. Public paths use `/api/v1`. Resource IDs are opaque stable strings.
4. Committed examples validate against the specification and drive the frontend mock/DemoTransport.
5. Generate TypeScript types/client artifacts from the contract where the selected tool is reliable, or validate a small adapter against generated schema types. Generated artifacts are not hand-edited.
6. FastAPI/Pydantic models must conform to the same contract; CI compares the served/generated OpenAPI or response fixtures with the reviewed source.
7. Live, cached and demo responses share operation-specific `data` schemas and common metadata including `schemaVersion`, `generatedAt`, `dataMode`, `partial` and warnings.
8. Errors use RFC 9457 Problem Details plus stable SPARC `code`, sanitized `traceId` and `invalidParams` fields.
9. GeoJSON follows RFC 7946 WGS 84 longitude/latitude; analysis CRS remains provenance, not a different public GeoJSON CRS.
10. Layer endpoints accept opaque `layerId` values only. They never fetch a client-provided URL.
11. `POST /comparisons` returns `200` for a precomputed/cache hit or `202` plus `Location` for enabled queued work. An `Idempotency-Key` protects creation retries.
12. Scientifically usable incomplete results use `200` with `partial: true` and explicit missing fields/warnings; they do not misuse HTTP `206`.

## Required contract domains

- District, block and subdistrict region hierarchy and capabilities.
- Structured baseline/comparison periods.
- Indicator identity/method version, units and direction.
- Baseline, comparison, absolute and percent change values with null reasons.
- Confidence evidence and data-quality coverage/warnings.
- Provenance with provider/catalog/source Item identity, method/parameter version, analysis CRS, license and citation.
- Plain-language interpretation and proxy/non-causation caveats.
- Provider-neutral layer descriptors, legends, attribution and offline availability.
- Jobs in queued, running, complete, partial, failed and cancelled states.
- Problem details for validation, authorization, conflict, quota, upstream and service failures.

## Ownership and freeze

- Codex proposes/edits the normative specification, examples and server conformance fixtures.
- Claude consumes reviewed artifacts and owns the frontend repository/transport mapping.
- Both review any change that alters client-visible shape or meaning.
- Contract freeze occurs at the end of Day 0 after examples and mock rendering pass.
- Additive compatible changes require review and regenerated artifacts.
- Removing/renaming a field, adding a required field, narrowing an enum, changing nullability or changing semantic meaning is breaking. It requires a version decision, migration note, updated examples and both sides updated before merge.

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Frontend and backend define types independently | Teams start without tooling | Silent drift, duplicate review, demo/live divergence | Rejected |
| FastAPI code-first only | Automatic schema from Pydantic | Frontend waits for backend/models and server choices become contract by accident | Rejected as sole workflow |
| TypeScript schema first only | Frontend-friendly | Python conformance still duplicated and HTTP semantics underdefined | Rejected as sole workflow |
| GraphQL | Typed queries and flexible selection | Additional runtime/tooling/authorization/cache complexity with no P0 need | Rejected |
| OpenAPI 3.1 source plus validated examples | Language-neutral, mockable and standard | Requires tooling compatibility and ownership discipline | **Selected** |

## Consequences

### Positive

- Claude can build against valid mocks on Day 1 without waiting for FastAPI.
- Demo/static data and live API results cannot intentionally diverge in shape.
- Errors, async states, provenance and partial data are designed before UI/backend implementation.
- Future clients can reuse a standard public description.

### Negative and trade-offs

- Contract design and examples consume Day 0 time.
- OpenAPI 3.1 support differs across generators; the toolchain needs a compatibility gate.
- Generated clients can create noisy diffs and must be version-pinned.
- A contract can prove shape, not scientific correctness; methodology/validation remain separate.

## Security implications

- Schemas bound strings, arrays, periods, pagination, response sizes and enums.
- P0 uses approved region IDs rather than arbitrary uploaded geometry or remote URLs.
- Provider credentials, raw errors, host paths, signed URLs and internal service names are absent from public schemas/examples.
- CORS uses explicit origins; public read routes do not add unnecessary authentication.
- A future processing endpoint must be protected or disabled and must accept approved recipes, never commands/SQL/paths/URLs.

## Reversal conditions

Changing the contract technology requires equivalent language-neutral schema generation, examples, HTTP semantics, error modeling and live/demo compatibility. Operation-level schema changes follow the breaking-change procedure even if storage or provider implementations change internally.

## Sources

Official standards/documentation were accessed on 2026-08-02.

- [OpenAPI Specification 3.1.2 — OpenAPI Initiative, 2025-09-19](https://spec.openapis.org/oas/v3.1.2.html). Current OpenAPI 3.1 patch and versioning semantics.
- [FastAPI features — FastAPI project](https://fastapi.tiangolo.com/features/). OpenAPI/JSON Schema and validation support; MIT license.
- [FastAPI request bodies — FastAPI project](https://fastapi.tiangolo.com/tutorial/body/). Pydantic model validation and schema generation.
- [RFC 9457: Problem Details for HTTP APIs — IETF, July 2023](https://www.rfc-editor.org/rfc/rfc9457). Standard machine-readable error shape.
- [RFC 9110: HTTP Semantics — IETF, June 2022](https://www.rfc-editor.org/rfc/rfc9110). Status, method and representation semantics.
- [RFC 7946: GeoJSON — IETF, August 2016](https://www.rfc-editor.org/rfc/rfc7946). Public geometry exchange convention.
