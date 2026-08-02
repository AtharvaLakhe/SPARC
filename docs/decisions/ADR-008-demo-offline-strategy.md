# ADR-008: Local-HTTP, precomputed offline demo as the primary recovery path

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Shared
- **Applies to:** Demonstration packaging, live fallback, local serving and rehearsal

## Context

The event environment may have unreliable internet, blocked ports, API outages, provider authentication failures, quota limits, a failed backend deployment, unavailable tiles or incompatible WebGL. A prototype that works only after remote processing does not meet the required reliability or completeness standard.

The same result cannot be duplicated in a separate bespoke offline UI without creating contract drift. The local path also cannot rely on opening an ES-module application with `file://`, because browser origin, routing, fetch and service-worker behavior differ from an HTTP origin.

## Decision drivers

- Complete primary and backup story with the network disabled.
- One UI and response schema for live and precomputed data.
- Fast, rehearsable startup on the presentation laptop.
- Integrity and provenance of packaged scientific results.
- No hidden provider, CDN, font, tile or database dependency.
- Clear disclosure that data are precomputed.

## Decision

1. Build a self-contained static Vite application and versioned primary/backup demo packs.
2. Serve the bundle through a packaged, tested local HTTP launcher bound to loopback by default. The exact launcher is chosen during implementation for the presentation OS and must require no event-day installation or internet access.
3. `file://` is not an accepted primary or backup launch method.
4. Implement `ApiTransport` and `DemoTransport` behind the same typed frontend repository. Both return schemas defined by the OpenAPI contract.
5. Resolve supported demo requests through a manifest keyed by canonical request parameters; do not calculate or fabricate unsupported values in the browser.
6. Include immutable JSON, GeoJSON, PNG/WebP and bounded XYZ assets, local fonts/icons, attributions, checksums and exact launch instructions.
7. Show an always-visible `Precomputed demo data` state with generation date, periods, provenance, quality and warnings.
8. Automatic live-to-demo fallback is allowed only for defined connectivity, timeout or service-unavailable states and must be disclosed. It is forbidden for invalid input, authorization, contract mismatch or integrity failure.
9. Do not prefetch/package public OpenStreetMap standard tiles. Use an expressly licensed bundled context layer, a neutral background, or no basemap.
10. Treat a service worker as optional defense in depth after update/cache tests, not as the sole offline copy or launch mechanism.
11. Provide static map imagery plus metrics/table/provenance when WebGL or an interactive layer fails. Optional 3D never participates in the critical path.

## Required package

The release includes:

- built application shell and local runtime assets;
- `demo/v1/manifest.json` with schema/data/app versions;
- primary and backup region, comparison, indicator, layer and provenance payloads;
- every asset's relative path, media type, byte size and SHA-256;
- data/library notices and visible attribution data;
- a read-only local HTTP launcher and tested instructions;
- a full-bundle checksum file; and
- no secrets, `.env` files, raw scenes, temporary signed URLs or required remote origins.

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Remote live stack only | Most dynamic demonstration | Internet/provider/backend/tile chain has many independent failure points | Rejected |
| Hosted frontend with cached API | Simple normal deployment | Venue internet and backend remain required; caches may be cold/stale | Insufficient alone |
| `file://` static build | No launcher process | Module, routing, fetch, origin and storage behavior is unreliable/restricted | Rejected |
| Service worker only | Seamless offline after a successful visit | Cold start/update/cache-version risks and secure-origin/lifecycle complexity | Optional secondary layer only |
| Local HTTP plus immutable demo pack | Browser-realistic origin, complete offline story, inspectable assets | Requires launcher packaging and rehearsal | **Selected** |
| Local FastAPI demo server | Same HTTP routes can be served exactly | Python/native environment adds startup failure for a static demo | Optional secondary path, not primary |

## Consequences

### Positive

- The full P0 story survives internet, catalog, backend and database outages.
- Frontend work begins from contract-valid examples before backend implementation.
- Local HTTP closely matches deployed browser origin/fetch behavior.
- Immutable manifests and hashes make rehearsal copies verifiable.

### Negative and trade-offs

- Demo mode supports only pre-approved parameter combinations.
- Precomputed results may be stale and require visible dates/caveats.
- Bundle size must be bounded and raw scenes excluded.
- The launcher and backup devices become release artifacts that require testing.
- Automatic fallback logic needs strict classification to avoid misleading substitution.

## Release gates

- Complete primary and backup journeys with network disabled from a cold browser profile.
- Validate OpenAPI, examples, JSON/GeoJSON, manifest paths, hashes, media types, layer bounds, legends and attributions.
- Confirm there are no required remote requests for code, fonts, icons, maps, models or data.
- Test API-down, corrupt asset, missing layer, WebGL-off, reduced-motion and optional-3D failure.
- Confirm mode/generation/provenance disclosure on every analytical view.
- Keep at least two immutable verified copies on separate devices/media.
- Re-run the full checklist after any bundle change; do not patch a verified copy in place.

## Security implications

- Bind to loopback and serve one fixed directory read-only; disable directory listing, uploads and execution.
- Resolve opaque IDs through the manifest; reject traversal and unlisted media types.
- Keep all provider credentials server-side and out of Vite variables/static assets.
- A checksum mismatch is a hard integrity error and must not render as a valid result.
- Mock examples are visibly marked and cannot be presented as processed evidence.

## Reversal conditions

Offline precomputation remains required for the event even if the live deployment proves stable. A future production product may make live/cache mode primary, but downloadable/versioned resilience packs can be reconsidered only with an equivalent tested continuity plan and truthful freshness communication.

## Sources

Official sources were accessed on 2026-08-02.

- [Vite static deployment guide — Vite project](https://vite.dev/guide/static-deploy.html). Static build/deployment model and preview-server scope.
- [Service Workers specification — W3C](https://www.w3.org/TR/service-workers/). Lifecycle, fetch interception and cache behavior.
- [Secure Contexts specification — W3C](https://www.w3.org/TR/secure-contexts/). Potentially trustworthy loopback origins.
- [OpenStreetMap tile usage policy — OpenStreetMap Foundation](https://operations.osmfoundation.org/policies/tiles/). Public service attribution, no-SLA and prohibited bulk/offline download behavior.
- [OpenAPI Specification 3.1.2 — OpenAPI Initiative](https://spec.openapis.org/oas/v3.1.2.html). Shared live/demo schema definition.
- [WCAG 2.2 — W3C](https://www.w3.org/TR/WCAG22/). Accessible status, alternatives and keyboard operation.

