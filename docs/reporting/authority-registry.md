# Authority registry and routing rules

**Registry version:** `2026-08-05`
**Verification policy:** recheck official URLs and portal requirements before any non-demo use

The registry is an allowlist for manual handoff. A URL in this document is not
permission for SPARC to submit, proxy, scrape, or automate the destination.

The implementation is jurisdiction-agnostic. Pack data lives under
`apps/api/reporting/jurisdictions/{countryCode}/`; the validated set is
India/Maharashtra (including the migrated MPCB, NMC, Maharashtra Forest,
Aaple Sarkar, CPGRAMS and NGT records), India national/CPCB, Karnataka/KSPCB,
US EPA plus California, England/Environment Agency, Northern Ireland/DAERA,
and a generic export-only fallback. This is limited coverage, not global
authority coverage.

Each pack records `countryCode`, administrative areas, municipality/district,
issue codes, channels, identity requirements, language support, emergency
instructions, official source and HTTPS handoff URL, verification status and
dates, coverage state, and adapter. Run
`python scripts/data/validate_jurisdiction_registry.py` before release. It
rejects malformed country codes, stale records, missing source URLs, invalid
issue codes, unverified URLs marked as verified, and insecure URLs.

| ID | Primary scope | Route | Portal controls | Official source |
|---|---|---|---|---|
| `mpcb` | Maharashtra air, water, industrial, noise and hazardous-waste pollution | Primary for pollution issues | User-operated portal/office route; no SPARC API | [MPCB FAQ](https://www.mpcb.gov.in/en/faq), [complaint SOP](https://www.mpcb.gov.in/en/node/6132) |
| `nmc` | Nagpur municipal sewage, waste, drains, civic nuisance and municipal lakes | Primary only after municipal limits are confirmed | Current form begins with mobile OTP | [NMC complaint form](https://nmcnagpur.gov.in/grievance/complaint_form.php) |
| `maharashtra-forest` | Forest land, tree-felling, wildlife and forest encroachment | Primary for forest issues | Manual department route | [Maharashtra Forest](https://mahaforest.gov.in/home/index/en), [contact](https://mahaforest.gov.in/fcawebsite/contactus) |
| `aaple-sarkar` | Maharashtra state grievance and escalation | State default or secondary escalation | Portal authentication remains user-operated | [Aaple Sarkar](https://aaplesarkar.mahaonline.gov.in/), [contact](https://aaplesarkar.mahaonline.gov.in/en/CommonForm/ContactUs) |
| `cpgrams` | Eligible central/state public-service grievance escalation | Central escalation route | Registered user portal; email is not a submission route | [CPGRAMS home](https://pgportal.gov.in/), [lodge grievance](https://pgportal.gov.in/Home/LodgeGrievance), [contact](https://pgportal.gov.in/Home/ContactUs) |
| `ngt` | Legal/judicial environmental forum | Escalation/reference only | No automated filing | [National Green Tribunal](https://www.greentribunal.gov.in/) |

## Coverage behaviour

- `FULLY_SUPPORTED`: ranked verified authorities and an HTTPS allowlisted handoff URL.
- `REPORT_GENERATION_ONLY`: PDF/evidence ZIP are available, but no unverified submission link is shown.
- `UNSUPPORTED_JURISDICTION`: the report remains local/exportable and no authority is guessed; SPARC is not an emergency-reporting service.

Routing priority is exact municipality, state/province regulator, national
authority, escalation authority, then export-only fallback. `Open311Adapter`
is only available when a verified official endpoint is present; P0 uses
`ManualPortalAdapter` and never automates CAPTCHA, OTP, login, email, scraping,
or status polling. Adapter interfaces are in
`apps/api/reporting/submission_adapters.py`.

## Routing constraints

1. Return one ranked primary route and zero to three optional secondary routes.
2. Never generate duplicate submissions automatically.
3. Never infer NMC jurisdiction from a district boundary alone.
4. Treat NGT as legal escalation/reference only; SPARC does not generate a legal pleading.
5. Require manual selection when the issue or jurisdiction is ambiguous.
6. Display the registry verification date and require re-verification when a record is stale.

## Issue-code mapping

| Issue code | Primary | Optional secondary |
|---|---|---|
| `pollution.air`, `pollution.water`, `pollution.industrial`, `pollution.noise`, `waste.hazardous` | MPCB | NMC only when municipal jurisdiction is confirmed and relevant |
| `municipal.sewage`, `municipal.waste`, `municipal.drain`, `municipal.lake`, `municipal.encroachment` | NMC after confirmation | MPCB for pollution-related cases |
| `forest.land`, `forest.tree_felling`, `forest.wildlife`, `forest.encroachment` | Maharashtra Forest | Aaple Sarkar |
| `state.grievance`, `state.escalation` | Aaple Sarkar | CPGRAMS |
| `central.grievance` | CPGRAMS | None by default |
| `legal.escalation` | None | NGT, manual and legal-advice warning |
