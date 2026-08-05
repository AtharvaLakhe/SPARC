# Gemini-assisted report drafting

Gemini is an optional server-side drafting provider. It does not replace the
claim-safety gate, provenance, checksums, routing registry, or deterministic
PDF generator.

The browser sends an explicit `geminiConsent` flag. With consent, the API sends
only the selected observation text, issue codes, administrative area names,
and satellite-derived analysis context. Exact coordinates, complainant name,
address, email, phone, prior complaint history, attachments, signature and
date are appended locally after the draft returns. The PDF keeps a blank
signature line so it can be printed and signed by hand; the date is entered by
the user.

The server reads `GEMINI_API_KEY` and optional `GEMINI_MODEL`. Never put either
value in a `VITE_` variable or commit it. If a user consents but Gemini is not
configured or returns an invalid response, the API returns a safe error and
does not present the report as Gemini-completed.

Gemini is instructed to produce neutral inspection-request language. It must
not assert illegality, causation, pollution, deforestation, encroachment,
responsibility, official verification, or legal proof. Missing facts must be
shown as “Not provided”. The generated PDF contains the requested sections:
authority, complainant details, identity and contact declarations, category,
location, observations, satellite findings, limitations, concerned parties,
timeline, prior complaints, requested action, truthfulness, privacy warning,
provenance/checksums, blank signature/date, and government acknowledgement.

The request shape follows Google’s `models.generateContent` API and API-key
header guidance: [Gemini API reference](https://ai.google.dev/api) and
[API-key guidance](https://ai.google.dev/gemini-api/docs/generate-content/api-key).
