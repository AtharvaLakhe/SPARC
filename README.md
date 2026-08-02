# SPARC

**Satellite-Powered Analytics for Resource Conservation**

SPARC is a planned district-level environmental decision-support prototype. It will turn open Earth-observation data into understandable before/after signals for local administrators, NGOs, communities, CSR teams, and environmental practitioners.

SPARC outputs are **satellite-derived SDG proxy indicators**, not official UN SDG indicators. They show observed spatial or temporal patterns and do not establish causation.

## Repository status

This repository is in the planning and contract phase. It contains requirements, research, architecture decisions, coordination rules, an OpenAPI draft, JSON Schemas, and clearly marked mock payloads. It intentionally contains no frontend, backend, geospatial processing implementation, downloaded imagery, processed geospatial data, deployed infrastructure, or third-party 3D model.

The selected pilot is **Nagpur district** with **Bengaluru Urban** as a smaller backup. P0 covers surface-water, vegetation/green-cover, and built-up-area proxies. Land-surface temperature and surface urban heat island analysis are P1.

## High-level architecture

```text
Browser/client (planned React + TypeScript + Vite)
  ├─ DemoTransport → local manifest + JSON/GeoJSON/image assets
  └─ ApiTransport  → planned FastAPI /api/v1 contract
                          ├─ immutable result repository
                          └─ future provider-neutral geoprocessing pipeline
                               → CDSE STAC / approved fallbacks
```

The judged path is precomputed-first and runs over local HTTP without internet. Live or semi-live processing is an enhancement and must preserve the same response schemas. The optional user-provided 3D showcase is never required for analytics.

## Planned request flow

No runtime request flow exists yet. The frozen target flow is:

```text
User selects Nagpur, an indicator, and two comparable periods
→ browser validates the selection against region capabilities
→ DemoTransport reads a local payload or ApiTransport sends POST /api/v1/comparisons
→ the contract validates region, indicator, and period fields
→ an immutable result is returned or a restricted live job is queued
→ the browser renders maps, metrics, quality evidence, provenance, and caveats
```

## Start here

| File | Purpose | Classification | What depends on it |
|---|---|---|---|
| [plan.md](plan.md) | Executable 3–4 day plan with owners, dependencies, acceptance, and fallbacks | Shared planning | Both workstreams and daily checkpoints |
| [SRS.md](SRS.md) | Testable product and non-functional requirements | Shared requirements | Architecture, tests, judging evidence |
| [contracts/openapi.yaml](contracts/openapi.yaml) | Canonical HTTP operation contract | Shared contract; Codex primary owner | Future API and generated client bindings |
| [packages/contracts/schemas/sparc.schema.json](packages/contracts/schemas/sparc.schema.json) | Canonical reusable data shapes | Shared contract; Codex primary owner | OpenAPI and mock validation |
| [docs/research/SPARC-technical-research.md](docs/research/SPARC-technical-research.md) | Evidence synthesis and recommendations | Research | ADRs and methodology |
| [docs/indicator-methodology.md](docs/indicator-methodology.md) | Reproducible formulas, QA, thresholds, limits | Scientific specification | Processing and validation |
| [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md) | Runtime boundaries and component flow | Architecture | Implementation structure |
| [docs/architecture/api-contract.md](docs/architecture/api-contract.md) | Endpoint-by-endpoint behavior and security | Architecture/contract | Frontend and backend integration |
| [docs/repository-ownership.md](docs/repository-ownership.md) | Exclusive and shared path ownership | Coordination | Conflict prevention and reviews |
| [docs/development-roadmap.md](docs/development-roadmap.md) | Day 0–4 delivery schedule | Execution | Team sequencing |
| [docs/testing-plan.md](docs/testing-plan.md) | Scientific, contract, integration, accessibility, and offline tests | Verification | Definition of done |
| [docs/demo-script.md](docs/demo-script.md) | Exact judged demonstration and recovery | Presentation | Rehearsal |

Removing a canonical requirements, contract, methodology, ownership, or test file leaves an implementation decision undefined. Other documents are indexed by topic below and cross-reference the canonical source rather than redefining it.

## Documentation map

### Research and requirements

- [Technical research](docs/research/SPARC-technical-research.md) and [source register](docs/research/source-register.md)
- [Data sources](docs/data-sources.md)
- [Open-source reuse](docs/open-source-reuse.md)
- [Indicator methodology](docs/indicator-methodology.md)
- [Validation plan](docs/validation-plan.md)

### Architecture

- [System architecture](docs/architecture/system-architecture.md)
- [Data pipeline](docs/architecture/data-pipeline.md)
- [API contract guide](docs/architecture/api-contract.md)
- [Data storage](docs/architecture/data-storage.md)
- [3D asset integration](docs/architecture/3d-asset-integration.md)
- [Offline demo strategy](docs/architecture/offline-demo-strategy.md)
- [Architecture decision records](docs/decisions/)

### Coordination and delivery

- [Repository ownership](docs/repository-ownership.md)
- [Two-developer workplan](docs/two-developer-workplan.md)
- [Frontend handoff](docs/frontend-handoff.md)
- [Integration plan](docs/integration-plan.md)
- [Git workflow](docs/git-workflow.md)
- [Development roadmap](docs/development-roadmap.md)
- [Testing plan](docs/testing-plan.md)
- [Deployment guide](docs/deployment-guide.md)
- [Risk register](docs/risk-register.md)

### Judging and viability

- [Demo script](docs/demo-script.md)
- [Judging checklist](docs/judging-checklist.md)
- [Business viability](docs/business-viability.md)
- [Presentation and Q&A](docs/presentation-and-qa.md)

## Folder ownership planned for implementation

- Codex: `apps/api/**`, `services/geoprocessing/**`, `contracts/**`, `packages/contracts/**`, `scripts/data/**`, backend/data tests, and infrastructure.
- Claude: `apps/web/**`, frontend tests, styling, UI documentation, and future 3D integration code.
- User-owned: actual files placed beneath `assets/models/earth/` and `assets/models/satellite/`.
- Shared paths have a primary owner and review rules in [docs/repository-ownership.md](docs/repository-ownership.md).

## Security baseline

- Private credentials are server-side environment variables only.
- `VITE_` values are public and may contain only non-secrets such as the API base URL and data-mode flag.
- Read-only P0 endpoints need no user authentication; future processing-job creation is restricted.
- Layer APIs resolve opaque allowlisted IDs and never fetch caller-controlled URLs.
- Raw scenes, working rasters, credentials, transient signed URLs, and unapproved model files are excluded by `.gitignore`.

## Project license

SPARC's own repository license has not yet been selected. Third-party code and data retain their original licenses and attribution requirements; see the reuse and data-source inventories before redistribution.
