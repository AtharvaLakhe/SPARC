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

The original documentation draft was re-frozen as `1.0.0-alpha.1` when implementation began. Its validation was tightened before any deployed consumer existed; all committed examples remained compatible. After the first integrated client release, further breaking changes require both workstream owners, updated examples, regenerated bindings, migration notes, and a version decision.

## Validation

The contract gate requires its validator dependency and fails rather than silently skipping full validation:

```powershell
python -m pip install -r apps/api/requirements-dev.txt
python -m unittest discover -s tests -p "test_*.py"
```

The gate validates every example with JSON Schema format checking, resolves every OpenAPI reference, tests unsafe identifiers/URLs, and recursively checks object closure and explicit string/collection bounds.

## Mock rules

Every normal response example has `meta.mock: true`; RFC 9457 error examples instead use conspicuous `mock:` identifiers and `MOCK` text because Problem Details does not carry response metadata. All example values are invented interface fixtures, not environmental findings about Nagpur, Bengaluru Urban, or any other location.
