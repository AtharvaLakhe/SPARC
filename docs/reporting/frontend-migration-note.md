# Frontend migration note — jurisdiction-agnostic reporting

Claude’s browser components should consume the frozen contract rather than
recreate routing rules.

## City-picker contract

The picker reads the versioned [`data/catalog/supported-cities.json`](../../data/catalog/supported-cities.json)
catalog (currently `2026-08-05.1`) and exposes thirteen quick targets:
Nagpur, Bengaluru, Mumbai, Delhi, Chennai, Bhopal, New York, Washington DC,
Tokyo, London, Cairo, Sydney, and Reykjavik. Each card displays its ISO
country code, administrative area, boundary definition, and coverage state.
Cards with analytics coverage `FULLY_SUPPORTED` map to the two checked-in
precomputed packs. All other cards enter a report/export scope with an explicit
catalog envelope. Routing coverage is separate: only cards whose routing state
is `FULLY_SUPPORTED` may show a verified manual handoff; report-generation-only
and unsupported routing states remain export-only. The catalog envelope is not
an ADM, legal, or cadastral boundary.

The build-free Orbit launcher uses the same thirteen names for its quick chips
and local gazetteer handoff. Keep that list synchronized with the catalog when
adding a city; the launcher must not imply that a geocoded point has a
published analytical pack.

Do not reintroduce seeded or plausible-looking numeric fallback values. A
report-only city must render an unavailable analytical state and send a
`NOT_RUN`/null evidence snapshot to `POST /api/v1/reports`; the generated PDF
and ZIP remain available. This is a claim-safety requirement, not a styling
choice. `UNSUPPORTED_JURISDICTION` also suppresses guessed authority links.

## Request

`POST /api/v1/reports` accepts universal location fields:
`countryCode`, `administrativeAreas[]`, `municipality`, `district`,
`postalCode`, and `coordinates`. Use `issueCodes[]` from the universal list,
send the selected `evidence` plus `evidenceSnapshots[]`, and preserve the
dashboard’s analysis period, dataset, method, quality and provenance context.

## Response

Read `eligibility`, `coverageState`, `jurisdictionRouting`, `authorityRoutes`,
artifact descriptors, and the `X-Report-Access` response header. Keep the token
in memory only. Download `/artifacts/pdf` for the SPARC-generated report and
`/artifacts/zip` for the evidence package; the user-upload picker is for
photos, not a “PDF evidence” upload.

`FULLY_SUPPORTED` may show ranked HTTPS handoff links. `REPORT_GENERATION_ONLY`
must show the package but no unverified URL. `UNSUPPORTED_JURISDICTION` must
show export-only behaviour and never guess an authority. Manual handoff is the
only P0 submission path; do not process CAPTCHA, OTP, credentials, email,
portal scraping, or status polling.

The details step collects optional complainant name/address/contact data,
identity and contact consent, concerned parties, timeline, prior complaint
history, requested action, and a user-entered signature date. The PDF leaves
the signature line blank for printing and hand signing. Gemini consent is
explicit; sensitive details and attachments are not sent to Gemini.

## Remaining Claude work

- Replace the temporary authority select with `GET /api/v1/jurisdictions`.
- Extract `EvidenceQualityGate`, `ComplaintWizard`,
  `OfficialPortalHandoff`, and `SubmissionTracker` components.
- Add focus management, keyboard file-picker coverage, translation-key packs
  for English/Hindi/Marathi, and browser tests for coverage fallbacks.
- Keep Claude-owned styling in `apps/web/src/reporting/reporting.css`; shared
  contract changes require review from both owners.
