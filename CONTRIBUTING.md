# Contributing to SPARC

SPARC is currently contract-first and documentation-led. The repository does not yet contain application code. Read [the ownership rules](docs/repository-ownership.md), [Git workflow](docs/git-workflow.md), and [API contract](docs/architecture/api-contract.md) before opening a change.

## Non-negotiable rules

- Do not describe SPARC outputs as official UN SDG indicators. Use **satellite-derived proxy indicator**, **environmental decision-support indicator**, or **satellite-derived local progress signal**.
- Do not claim causation from a before/after association.
- Do not call NDVI forest cover or forest loss, Sentinel-2 a thermal sensor, surface temperature air temperature, or precomputed data live data.
- Never commit secrets, raw provider credentials, transient signed URLs, unrestricted upstream URLs, raw satellite scenes, or user-provided model binaries without explicit approval.
- Preserve citations, provenance, licenses, quality warnings, and effective spatial resolution when changing scientific content.
- Do not edit generated contract bindings manually. `contracts/openapi.yaml` and the canonical schemas in `packages/contracts/schemas/` control future generation.

## Branches and commits

- Codex work: `codex/<short-task>`
- Claude work: `claude/<short-task>`
- Temporary checkpoint work: `integration/day-N`
- Commits use an imperative subject and an optional scope, for example `docs(api): freeze comparison contract`.
- Keep commits single-purpose. Data, generated artifacts, and source changes must not be mixed without a clear reason.

`main` is the releasable branch. The Day 0 contract and ownership pull request merges before frontend or backend implementation branches. See [docs/git-workflow.md](docs/git-workflow.md) for merge order and breaking-change handling.

## Pull-request checklist

- [ ] The change stays within the author's owned paths or includes the required owner review.
- [ ] Contract changes update schemas, OpenAPI operations, examples, and migration notes together.
- [ ] New factual claims have primary or peer-reviewed citations and an access date.
- [ ] Recommendations and prototype heuristics are labelled as such.
- [ ] User-facing scientific text includes limitations and provenance.
- [ ] No secret, raw scene, unapproved boundary, or 3D model payload was added.
- [ ] Relevant documentation, contract, security, accessibility, and offline checks pass.
- [ ] The primary Nagpur path and Bengaluru Urban backup remain usable.

## Contract changes

The v1 contract freezes at the end of Day 0. After that point:

1. Additive optional fields and new endpoints require contract-owner review and updated examples.
2. A breaking change requires a written change record, approval from both workstreams, a schema-version increment, regenerated bindings, updated mocks, and migration notes.
3. Frontend and backend code must consume one canonical contract; parallel handwritten models are prohibited.

## Research and attribution

Every substantial factual claim must identify its source, author or organization, publication/update date when available, access date, URL, and the decision it supports. Do not copy long passages. Record dependency and dataset licenses in [docs/open-source-reuse.md](docs/open-source-reuse.md) and [docs/data-sources.md](docs/data-sources.md).

## Testing expectations

Documentation changes are checked for required files, local links, citations, terminology, Mermaid syntax, and secret patterns. Future application changes must additionally run the checks assigned in [docs/testing-plan.md](docs/testing-plan.md).

