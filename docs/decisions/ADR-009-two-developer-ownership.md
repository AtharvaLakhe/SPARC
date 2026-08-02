# ADR-009: Two-developer ownership

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Shared

## Context

SPARC will be implemented in parallel by two developers using separate coding agents. Contract, generated, and integration files are natural conflict points. Unclear ownership would cause merge conflicts or, more seriously, frontend and backend behavior to drift while still compiling independently.

## Decision

Use path-based primary ownership with review at shared boundaries:

- Codex owns backend, geoprocessing, contracts, server/data tests, data scripts, and infrastructure.
- Claude owns the web application, frontend tests, UI documentation, styling, and optional 3D integration code.
- Codex is the primary editor of the v1 OpenAPI and JSON Schema sources. Claude must review changes that affect browser behavior.
- The user owns the actual Earth and satellite model files. Neither developer may alter, replace, convert, or redistribute them without approval.
- `README.md`, `SRS.md`, `plan.md`, root configuration, and cross-cutting documentation are shared paths with a named editor per change.
- Contract sources freeze at the end of Day 0. Generated files are produced only from reviewed sources and are never edited by hand.
- Implementation branches use `codex/<task>` and `claude/<task>`. Daily convergence uses `integration/day-N`; only verified integration changes reach `main`.

The complete path matrix and breaking-change procedure are defined in [`../repository-ownership.md`](../repository-ownership.md) and [`../git-workflow.md`](../git-workflow.md).

## Consequences

### Positive

- Both developers can begin Day 1 independently from the same mocks.
- Reviews focus on interface boundaries rather than every internal edit.
- A contract change cannot silently land in only one workstream.
- User-provided model binaries remain outside agent ownership.

### Costs

- Small cross-cutting changes may need two reviews.
- Integration branches add one deliberate merge step.
- Contract changes after freeze require migration work even during a hackathon.

## Rejected alternatives

- **Both developers edit any path:** fast initially, but conflict-prone and impossible to audit.
- **Separate repositories:** avoids file conflicts but makes contract synchronization, demo packaging, and final submission harder.
- **Frontend-generated contract as canonical:** reverses the dependency direction and cannot fully specify HTTP behavior.
- **Backend-generated contract as an unreviewed runtime artifact:** prevents the frontend from starting on Day 0 and can hide breaking changes.

## Revisit triggers

Revisit only if the team grows beyond two implementation owners, the repository is split, or a validated code-generation workflow materially changes the shared-file boundary.
