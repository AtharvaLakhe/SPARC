# SPARC Shared Contracts

This directory contains specifications only. It does not contain generated TypeScript or Python application code.

## Canonical sources

- `schemas/sparc.schema.json` is the canonical JSON Schema 2020-12 document for reusable request and response data shapes.
- `../../contracts/openapi.yaml` is the canonical OpenAPI 3.1 operation contract and references definitions in the schema document.
- `../../contracts/examples/` contains synthetic payloads used for contract validation and frontend development.

Future TypeScript and Pydantic bindings must be generated from a bundled copy of the OpenAPI document with a pinned tool version. Generated files must carry a header naming the source contract and tool version and must never be edited by hand.

## Versioning

`meta.schemaVersion` follows semantic versioning independently of `/api/v1` path versioning:

- Patch: clarifications that do not alter validation.
- Minor: additive optional fields or new enum-independent operations.
- Major: removed/renamed fields, newly required fields, changed meaning, narrowed enums, or incompatible units.

The v1 contract freezes at the end of Day 0. Breaking changes require both workstream owners, updated examples, regenerated bindings, migration notes, and a schema-version increase.

## Mock rules

Every normal response example has `meta.mock: true`; RFC 9457 error examples instead use conspicuous `mock:` identifiers and `MOCK` text because Problem Details does not carry response metadata. All example values are invented interface fixtures, not environmental findings about Nagpur, Bengaluru Urban, or any other location.
