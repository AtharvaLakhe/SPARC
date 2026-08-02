# Security review and adopted controls

**Status:** implementation baseline  
**Scope:** contracts, immutable demo serving, planned geospatial processing, and the first read-only API slice

## 1. Context

The initial repository contained planning documents, schemas, and synthetic examples but no deployed application. The findings below were therefore contract or architecture weaknesses, not evidence of an active compromise. They matter now because implementation has started and insecure contract shapes are expensive to remove after clients depend on them.

## 2. Valid findings adopted

| Area | Confirmed weakness | Adopted control |
|---|---|---|
| Relative application URLs | Prefix-only patterns accepted protocol-relative URLs, traversal segments, encoded separators, backslashes, and control characters | Every URL-like relative field uses the same anchored, length-bounded segment pattern; IDs still resolve through registries rather than paths |
| Opaque identifiers | Length-only identifiers could carry path or delimiter syntax | IDs are length-bounded and limited to lowercase, hyphenated, optionally colon-namespaced tokens; catalogue membership remains authoritative |
| External links | `format: uri` alone did not enforce a safe browser scheme | Attribution and provenance links require HTTPS, reject whitespace/control characters, and remain length-bounded; any server fetch also requires a parsed-host allowlist |
| Dates | Schema formats alone did not guarantee real dates, ordering, supported ranges, or bounded work | Contracts constrain lexical shape; Pydantic parses real dates and server domain validation enforces order, span, season compatibility, and precomputed availability |
| OpenAPI headers/templates | `Location` and TileJSON patterns matched unsafe suffixes | Patterns are fully anchored and bounded |
| Text and collection sizes | Several response fields and arrays were unbounded | Product-appropriate maximum lengths and item counts are encoded without claiming that regexes are size limits |
| Public comparison work | An unauthenticated POST could become an unbounded processing trigger | P0 only performs bounded lookup of immutable results; live work and administrative creation remain disabled |
| Error disclosure | Future framework defaults could expose internal details | The API returns stable Problem Details and never serializes exceptions, environment values, paths, provider bodies, tokens, or signed URLs |
| Upstream raster parsing | GDAL starts parsing before SPARC's scientific logic and supports network/reference-capable drivers | The future pipeline follows the separate [pipeline hardening requirements](architecture/pipeline-hardening.md) |

## 3. Changes deliberately not adopted

- No incomplete field inventory: `geometryUrl`, `comparisonUrl`, `resultUrl`, layer URLs, and response links follow one policy and are tested together.
- No `allowed_drivers=` Rasterio example. Rasterio's documented read-time restriction is the `driver` argument; the exact behavior must be verified against the pinned Rasterio/GDAL matrix.
- No test may silently convert missing full-schema validation into a pass. Required validator dependencies fail closed in the contract gate.
- No claim that every patterned string is length-bounded. Length limits are explicit.
- No custom URL regex attempts to replace runtime URI parsing, DNS/IP checks, or an outbound-host allowlist.
- No restriction of RFC Problem Details `type` to local paths only; legitimate absolute HTTPS documentation identifiers remain possible.
- No assumption that offline presentation removes preprocessing risk. Upstream assets are still handled while the demo pack is built.

## 4. Remaining implementation risks

- The UI prototype is currently a separate static Three.js application and has no typed SPARC data gateway yet.
- The mock API proves transport and validation behavior; it does not validate scientific correctness or real Nagpur outputs.
- In-process limits are not a replacement for deployment-level request limits, timeouts, concurrency controls, and rate limiting.
- Exact GDAL drivers, resource ceilings, sandboxing, and COG range-read trade-offs must be confirmed during the pinned compatibility spike before imagery is opened.
- Browser code must treat all API strings as data, use safe DOM APIs, and re-check external-link schemes before rendering clickable links.

## 5. Security acceptance gate

- Contract examples validate under Draft 2020-12 with format checking enabled.
- Negative tests cover every identifier, relative URL, external URL, date, text, and collection category.
- OpenAPI parses, all local references resolve, and duplicate inline constraints match the canonical schema policy.
- API tests cover invalid input, unknown catalogue values, unsupported periods, disabled live mode, sanitized errors, exact CORS origins, and request-size handling.
- Secret scans include source, fixtures, browser bundles, logs, manifests, and release artifacts.
- Hostile-raster fixtures run only inside the isolated processing test environment defined by the pipeline hardening document.

