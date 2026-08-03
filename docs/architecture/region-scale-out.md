# Scaling from one district to every district

**Status:** Proposal. Processing steps are in the Codex lane and need their owner's review; the browser steps are in the Claude lane.
**Last updated:** 2026-08-03

## Why only Nagpur today

Not a UI limit and not a contract limit. Three separate reasons, only one of which is expensive:

| Layer | State | Why |
|---|---|---|
| Boundaries | **735 districts already validated** | The pinned geoBoundaries release `IND-ADM2-76128533` contains every Indian ADM2 unit and its archive checksum has passed. `extract_geoboundaries_adm2.py` writes out a *hardcoded selection* of two. |
| Contract / API | **Already region-agnostic** | `regionId` is an opaque catalogue key. plan.md's own acceptance criterion is "New region needs no contract change." |
| Browser | **Already region-agnostic** | The dashboard renders whatever `listRegions` returns; it never names a district. |
| Processing evidence | **The actual constraint** | Nagpur has water + vegetation + built-up runs. Bengaluru Urban has water only. Everything else has nothing. |

So the question is not "how do we support more districts" — the client and contract already do. It is **"how do we produce evidence for 735 districts without doing 735 districts' worth of work."**

## The one insight that makes this cheap

Earth Engine is currently driven one district at a time. It does not have to be.

A composite is computed over an *image*, and zonal statistics are computed with
`reduceRegions` over a **FeatureCollection**. The composite is the expensive part
and it is identical whether you reduce it over one polygon or seven hundred.

```
today     735 districts × 3 indicators × 2 windows  =  4,410 EE jobs
batched     1 collection × 3 indicators × 2 windows  =      6 EE jobs
by state   36 states     × 3 indicators × 2 windows  =    216 EE jobs
```

The state-chunked figure is the realistic one — a single national `reduceRegions`
export will likely exceed EE's payload and time limits, and per-state batches
also fail independently, which is what you want. Either way it is **two to three
orders of magnitude fewer jobs**, and the marginal cost of the 735th district is
close to zero.

The existing importer already verifies boundary checksum, CRS, method settings,
coverage and area arithmetic per result. It needs to iterate CSV rows keyed by
`shapeID` instead of reading a single value. That is the whole change.

## What does *not* batch

Being honest about this is the difference between a plan and a wish.

- **Coverage gates are per-district.** A district under monsoon cloud in the
  comparison window fails its common-valid gate regardless of how the job was
  submitted. Those must come back as `status: unavailable` with a reason — the
  contract and the UI already handle exactly this, and the partial fixture
  proves the path.
- **Independent validation does not batch at all.** It needs reference labels a
  human produces. This is the hard ceiling on national coverage and it drives
  the tiering below.
- **Licence does batch.** ODbL 1.0 covers the whole release, so national
  coverage adds no new licence work — the attribution already shipped is the
  attribution for all 735.

## Tiering — the honest way to cover the country

You cannot validate 735 districts, and pretending otherwise is the failure mode
this project exists to avoid. So publish two tiers and label them:

| Tier | Coverage | Evidence | `quality` |
|---|---|---|---|
| **Screening** | national, all 735 | coverage, scene counts, threshold sensitivity | `unknown` |
| **Validated** | pilots only | the above **plus** independent labels and accuracy analysis | `low`/`medium`/`high` as earned |

The client already renders this correctly: `quality: unknown` gets its own pill,
and the "No independent validation" callout already fires whenever
`independentValidationComplete` is false. **No UI work is needed to be honest at
national scale** — only to be fast at it.

Screening tier is genuinely useful on its own. "Which districts moved most on
the water proxy" is a triage question, and triage is what a screening indicator
is for.

## Sequence

**Phase 0 — unlock what exists** *(hours, no new data)*
1. Replace the hardcoded district selection in `extract_geoboundaries_adm2.py`
   with a parameter: `--districts all | <state> | <list>`. Same archive, same
   gate logic, same checksum — it already runs per feature.
2. Emit `regions.json`: one index record per district (id, name, state, bbox,
   centroid). ~735 records, roughly 60 KB gzipped.

**Phase 1 — batch the processing** *(the real work, Codex lane)*
3. Rebuild the EE step around `reduceRegions` over a per-state FeatureCollection.
   Same composites, same masks, same thresholds — only the reduction changes.
4. Extend the importer to iterate rows by `shapeID`, keeping every existing
   verification per row.
5. Districts failing a gate emit `status: unavailable` with a reason. Never drop
   them silently: a missing district and a cloudy district look identical to a
   user, and only one of them is a data problem.

**Phase 2 — serve it** *(no database)*
6. One immutable JSON per district per indicator, plus the index. Static files,
   content-addressed, CDN-cacheable. P0's "no runtime database" holds at 735
   exactly as it does at 1.
7. Offline bundle ships the index plus pilot packs; other districts fetch on
   demand. Bundling 735 packs would be a several-hundred-megabyte download for a
   demo that visits three of them.

**Phase 3 — browser** *(Claude lane)*
8. Replace the district chip list with typeahead over the index. Seven hundred
   chips is not a control.
9. Choropleth on the globe: colour every district by the selected indicator.
   This is where the per-indicator colour work already in place pays off — at
   national scale the map becomes the triage tool, not decoration.
10. Keep the non-WebGL path: a sortable table of districts ranked by change,
    which is arguably the more useful view for the screening tier anyway.

## What this changes about the demo story

Today: "here is Nagpur." After Phase 1: "here is every district in India at
screening quality, and here is Nagpur with the validation work actually done."

The second is a much stronger claim precisely because it distinguishes the two —
it demonstrates the pipeline scales *and* that the team knows what a validated
result costs.

## Risks

| Risk | Control |
|---|---|
| EE export limits at national scale | Chunk by ADM1; 36 batches fail independently |
| A district's gate failure is read as "no change" | `status: unavailable` with reason; already rendered |
| Screening tier quoted as validated | Two tiers, labelled; `quality: unknown` already surfaces |
| Offline bundle size | Ship index + pilots only; fetch on demand |
| 735 districts in one control | Typeahead + ranked table, not chips |
