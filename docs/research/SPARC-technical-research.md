# SPARC technical research synthesis

**Status:** complete for hackathon planning; empirical data-discovery and validation work remain open  
**Research date:** 2026-08-02  
**Evidence cut-off/access date:** 2026-08-02  
**Primary pilot:** Nagpur district  
**Backup:** Bengaluru Urban district

## Executive result

SPARC can produce a defensible hackathon demonstration if it presents the outputs as **satellite-derived proxies**, keeps the periods season-matched, compares only the common valid footprint, and exposes uncertainty instead of promising authoritative environmental inventories.

The recommended scope is:

| Priority | Indicator | Prototype decision | Resolution claim | Public wording |
|---|---|---|---:|---|
| P0 | Open surface water | Sentinel-2 L2A MNDWI | 20 m | open surface-water area proxy |
| P0 | Green cover | Sentinel-2 L2A NDVI | 10 m | green-cover proxy |
| P0 | Built-up | constrained Sentinel-2 NDBI with water/vegetation guards | 20 m | built-up spectral-candidate proxy |
| P1 | Surface heat | USGS Landsat 8/9 Collection 2 Level-2 `ST_B10` | 100 m thermal support on a 30 m product grid | land-surface temperature and surface-UHI contrast |

Sentinel-2 band resolutions and Level-2A product semantics come from the mission product specification. Landsat's Level-2 guide documents the thermal product's native support, distributed grid, scale, and QA. ([S2-PSD](source-register.md#s2-psd), [LANDSAT-L2-GUIDE](source-register.md#landsat-l2-guide))

Dynamic World is useful optional context but must not be required by the indicator or released demo. It may be queried only through the offline Earth Engine worker. JRC Global Surface Water, ESA WorldCover, and GHSL are dated corroboration or validation-stratification products, not ground truth. Their own documentation records product-specific validation and comparability limitations. ([DW-2022](source-register.md#dw-2022), [GSW-2024](source-register.md#gsw-2024), [WORLDCOVER-PUM](source-register.md#worldcover-pum), [GHSL-2023](source-register.md#ghsl-2023))

## Research question

What is the smallest scientifically defensible method set that can show district-scale environmental change in a 3–4 day hackathon without a proprietary processing dependency, while preserving a credible production path?

## Evidence method

Research was limited to:

1. current mission/product-owner specifications and legal notices;
2. current government/JRC/ESA/USGS data access pages;
3. original peer-reviewed index, dataset, and validation papers;
4. authoritative open-source project license files.

Secondary tutorials, copied formulas without original attribution, threshold lists, vendor claims, and search snippets were excluded as evidence. The complete bibliographic and provenance record is [source-register.md](source-register.md).

Evidence labels used across the documentation:

- **FACT:** supported by a registered primary/peer-reviewed source.
- **DECISION:** selected SPARC scope or governance rule.
- **RECOMMENDATION:** preferred implementation choice based on the evidence and hackathon constraints.
- **HEURISTIC:** configurable prototype value with no universal validity.
- **ASSUMPTION:** not yet verified from acquired data or local reference evidence.

## Fixed pilot design

### Geography

**DECISION:** Nagpur is primary and Bengaluru Urban is backup. Pune and Gurugram were considered. Selection is conditional on a direct catalog and QA dry run; no district-specific imagery inventory has yet been created. See [ADR-007](../decisions/ADR-007-pilot-district.md).

The prototype district geometry source is the pinned geoBoundaries gbOpen India ADM2 release `IND-ADM2-76128533`. The source-specific India release metadata records ODbL 1.0, despite the collection-level gbOpen CC BY 4.0 description, so SPARC follows ODbL attribution and applicable share-alike obligations. It is suitable for prototype analysis but is not an authoritative legal or cadastral boundary. No Survey of India geometry is used or redistributed. ([GBOPEN-IND-ADM2](source-register.md#gbopen-ind-adm2))

### Periods

- **P0 baseline:** 2019-10-15 through 2019-12-15 inclusive.
- **P0 comparison:** 2024-10-15 through 2024-12-15 inclusive.
- **P1 heat baseline:** 2019-03-01 through 2019-05-15 inclusive.
- **P1 heat comparison:** 2024-03-01 through 2024-05-15 inclusive.

These are project decisions. They support like-for-like seasonal comparison but do not establish a trend, causal effect, or long-term climate signal.

### Data access

**DECISION:** use the current Copernicus Data Space STAC endpoint for Sentinel discovery and USGS STAC/EarthExplorer for Landsat. CDSE documents `https://stac.dataspace.copernicus.eu/v1/` as the current endpoint after deprecation of the legacy endpoint in November 2025. USGS documents Collection 2 COG/STAC and EarthExplorer access. ([CDSE-STAC](source-register.md#cdse-stac), [LANDSAT-STAC](source-register.md#landsat-stac))

No browser, API request, or released-demo path may require Earth Engine authentication. The offline worker alone may use the local Earth Engine credential; it must not appear in client code, logs, manifests, Git, or release artifacts.

## Scientific method decisions

### 1. Water: MNDWI

Xu's MNDWI is:

\[
MNDWI=(Green-SWIR1)/(Green+SWIR1)
\]

For Sentinel-2, use B3 and B11, making this a 20 m analytical product. MNDWI's SWIR substitution was introduced to improve open-water enhancement in built-up backgrounds relative to McFeeters NDWI. ([MNDWI-2006](source-register.md#mndwi-2006), [NDWI-1996](source-register.md#ndwi-1996), [S2-PSD](source-register.md#s2-psd))

**HEURISTIC:** use `MNDWI > 0` as the P0 fixed rule and calculate one pooled Otsu threshold as sensitivity. Zero is a documented starting direction, not a universal optimum; Otsu is a histogram criterion, not validation. ([MNDWI-2006](source-register.md#mndwi-2006), [OTSU-1979](source-register.md#otsu-1979))

AWEI shadow variant is a diagnostic. Its empirical coefficients came from Landsat 5 TM and unchanged application to Sentinel-2 must be treated as a transfer assumption. ([AWEI-2014](source-register.md#awei-2014))

Sentinel-1 can fill a cloud-contingency role only with consistent acquisition geometry and documented calibration/terrain processing; no authoritative universal dB threshold was found. ([S1-GRD](source-register.md#s1-grd))

**Claim boundary:** the result detects open-water-like spectral response. It does not measure water volume, groundwater, all wetlands, water quality, or maximum flood extent.

### 2. Green cover: NDVI

NDVI is:

\[
NDVI=(NIR-Red)/(NIR+Red)
\]

Use Sentinel-2 B8 and B4 at 10 m. The formula and vegetation interpretation are documented by USGS and the Sentinel specification. ([NDVI-USGS](source-register.md#ndvi-usgs), [S2-PSD](source-register.md#s2-psd))

**HEURISTIC:** use `NDVI >= 0.30`, with sensitivity at 0.20 and 0.40. No registered source makes these universal ecological boundaries.

EVI may be a dense-canopy continuous diagnostic, using decoded 0–1 reflectance because its formula includes an additive constant. The original EVI work documents its canopy-background/atmospheric design goals relative to NDVI. ([EVI-2002](source-register.md#evi-2002))

**Claim boundary:** thresholded NDVI is a green-cover proxy. It is not forest cover, biomass, biodiversity, crop yield, or a health diagnosis. Crop calendars, irrigation, rainfall, senescence, soil, and residual cloud can change it.

### 3. Built-up: constrained NDBI

NDBI is:

\[
NDBI=(SWIR1-NIR)/(SWIR1+NIR)
\]

Use Sentinel-2 B11/B8 at 20 m. The original method uses the positive-value direction for built-up mapping. ([NDBI-2003](source-register.md#ndbi-2003), [S2-PSD](source-register.md#s2-psd))

**HEURISTIC:** the P0 candidate rule is `NDBI > 0 AND MNDWI <= 0 AND NDVI < 0.30`. IBI with `L=0.5` and `IBI > 0` is a sensitivity method. IBI was originally evaluated in a single Landsat ETM+ city study, so reported performance cannot be transferred to Nagpur/Sentinel-2 without local validation. ([IBI-2008](source-register.md#ibi-2008))

**Claim boundary:** NDBI responds to bare soil, rock, sand, dry vegetation, construction, and some roofs. The result is a built-up spectral-candidate proxy, not an impervious-area or building-footprint inventory.

Production should replace the rule with a locally trained temporal classifier using optical, optional radar, texture, and persistence features.

### 4. Surface temperature: official Landsat Level-2 ST

Use `ST_B10` from Landsat 8/9 Collection 2 Level-2 `L2SP` products:

\[
T_K=DN\times0.00341802+149.0
\]

\[
T_C=T_K-273.15
\]

USGS documents the official algorithm, scale/offset, atmospheric inputs, ASTER GED emissivity dependency, QA bands, stable missing-data locations, and cloud-adjacency errors. ([LANDSAT-L2-GUIDE](source-register.md#landsat-l2-guide), [LANDSAT-ST](source-register.md#landsat-st))

Do not implement an internet-popular Level-1 brightness-temperature/emissivity shortcut for P1. The official Level-2 product is more defensible and smaller in implementation scope.

Landsat Band 10 has 100 m native thermal support but is distributed on a 30 m grid. The displayed pixel grid must not be advertised as 30 m independent heat detail. ([LANDSAT-L2-GUIDE](source-register.md#landsat-l2-guide))

Surface UHI should be computed within each scene as median urban LST minus median fixed/matched rural-reference LST, then summarized across dates. Land-surface temperature is not near-surface air temperature. ([NASA-LST](source-register.md#nasa-lst))

**Claim boundary:** the March–May result describes clear-sky daytime overpass conditions, not nighttime heat, personal exposure, or causal urbanization effects. Landsat 8/9 acquisition timing is approximately 10:12 local solar time. ([LANDSAT-SCHEDULE](source-register.md#landsat-schedule))

## Cross-cutting QA findings

### Reflectance conversion is a correctness risk

Direct Sentinel-2 Collection-1 products must be decoded from metadata. The Level-2A Data Quality Report defines:

\[
surfaceReflectance=(DN+BOA\_ADD\_OFFSET)/QUANTIFICATION\_VALUE
\]

with DN zero as nodata. The processing baseline and historical reprocessing are therefore part of result provenance. ([S2-DQR](source-register.md#s2-dqr), [S2-PROCESSING](source-register.md#s2-processing))

### Per-pixel QA outranks scene cloud percentage

Sentinel-2 supplies an SCL raster with nodata, defective, shadow, cloud, cirrus, snow/ice, land-cover-like, and water classes. SPARC should use it to build per-pixel valid masks; scene cloud percentage is only a discovery prefilter. ([S2-PSD](source-register.md#s2-psd), [CDSE-S2-L2A](source-register.md#cdse-s2-l2a))

### Common-valid footprint is mandatory

Unknown pixels cannot be treated as non-target land. Area change must be calculated on one common-valid denominator, with valid-observation counts published. This is a SPARC decision necessary to avoid cloud/coverage artifacts.

### Thresholds are model parameters

No universal threshold was found for the district-level decisions. Fixed P0 values are heuristics. Calibration and validation data must be separate, and a threshold must remain fixed between periods.

### Area needs an equal-area/local projected grid

All target area, gain, and loss calculations must use pixel area in metres and one recorded grid. Upsampling does not improve native analytical support.

## Validation conclusion

A product is not validated because two satellite products agree. JRC GSW, Dynamic World, WorldCover, and GHSL share related remote-sensing inputs and their own model errors; they are corroboration unless compared against an independent reference design.

The correct production validation path is a probability sample stratified by stable target, stable non-target, gain, and loss; temporally appropriate reference evidence; design-consistent user's/producer's accuracy; and error-adjusted area with confidence intervals. This follows Olofsson et al. ([OLOFSSON-2014](source-register.md#olofsson-2014))

For the hackathon, SPARC may show an exploratory manual review, but it must be labelled non-statistical. Confidence must expose data support, validation status, threshold sensitivity, temporal match, and warnings rather than a fabricated probability.

## Prototype versus production

| Concern | Hackathon prototype | Production requirement |
|---|---|---|
| Time | two fixed same-season periods | multi-year same-season/phenology-aware series |
| Water | MNDWI fixed threshold plus sensitivity | locally calibrated optical/SAR temporal model |
| Green | NDVI thresholded proxy | separate vegetation types and phenology-aware trajectories |
| Built | constrained NDBI proxy | local calibrated temporal classifier and persistent transitions |
| Heat | Landsat official ST and scene-level SUHI | multi-year scene series, matched rural references, uncertainty intervals |
| QA | SCL/QA masks, two-observation floor | probabilistic quality model and version monitoring |
| Validation | exploratory review if time allows | probability sample, independent labels, adjusted area/intervals |
| Delivery | precomputed licensed Nagpur bundle | automated monitored acquisition and reproducible processing |

## Risk register

| Severity | Risk | Effect | Response |
|---|---|---|---|
| Critical | insufficient common-valid Sentinel coverage | false or unpublishable change | run discovery gate; switch whole pilot to Bengaluru Urban if Nagpur fails |
| Critical | wrong Level-2A offset/scaling | biased indices across processing versions | parse metadata and test known fixtures ([S2-DQR](source-register.md#s2-dqr)) |
| Critical | thresholds tuned independently by date | artificial gain/loss | calibrate once and freeze |
| High | NDBI bare-soil confusion | overstates built candidates | water/NDVI guards, IBI sensitivity, local validation ([NDBI-2003](source-register.md#ndbi-2003)) |
| High | NDVI described as forest | misleading ecological claim | enforce green-cover proxy vocabulary |
| High | LST described as air temperature | misleading heat claim | enforce surface-temperature/SUHI vocabulary ([NASA-LST](source-register.md#nasa-lst)) |
| High | boundary version mismatch | geometry-driven apparent change | one versioned AOI/hash across periods |
| High | optional product treated as truth | inflated confidence | call products context/corroboration; independent validation |
| Medium | minimum mapping unit removes real small features | biased area | publish raw/cleaned outputs and exact rule |
| Medium | provider outage/credential failure during demo | broken presentation | precompute immutable, licensed outputs |
| Medium | license/attribution omission | redistribution/compliance failure | generate data and software notices before release |

## Open evidence items

The following cannot be confirmed from the current codebase or from planning research alone:

- actual Sentinel-2 item counts and AOI-level clear coverage for all four districts;
- actual Landsat clear-scene counts and ASTER GED gap pattern for the proposed rural/urban zones;
- stable district/subdistrict codes and current-boundary review before any expansion beyond the two validated prototype district AOIs;
- locally defensible thresholds and minimum mapping units;
- independent reference imagery availability and license;
- local user's/producer's accuracy and adjusted areas;
- storage, egress, and runtime costs for the direct source path.

These are discovery/implementation tasks, not facts to fill with estimates.

## Documentation map

- Exact formulas, masks, output schema, and failure modes: [indicator-methodology.md](../indicator-methodology.md)
- Acquisition routes, assets, manifests, and offline fallback: [data-sources.md](../data-sources.md)
- Validation design and confidence policy: [validation-plan.md](../validation-plan.md)
- Software/data licenses and required attribution: [open-source-reuse.md](../open-source-reuse.md)
- Pilot decision: [ADR-007](../decisions/ADR-007-pilot-district.md)
- Full source metadata: [source-register.md](source-register.md)
