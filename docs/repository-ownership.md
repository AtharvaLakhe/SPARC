# Repository ownership

**Status:** Day 0 coordination baseline  
**Applies from:** contract freeze at the end of Day 0

Ownership means responsibility for correctness and first review. It is not permission to bypass the other workstream when a change alters a shared interface.

## Ownership matrix

| Path | Classification | Primary owner | Direct edits by other owner | Required review | Generated-file rule |
|---|---|---|---|---|---|
| `apps/api/**` | Server/backend | Codex | Only after assignment | Codex; Claude if response behavior changes | Generated server models, if adopted, come from canonical schemas |
| `services/geoprocessing/**` | Server/data processing | Codex | No, except paired fixes | Codex | Derived artifacts go under ignored data paths, never beside source |
| `scripts/data/**` | Build/data tooling | Codex | No, except paired fixes | Codex | Scripts may generate data; generated outputs declare source/version |
| `contracts/**` | Shared HTTP contract | Codex | Proposal or paired edit only | Both for browser-visible changes | OpenAPI/examples are reviewed sources, not generated output |
| `packages/contracts/schemas/**` | Shared data contract | Codex | Proposal or paired edit only | Both | Canonical JSON Schema source; never overwrite from a runtime model without review |
| future `packages/contracts/generated/**` | Shared build artifact | Codex runs generator | Never by hand | Both through source diff | Header must name source, generator/version, and command |
| `apps/web/**` | Browser/client | Claude | Only after assignment | Claude; Codex if server assumptions change | Generated API types are imported, not copied |
| `tests/frontend/**` | Browser/client tests | Claude | Only after assignment | Claude | Snapshots are regenerated through the test tool and reviewed |
| `docs/mockups/**` and UI docs | Design/frontend | Claude | Only after assignment | Claude | Exported images identify source and may not contain secrets |
| future 3D integration code | Browser/client | Claude | Only after assignment | Claude | Must consume user assets through the documented adapter/fallback |
| `tests/api/**`, `tests/processing/**`, `tests/contract/**` | Server/shared tests | Codex | Claude may add a failing contract case | Codex; both for contract fixtures | Test fixtures must validate against canonical schemas |
| `tests/integration/**` | Shared integration | Assigned per scenario | Only with coordination | Both | Do not record live tokens, signed URLs, or provider responses |
| `infra/**` | Build/deployment | Codex | Proposal only | Codex; Claude reviews web build assumptions | Generated deployment metadata is reproducible and secret-free |
| root planning files and `docs/**` not listed above | Shared documentation | Assigned editor per pull request | Yes, after announcing scope | Relevant domain owner | No generated prose |
| root dependency lockfiles and workspace config | Shared build/configuration | Developer introducing the change | Only one active editor | Both | One tool invocation owns each lockfile update |
| `.env.example` | Shared configuration | Codex | Proposal only | Both | Names and safe examples only; never real values |
| `data/raw/**`, `data/interim/**`, `data/processed/**`, caches | Local/generated data | Codex | Read only when needed | Codex | Ignored; manifest/checksum metadata may be committed separately after review |
| `data/demo/**` | Shared demo artifact | Codex produces; Claude consumes | Claude may not alter numeric results | Both | Immutable, versioned, checksum-recorded; values cannot be hand-tuned in UI |
| `assets/models/earth/**`, `assets/models/satellite/**` | User-provided binary assets | User | No agent direct modification | Explicit user approval | Keep payloads uncommitted until format, license, and size are approved |

## Planned repository layout

```text
/
├── apps/
│   ├── api/                  # planned FastAPI service
│   └── web/                  # planned React/Vite browser application
├── services/geoprocessing/   # provider-neutral processing library
├── packages/
│   ├── contracts/            # canonical schemas and future generated types
│   └── config/               # future shared, non-secret build conventions
├── data/
│   ├── boundaries/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── demo/
├── assets/models/
│   ├── earth/[USER_PROVIDED_EARTH_MODEL]
│   └── satellite/[USER_PROVIDED_SATELLITE_MODEL]
├── contracts/                # OpenAPI and mock examples
├── docs/                     # research, architecture, decisions, coordination
├── scripts/data/             # reproducible acquisition/build commands
├── tests/                    # api, processing, contract, integration, frontend
└── infra/                    # minimal deployment definitions
```

Directories that do not yet exist are an implementation target, not evidence of current code. The planning phase does not create empty application or asset directories.

## Shared-file protocol

Before editing a shared path, the developer posts the file list and purpose in the active pull request or coordination channel. One developer is the editor until that change merges. The other reviews rather than making a competing branch edit.

A shared change is complete only when:

1. canonical source and examples agree;
2. both affected workstreams have adapted;
3. contract and integration checks pass;
4. migration or regeneration notes are present; and
5. the daily integration branch remains runnable in demo mode.

## Contract ownership and freeze

The v1 contract consists of `contracts/openapi.yaml`, `packages/contracts/schemas/sparc.schema.json`, and the mock payloads under `contracts/examples/`. It freezes at the end of Day 0 after both developers can load the same examples.

After freeze:

- an additive optional field needs a contract proposal, both reviews, examples, and tests;
- a newly required field, removed/renamed field, narrower enum, changed unit, or changed meaning is breaking;
- a breaking change requires a change record, schema-version decision, both implementations in the same integration window, regenerated bindings, and migration notes;
- emergency demo fixes prefer an adapter or feature flag over a breaking contract edit.

## Secrets and environment ownership

Codex owns server variable names and secret-loading behavior. Claude owns documented public browser configuration. Any `VITE_*` value is delivered to the browser and therefore cannot be a secret. Provider credentials remain server-only and are never copied into mocks, screenshots, test recordings, frontend code, or deployment output.

## What removal would break

Removing this file would remove the conflict-avoidance policy, shared review boundary, generated-file ownership, model-asset protection, and contract change authority. The two workstreams would no longer have a reliable way to decide who may edit a path.
