# Reporting evidence and artifact specification

## Required evidence binding

Every report binds `regionId`, exact longitude/latitude, boundary source and
licence, attribution, boundary SHA-256, boundary disclaimer, indicator,
baseline/comparison/value/unit, method ID/version, processing-run ID, evidence
checksum, quality status, validation status, user observation, language,
consent, and authority route.

The boundary disclaimer is mandatory:

> This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.

For a city with no accepted Earth Engine pack, the boundary record is an
explicit WGS84 catalog centroid/bbox envelope with a checksum and
`status: CATALOG_ONLY`. It is a report/export scope aid, not an ADM, municipal,
legal, or cadastral polygon. The evidence snapshot must use null values,
`methodId: not-run`, `validationStatus: NOT_RUN`, and `qualityLevel: unknown`.
Those records may generate the PDF and ZIP but must not display fabricated
satellite-derived numbers.

## Claim modes

| Evidence state | Generated wording |
|---|---|
| `FORMAL_PASSED` and stable quality | Neutral proxy value plus limitations |
| `EXPLORATORY_ONLY`, `NOT_RUN`, low or unknown | Request for verification only |
| Conflicting methods | No numerical or directional indicator claim |
| Current Nagpur built-up conflict | Indicator blocked |

User text is labelled as a user observation. It is never converted into a
finding of illegality, causation, pollution source, or responsible party.

## Artifacts

Top-level names are `report-{reportId}.pdf` and `evidence-{reportId}.zip`.
The ZIP contains the PDF, boundary GeoJSON, before/after PNGs,
`provenance.json`, `manifest.json`, and sanitized user attachments.

Manifest entries contain path, media type, byte length, and SHA-256 for every
packaged data file. The response artifact descriptors carry SHA-256 checksums
for the PDF and final ZIP; the manifest descriptor carries the checksum of its
canonical bytes. JSON is canonical UTF-8 with sorted keys and a trailing
newline. ZIP entry order and timestamps are fixed for reproducibility.

Limits are six attachments, 5 MiB per attachment, 20 MiB combined attachments,
25 MiB generated ZIP, 4,000 characters of user observation, and 8,192 pixels
per image dimension. Accepted user files are JPEG, PNG, and PDF. Images are
decoded and re-encoded without EXIF metadata. The browser may submit the
checksum of the selected upload; the API accepts that input checksum, then
records the checksum of the normalized bytes that actually enter the package.
Archives, SVG, executables,
remote URLs, traversal names, and malformed files are rejected.

## Provenance

`provenance` records the boundary checksum, indicator method/version,
processing-run ID, evidence checksum, locale, eligibility decision, and source
records. Generated artifacts do not include provider credentials, signed URLs,
machine paths, or unredacted request headers.
