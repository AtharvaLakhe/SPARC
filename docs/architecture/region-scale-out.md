# Scaling from one district to every district

**Status:** Future architecture proposal — not implemented, not a P0 release claim.
**Evidence reviewed:** 2026-08-04

## Current evidence boundary

The browser and contract can represent more than one region, but that is not the
same as having evidence for more than one region.

| Layer | Verified state | Constraint |
|---|---|---|
| Boundaries | The pinned geoBoundaries archive contains 735 ADM2 features (while its release metadata declares 736). Nagpur, Bengaluru Urban, and Mumbai City have passed SPARC's individual feature, geometry, CRS, state-location, provenance, and checksum gates. | Do not describe the full archive as 735 validated SPARC district boundaries. |
| Contract / API | `regionId` is opaque and the schemas can be extended without a regional special case. The current API intentionally allowlists synthetic fixtures only. | Immutable real-pack loading, unavailable-region records, and an attributable manifest are not implemented. |
| Browser | The dashboard renders the regions supplied by its transport. DemoTransport also offers generated city fixtures, visibly marked synthetic; ApiTransport does not expose those generated fixtures. | This proves client flexibility, not real-data coverage. |
| Processing evidence | Nagpur, Bengaluru Urban, and Mumbai City each have water, vegetation, and built pre-publication reports plus their documented sensitivity records. None has independent validation; Nagpur built-up remains method-blocked. | No district result is presented as legally verified or ground-truth confirmed. |

The scaling question is therefore: **how can a future screening tier add
districts without weakening the existing method, licence, validation, or
provenance gates?** It is not evidence that the project already covers India.

## What can be shared, and what cannot

Earth Engine can reuse an image collection and composite before applying zonal
statistics to a `FeatureCollection` with `reduceRegions`. This may reduce
repeated work, but the current P0 method cannot be changed to a single national
job by assertion:

- Nagpur and Bengaluru Urban use different fixed same-season windows.
- Their approved analysis CRSs differ (`EPSG:32644` and `EPSG:32643`). A shared
  reduction must either preserve the applicable grid by spatial chunk or adopt
  a new documented grid and method version.
- Source scenes, clear-observation coverage, common-valid footprint, and stop
  decisions remain district-specific.
- Export size, reducer memory, retry behaviour, and Earth Engine quotas have
  not been benchmarked for a state or national feature collection.

The current importer reads and validates one scalar summary row for a selected
approved region. It does **not** iterate a multi-district CSV keyed by
`shapeID`. Supporting that requires a new request/manifest format, per-feature
boundary bindings, deterministic error records, and tests; it is more than a
loop change.

## Proposed screening and validated tiers

These are future release tiers, not current outputs.

| Tier | Potential coverage | Required evidence | Quality policy |
|---|---|---|---|
| Screening | Districts that pass processing and coverage gates | Frozen source/product rules, scenes, coverage, threshold/method sensitivity, provenance, and an explicit unavailable outcome where a gate fails | `unknown` |
| Validated | Pilots only, unless validation capacity expands | Screening evidence plus temporally suitable independent labels, probability design, and design-consistent accuracy analysis | `low`/`medium`/`high` only as earned |

Screening answers a triage question, not an accuracy claim. A missing or
cloud-failed district must be shown as unavailable with a reason, never as no
change. A directionally stable sensitivity result is still not independent
validation.

## Prerequisites before implementation

1. Decide whether the national programme uses per-zone grids or a new approved
   equal-area analysis grid. Record that decision as a new method version; do
   not silently replace the current pilot CRSs.
2. Extend boundary extraction from its two approved features only after adding
   per-feature name, state, polygon, provenance, checksum, and licence gates.
   Resolve the archive/metadata feature-count discrepancy before publishing an
   all-district count.
3. Define a bounded batch request and response manifest. Each row must bind to
   its feature ID, region key, checksum, CRS, period group, method version,
   source scenes, coverage, and status.
4. Implement a multi-row importer that rejects duplicates, unknown feature IDs,
   checksum/CRS/method mismatches, non-finite arithmetic, and incomplete
   expected coverage. Test all of those failures.
5. Benchmark progressively — first one geographic/period/CRS chunk, then a
   state-sized run — before estimating national cost, task count, or runtime.
6. Preserve ODbL attribution and any applicable share-alike obligation for the
   selected boundary collection and every redistributed derived database.

## Future delivery sequence

```text
feature-level boundary gates
→ bounded CRS/period-group batch design
→ one-chunk Earth Engine benchmark
→ multi-row verification and unavailable records
→ immutable screening packs plus attribution manifest
→ independent validation for selected pilots
→ reviewed server-side mapping and browser delivery
```

The offline P0 bundle should continue to contain only accepted pilot artifacts.
If a future screening service fetches other immutable packs on demand, it must
retain the same data-mode, quality, provenance, and unavailable-state
disclosures. It must not turn a browser flag or generated demo fixture into a
real-data route.

## Browser evolution

The current city picker and globe overlay are useful interaction work. The
accepted Nagpur, Bengaluru Urban, and Mumbai City packs are immutable; any
other generated city values are synthetic/fallback-only. A future national index may use a
typeahead and a non-WebGL sortable table; neither should display a result until
the corresponding immutable pack has passed the appropriate screening or
validation gate.

## Risk controls

| Risk | Required control |
|---|---|
| Batch changes the pilot grid or season | Preserve the existing grid/period group, or version the method and revalidate. |
| A failed district appears as no change | Persist an explicit unavailable record and render its reason. |
| Screening is quoted as validated | Keep `quality: unknown`, show sensitivity and validation state, and prohibit stronger copy. |
| Boundary count, geometry, or licence is assumed from the archive | Run per-feature gates and retain source-specific attribution before distribution. |
| National scale cost is guessed | Benchmark bounded chunks before making cost, job-count, or performance claims. |
| Bundle becomes too large | Ship accepted pilot artifacts offline; fetch future immutable screening packs only through a reviewed path. |
