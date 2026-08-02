# Contract Examples

Every JSON file in this directory is synthetic and exists only to develop and validate interfaces before real processing. Normal responses have `meta.mock: true`; the RFC 9457 error fixture uses conspicuous `mock:` identifiers and `MOCK` text because its schema has no response envelope. All metric, date, scene, quality, and checksum values are invented.

| File | Canonical schema |
|---|---|
| `district-summary.mock.json` | `DistrictSummaryResponse` |
| `water-comparison.mock.json` | `IndicatorComparisonResponse` |
| `vegetation-comparison.mock.json` | `IndicatorComparisonResponse` |
| `built-up-comparison.mock.json` | `IndicatorComparisonResponse` |
| `lst-comparison.mock.json` | `IndicatorComparisonResponse` |
| `time-series.mock.json` | `TimeSeriesResponse` |
| `block-results.mock.json` | `BlockResultsResponse` |
| `layer-descriptor.mock.json` | `LayerResponse` |
| `processing-job.mock.json` | `JobResponse` |
| `partial-data.mock.json` | `IndicatorComparisonResponse` |
| `api-error.mock.json` | `ProblemDetails` |

Real implementation fixtures must be created by the reproducible pipeline and retain the same contract without the mock flag.
