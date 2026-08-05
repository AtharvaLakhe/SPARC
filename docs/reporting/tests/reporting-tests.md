# Reporting test plan

## Contract tests

- Parse OpenAPI 3.1 and resolve every external schema reference.
- Validate `report.mock.json` and `authorities.mock.json` against the canonical schema.
- Reject unbounded strings/arrays, off-site URLs, traversal IDs, unsafe report IDs, and invalid SHA-256 values.
- Verify mock responses expose `meta.mock: true`.

## Domain tests

- Route each issue-code family to the expected primary and optional secondary authority.
- Require municipal confirmation before NMC primary routing.
- Require manual selection for unknown issues and NGT escalation.
- Allow numeric wording only for formal validated evidence.
- Force verification-only wording for exploratory/unknown quality.
- Block numerical and directional claims when built-up methods conflict.

## Artifact and integrity tests

- Generate PDF/ZIP twice and compare stable hashes.
- Verify manifest byte lengths and SHA-256 values, PDF/ZIP descriptor checksums,
  and the packaged `provenance.json` entry.
- Verify deterministic ZIP ordering and timestamps.
- Reject path traversal, duplicate names, unsafe names, malformed images/PDFs,
  MIME spoofing, SVG, executable files, nested archives, oversized files, and
  oversized image dimensions.
- Confirm EXIF is absent after JPEG/PNG normalization.
- Confirm English, Hindi, and Marathi translation keys are complete.

## API/security tests

- Create, read, download, hand off, acknowledge, expire, and delete a report.
- Require the report access token and reject guessed or mismatched tokens.
- Return `410` after expiry and remove temporary artifacts.
- Reject unallowlisted authorities, open redirects, automatic submission attempts, and unconfirmed handoffs.
- Preserve problem+json responses without tokens, credentials, paths, or stack traces.
- Enforce attachment and request limits and report-level rate limits.
- Ensure acknowledgements are explicitly marked `USER_ENTERED`.

## Integration acceptance

The complete P0 flow must run offline using marked synthetic evidence and must
produce a neutral PDF/ZIP, a ranked route, an allowlisted manual URL, and a
user-entered acknowledgement without changing any browser-owned file.

## Jurisdiction-pack coverage tests

- India/Maharashtra exact municipality routes NMC before state/national fallbacks.
- Karnataka routes KSPCB; US routes EPA; England routes Environment Agency;
  Northern Ireland routes DAERA.
- Unsupported countries return `UNSUPPORTED_JURISDICTION` with export-only
  fallback and no guessed authority.
- Recognized but unmatched areas return `REPORT_GENERATION_ONLY` with no
  unverified submission URL.
- Registry validation rejects stale records, invalid country/issue codes,
  duplicate IDs, missing official sources, and insecure URLs.
- Emergency classification preserves the explicit “SPARC is not an
  emergency-reporting service” instruction.
