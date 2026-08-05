# Privacy, safety and legal policy

## User control

The user must explicitly confirm that they reviewed the package, believe the
observation is truthful, consent to sharing the exact location and attachments,
and understand that submission is manual.

Contact information is optional and is included only after an explicit choice.
It is never logged. P0 reports are anonymous, device-scoped, stored in a private
temporary workspace, and deleted after 24 hours. No backup or shared cache is
allowed.

Gemini drafting is an explicit opt-in. The server sends selected report text and
non-identifying analysis context only; names, addresses, contacts, exact
coordinates, attachments, signatures and dates are appended locally after the
draft. The Gemini key is server-only and is never placed in browser code.

## Required warnings

> This package records an observation and request for verification. It does not prove a violation, identify a responsible party, or provide legal advice.

> Review every fact before manual submission. SPARC does not submit complaints, bypass CAPTCHA or OTP, or store government credentials.

> Include personal details, exact location, and attachments only when you consent to sharing them.

The boundary disclaimer is included in every report and ZIP manifest. Satellite
proxies do not prove causation, legal status, pollution responsibility, forest
loss, or cadastral ownership.

Reporting is jurisdiction-agnostic at the report-generation layer. Authority
routing is limited to the verified packs documented in
`docs/reporting/authority-registry.md`; SPARC does not claim global coverage.
For `REPORT_GENERATION_ONLY` and `UNSUPPORTED_JURISDICTION`, users can export
the package but SPARC does not guess a destination. SPARC is not an
emergency-reporting service; imminent threats must use local emergency
services and the instructions in the applicable official registry record.

## Security controls

- HTTPS and explicit CORS in deployed environments.
- High-entropy report access token required for reads, downloads, handoff, acknowledgement, and deletion.
- Tokens never appear in URLs, logs, manifests, PDFs, or screenshots.
- Strict allowlisted HTTPS authority URLs; no open redirects or SSRF.
- Bounded request body, text, image, attachment, ZIP, and report rates.
- ZIP-slip, executable, SVG, decompression-bomb, MIME-spoofing, and control-character rejection.
- No cookies or government credentials in P0.
- Production P1 requires encrypted private storage, RBAC, audit-log protection, configurable retention, and deletion jobs.

## Audit events

P0 records only non-personal event metadata: created, validated, artifact-generated,
downloaded, handoff-recorded, acknowledgement-recorded, expired, and deleted.
The external acknowledgement is marked `USER_ENTERED`; SPARC never claims that
an authority accepted or verified it.

Production deployment requires privacy/legal review before collecting contact
details or retaining reports beyond the P0 temporary window.
