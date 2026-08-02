# ADR-007: Select Nagpur as the pilot district

- **Status:** Accepted, conditional on discovery gate
- **Decision date:** 2026-08-02
- **Primary pilot:** Nagpur district, Maharashtra
- **Prepared backup:** Bengaluru Urban district, Karnataka
- **Compared:** Nagpur, Bengaluru Urban, Gurugram, and Pune
- **Scope:** one hackathon pilot; this is not a claim that the selected district is nationally representative

## Context

SPARC needs one district that can demonstrate all P0 indicators—open surface-water proxy, green-cover proxy, and built-up spectral-candidate proxy—within a short build. P1 adds March–May Landsat land-surface temperature and surface-UHI contrast.

The project has fixed the primary optical comparison periods to 2019-10-15 through 2019-12-15 and 2024-10-15 through 2024-12-15, inclusive. The P1 heat comparison uses March 1–May 15 in 2019 and 2024.

Official district geometry is intended to come from the Survey of India Administrative Boundary Database. Survey of India provides district-level administrative vector products, but the exact chosen file and redistribution terms have not yet been acquired or reviewed. ([SOI-ABDB](../research/source-register.md#soi-abdb), [SOI-CATALOG](../research/source-register.md#soi-catalog))

Sentinel-2 Level-2A and Landsat Collection 2 Level-2 products are generally discoverable through direct official STAC/data services, so the pilot does not require Google Earth Engine. District-specific clear-scene counts and common-valid coverage have not been queried. ([CDSE-STAC](../research/source-register.md#cdse-stac), [LANDSAT-STAC](../research/source-register.md#landsat-stac))

## Decision drivers

The selection prioritizes:

1. ability to tell a coherent story across water, green cover, built candidates, and heat;
2. likelihood of usable same-season optical observations;
3. clear interpretation without claiming legal, hydrological, or ecological causality;
4. manageable AOI and processing volume for a hackathon;
5. availability of an authoritative, stable district geometry;
6. a credible backup if catalog discovery fails;
7. ability to precompute a reliable offline demo without Earth Engine.

## Options considered

The table is a **planning heuristic**, not measured environmental performance. Scores are 1–5, with 5 preferred. They are explicit team judgments made before imagery acquisition.

| Criterion | Weight | Nagpur | Bengaluru Urban | Pune | Gurugram |
|---|---:|---:|---:|---:|---:|
| Multi-indicator story breadth | 25% | 5 | 4 | 5 | 3 |
| Expected fixed-window optical feasibility | 20% | 4 | 3 | 3 | 4 |
| Built/heat demonstration value | 15% | 4 | 5 | 5 | 5 |
| Interpretability for a first pilot | 15% | 5 | 4 | 3 | 4 |
| Expected processing/manageability | 10% | 4 | 5 | 3 | 5 |
| Boundary/source readiness | 10% | 4 | 4 | 4 | 4 |
| Backup/demo resilience | 5% | 5 | 5 | 4 | 4 |
| **Weighted planning score** | **100%** | **4.45** | **4.10** | **3.95** | **4.00** |

These scores must not be cited as scientific evidence. In particular, “expected optical feasibility” is an **assumption** until AOI-level SCL and QA masks are processed.

### Nagpur

**RECOMMENDATION:** select as primary because the planning team expects a balanced mix of water, vegetation, built surfaces, and urban/rural context without making the pilot solely a megacity heat demonstration. The expected balance and manageable processing are unverified assumptions.

Main risk: the fixed October–December windows may not yield sufficient common-valid coverage, and a spectral built-candidate proxy can confuse bare/dry surfaces. The latter is a known limitation of transferring NDBI-like methods beyond their original study context. ([NDBI-2003](../research/source-register.md#ndbi-2003))

### Bengaluru Urban

**RECOMMENDATION:** prepare as backup. It is expected to provide a strong built/heat narrative and a compact urban AOI, but fixed-window optical availability and a defensible rural heat reference remain unverified.

The candidate backup optical windows are 2019-01-15 through 2019-03-15 and the same dates in 2024. They are planning choices, not confirmed scene availability. They must pass the same equal-duration, same-season, common-valid-area, metadata, and license gates before being frozen; otherwise select a documented symmetric backup window or do not publish the backup comparison.

Dynamic World must not become a shortcut for this backup: it is optional and its user-derived temporal products require their own validation. ([DW-2022](../research/source-register.md#dw-2022))

### Pune

Pune remains a strong future pilot candidate because the planning team expects rich water/vegetation/built/heat contrasts. It is not first because the expected spatial heterogeneity and processing/interpretation burden are judged too high for the initial hackathon. Those are planning assumptions, not measured facts.

### Gurugram

Gurugram remains a useful built-up and heat stress-test candidate. It is not first because the planning team expects a less balanced P0 water/green story and greater risk that dry/bare surfaces will dominate the direct spectral built proxy. This remains an assumption until imagery and reference labels are inspected.

## Decision

Use **Nagpur district** for the primary implementation and documentation.

P0 targets one Nagpur subdistrict drill-down. Hingna is only the provisional candidate until the acquired boundary hierarchy, stable code, redistribution terms, source coverage, and result quality pass the gate. If no child region passes, the release must disclose the missing P0 scope rather than present an unverified boundary.

Prepare **Bengaluru Urban district** as a configuration-compatible backup using exactly the same:

- method version;
- source product levels;
- period lengths and seasonal intent;
- QA rules;
- grid-selection procedure;
- threshold governance;
- common-valid and equal-area rules;
- output schema and claim wording.

District-specific calibrated threshold values may differ only when selected from independent local calibration data and versioned explicitly. A threshold must remain fixed between 2019 and 2024 within one district analysis.

## Conditional discovery gate

Nagpur remains primary only if a direct catalog/acquisition dry run passes all critical conditions.

### P0 gate

The following cutoffs are **hackathon heuristics**, not sensor standards:

- official/versioned Nagpur geometry is acquired and usable for the intended artifact;
- required Sentinel-2 Level-2A bands, SCL, and metadata are retrievable for both fixed windows;
- at least 70% of district area is common-valid after per-pixel QA;
- median valid observation count is at least two in each period;
- processing-baseline/reflectance-offset handling succeeds for both periods;
- no unresolvable grid, metadata, or license problem exists.

Sentinel-2 direct reflectance must use metadata `BOA_ADD_OFFSET` and `QUANTIFICATION_VALUE`; a simplistic DN division is not an acceptable gate pass. ([S2-DQR](../research/source-register.md#s2-dqr))

### P1 gate

The following are **hackathon heuristics**:

- at least three usable Landsat `L2SP` acquisitions survive QA in each March 1–May 15 period;
- the urban and rural-reference zones each retain adequate valid pixels in every reported scene;
- ASTER GED gaps/cloud adjacency do not make the scene contrast spatially unrepresentative;
- surface-UHI sensitivity to rural definition does not reverse the qualitative conclusion.

USGS documents stable ST gaps where ASTER GED emissivity is missing and cloud/cloud-shadow adjacency errors. ([LANDSAT-ST](../research/source-register.md#landsat-st))

### Switch rule

Switch the entire pilot to Bengaluru Urban if Nagpur fails a critical P0 gate and the failure cannot be fixed without changing dates, product level, or scientific method. Do not cherry-pick Nagpur for one indicator and Bengaluru for another while presenting a single district story.

If both districts fail, stop the public change claim and deliver an architecture/method demonstration with clearly labelled synthetic or previously validated data; do not quietly relax QA or season matching.

## Consequences

### Positive

- One district keeps acquisition, processing, validation, and explanation tractable.
- All P0 indicators share the same Sentinel-2 observations and common-valid governance.
- The backup can use the same pipeline configuration rather than a separate implementation.
- No Earth Engine account, service credential, or runtime availability is required.

### Negative and risks

- One district cannot establish national generalizability.
- Two dates/windows cannot establish a long-term trend or causality.
- The built result remains a constrained spectral candidate proxy until a local classifier is validated.
- Cloud, crop calendar, rainfall, reservoir operations, bare soil, and rural-reference choice can dominate the apparent changes.
- A successful demo can still fail formal scientific validation.

## Rejected alternatives

### Run all four districts in P0

Rejected because it multiplies data discovery, boundary review, visual QA, threshold calibration, validation, storage, and explanation. That breadth is incompatible with a rigorous first hackathon pilot.

### Select Bengaluru Urban as primary immediately

Rejected because it would bias the first story toward built/heat outputs before confirming a balanced water and green-cover demonstration. Bengaluru Urban remains the first fallback.

### Select by scene-level cloud percentage alone

Rejected because scene metadata does not establish AOI-level clear coverage. The decision must use per-pixel QA and common-valid footprint after acquisition. Sentinel-2 provides per-pixel scene classification for this purpose. ([S2-PSD](../research/source-register.md#s2-psd))

### Use Dynamic World to avoid direct built-up methodology

Rejected as a core path because SPARC has no Google Earth Engine dependency and Dynamic World temporal products still require local validation. ([DW-2022](../research/source-register.md#dw-2022), [DW-CATALOG](../research/source-register.md#dw-catalog))

## Follow-up evidence required

The owner of data acquisition must attach the discovery manifest and gate result described in [data-sources.md](../data-sources.md). Until then, pilot feasibility is **conditionally accepted**, not empirically confirmed.
