# SPARC indicator methodology

**Status:** implementation-ready planning specification; no imagery has been downloaded or processed  
**Evidence cut-off:** 2026-08-02  
**Primary pilot:** Nagpur district  
**P0 optical periods:** 2019-10-15 through 2019-12-15 and 2024-10-15 through 2024-12-15, both endpoints inclusive  
**P1 heat periods:** 2019-03-01 through 2019-05-15 and 2024-03-01 through 2024-05-15, both endpoints inclusive

## Reading rules

- **FACT** means the statement is supported by the linked product-owner or original peer-reviewed source.
- **DECISION** means it is part of the SPARC scope.
- **RECOMMENDATION** means it is the preferred engineering approach but may change after the discovery dry run.
- **HEURISTIC** means a configurable prototype value without universal scientific validity.
- **ASSUMPTION** means it has not been verified from acquired imagery or field data.

## Indicator contract

### What SPARC may claim

| Indicator ID | Public name | Defensible interpretation | Prohibited interpretation |
|---|---|---|---|
| `surface_water_proxy` | Open surface-water area proxy | Optically detected open-water-like surface under the stated dates, masks, and threshold | Water volume, groundwater, water quality, all wetlands, or proof of legal encroachment |
| `green_cover_proxy` | Green-cover proxy | Area whose Sentinel-2 greenness exceeds the stated fixed rule | Forest cover, biodiversity, biomass, crop yield, or vegetation health diagnosis |
| `built_candidate_proxy` | Built-up spectral-candidate proxy | Area meeting the stated SWIR/NIR rule and vegetation/water guards | Authoritative building footprint, impervious fraction, cadastral development, or construction legality |
| `surface_temperature` | Land-surface temperature | Landsat Collection 2 Level-2 surface “skin” temperature for clear-sky overpass conditions | Near-surface air temperature, nighttime heat, or personal heat exposure |
| `surface_uhi` | Surface urban heat-island contrast | Same-scene urban-minus-rural land-surface-temperature contrast | Causal effect of urbanization or an air-temperature UHI measurement |

The surface-temperature distinction is a documented physical distinction, not wording preference. Landsat measures the surface state, while air temperature is a different quantity. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide), [NASA-LST](research/source-register.md#nasa-lst))

### Shared processing rules

1. **DECISION — direct data path:** do not depend on Google Earth Engine. Discover Sentinel products through the current Copernicus Data Space STAC endpoint and Landsat through USGS STAC/EarthExplorer. ([CDSE-STAC](research/source-register.md#cdse-stac), [LANDSAT-STAC](research/source-register.md#landsat-stac))
2. **DECISION — same season:** use the fixed periods above. Do not replace missing dates with another season without issuing a new methodology version.
3. **RECOMMENDATION — product level:** use Sentinel-2 Level-2A surface reflectance, not Level-1C top-of-atmosphere reflectance. The Level-2A structure and bands are defined by the current product specification. ([S2-PSD](research/source-register.md#s2-psd))
4. **FACT — direct reflectance decoding:** for Level-2A pixels with `DN != 0`, decode surface reflectance per band as:

   \[
   \rho_i=(DN_i+BOA\_ADD\_OFFSET_i)/QUANTIFICATION\_VALUE_i
   \]

   Read both values from product metadata. `DN = 0` remains nodata. Processing baseline 04.00 introduced the offset, and the reprocessed historical collection carries the newer representation. ([S2-DQR](research/source-register.md#s2-dqr), [S2-PROCESSING](research/source-register.md#s2-processing))
5. **RECOMMENDATION — per-pixel mask:** exclude Sentinel-2 SCL values `0` nodata, `1` saturated/defective, `2` cast shadow, `3` cloud shadow, `7` unclassified, `8` medium-probability cloud, `9` high-probability cloud, `10` cirrus, and `11` snow/ice. Retain values `4` vegetation, `5` bare/not-vegetated, and `6` water as observable input. Do not use SCL `6` as the indicator answer. Current class definitions come from the Level-2A specification. ([S2-PSD](research/source-register.md#s2-psd), [CDSE-S2-L2A](research/source-register.md#cdse-s2-l2a))
   - **HEURISTIC — cloud edge:** run a sensitivity case that dilates SCL cloud/cloud-shadow/cirrus exclusions by one target-grid pixel. If adopted, freeze the dilation across periods and publish its effect on common-valid coverage and indicator area.
6. **RECOMMENDATION — composite:** calculate each index on each clear observation, then take the per-period pixel median. This preserves the nonlinear index calculation and reduces one-scene outliers.
7. **HEURISTIC — evidence floor:** a period pixel is valid when it has at least two clear observations. Store its exact observation count; do not convert a missing pixel into non-target land.
8. **DECISION — common support:** compare only pixels valid in both periods. Publish common-valid area and percentage. Never interpret cloud-covered or otherwise unknown area as land, water loss, vegetation loss, or built gain.
9. **DECISION — grid:** use one explicitly versioned target grid per indicator. Use nearest-neighbor resampling for categorical masks and class rasters. The analytical resolution is the coarsest native input band, regardless of display upsampling.
10. **DECISION — area:** calculate area from pixel-area in a locally appropriate projected/equal-area CRS. Do not count pixels in geographic degrees. Record CRS, transform, pixel size, resampling, and AOI geometry hash.
11. **DECISION — one decision rule:** tune a threshold on independent or pooled calibration data, then freeze it across both comparison periods. Independently optimizing a threshold for each period changes the classifier as well as the landscape and can create artificial change.
12. **DECISION — reproducibility:** retain product IDs, sensing times, processing baselines, source URLs, content hashes where possible, mask settings, threshold values, software versions, and intermediate evidence rasters.

### Shared area and change formulas

For target indicator mask `I(i,t)` and common-valid mask `C(i)`:

\[
A_t=\sum_i pixelArea_i\,I(i,t)\,C(i)
\]

\[
gain=\sum_i pixelArea_i\,[I(i,0)=0 \land I(i,1)=1]C(i)
\]

\[
loss=\sum_i pixelArea_i\,[I(i,0)=1 \land I(i,1)=0]C(i)
\]

\[
net=A_1-A_0=gain-loss
\]

\[
percentChange=100(A_1-A_0)/A_0
\]

Return `percentChange = null` with warning `BASELINE_ZERO` when `A_0 = 0`; do not substitute zero or infinity. Report hectares and square kilometres, gross gain, gross loss, net change, and common-valid denominator.

## P0-A: open surface-water proxy

### Primary method: MNDWI

**DECISION:** use Xu's Modified Normalized Difference Water Index:

\[
MNDWI=(\rho_{green}-\rho_{SWIR1})/(\rho_{green}+\rho_{SWIR1})
\]

| Input | Sentinel-2 band | Native resolution |
|---|---:|---:|
| Green | B3 | 10 m |
| SWIR1 | B11 | 20 m |

MNDWI substitutes SWIR for the NIR channel used by McFeeters NDWI to suppress much built-up/background response. ([MNDWI-2006](research/source-register.md#mndwi-2006), [NDWI-1996](research/source-register.md#ndwi-1996)) Because B11 is native 20 m, the analytical water result is 20 m. ([S2-PSD](research/source-register.md#s2-psd))

**FACT:** the original positive-water direction makes `MNDWI > 0` a documented starting rule, not a globally valid optimum. ([MNDWI-2006](research/source-register.md#mndwi-2006))

**HEURISTIC — P0 default:** `water = MNDWI > 0` after QA and period compositing. Also compute one pooled Otsu threshold over both periods as a sensitivity result; never apply separate Otsu thresholds per period. Otsu is a histogram-separation algorithm, not environmental validation. ([OTSU-1979](research/source-register.md#otsu-1979))

Treat a denominator with absolute value below the numeric epsilon as nodata. Store the continuous MNDWI raster in addition to the binary result.

### Water sensitivity and fallback

**RECOMMENDATION:** calculate shadow-oriented AWEI as a diagnostic, not as a second vote that silently changes the result:

\[
AWEI_{sh}=\rho_{blue}+2.5\rho_{green}-1.5(\rho_{NIR}+\rho_{SWIR1})-0.25\rho_{SWIR2}
\]

Sentinel-2 inputs are B2, B3, B8, B11, and B12; its effective resolution is 20 m. AWEI coefficients were fitted with Landsat 5 TM, so unchanged use on Sentinel-2 is an explicit transfer assumption requiring local validation. The original paper describes zero as a reasonable starting threshold, not a universal one. ([AWEI-2014](research/source-register.md#awei-2014), [S2-PSD](research/source-register.md#s2-psd))

**RECOMMENDATION — cloud fallback:** use homogeneous Sentinel-1 IW GRD observations only when optical common-valid coverage is inadequate. Keep polarization, orbit direction, preferably relative orbit, incidence geometry, and preprocessing consistent. There is no registered source establishing a universal VV or VH dB water threshold; derive it from local labels or a documented representative-tile method. Direct GRD workflows require calibrated, noise-treated, terrain-corrected data. ([S1-GRD](research/source-register.md#s1-grd))

**RECOMMENDATION — historical check:** compare the result with same-month/year JRC Global Surface Water history where applicable. GSW v1.5 reaches 2024, while the original validated version of record is 1984–2015 and later updates carry documented co-registration and validation caveats. It is corroboration, not ground truth. ([GSW-2016](research/source-register.md#gsw-2016), [GSW-2024](research/source-register.md#gsw-2024))

### Water failure modes

- **FACT:** MNDWI improves urban-background suppression relative to McFeeters NDWI but is still a spectral classifier rather than a physical water inventory. ([MNDWI-2006](research/source-register.md#mndwi-2006))
- **RISK:** shallow, turbid, vegetated, shadowed, mixed-shoreline, saline, bright-roof, wet-soil, and snow/ice pixels can cross the decision boundary.
- **RISK:** period medians suppress short-lived inundation. Label the output “typical open-water proxy in the selected window,” not “maximum flood extent.”
- **RISK:** rainfall, reservoir operation, irrigation, flood timing, and—for coastal pilots—tide can dominate a two-period comparison.
- **HEURISTIC:** if connected-component cleanup is used, expose the minimum mapping unit and publish raw and cleaned areas. Never hide removed small ponds as “noise.”

### Production upgrade

Use a multi-year, same-season optical time series plus locally calibrated Sentinel-1 features, persistent detection rules, threshold sensitivity, and design-based validation. Do not promote a P0 MNDWI mask to a legal or hydrological inventory.

## P0-B: green-cover proxy

### Primary method: NDVI

**DECISION:** use the Normalized Difference Vegetation Index:

\[
NDVI=(\rho_{NIR}-\rho_{red})/(\rho_{NIR}+\rho_{red})
\]

| Input | Sentinel-2 band | Native resolution |
|---|---:|---:|
| Red | B4 | 10 m |
| NIR | B8 | 10 m |

The normalized red/NIR formulation is the standard NDVI definition. ([NDVI-USGS](research/source-register.md#ndvi-usgs), [S2-PSD](research/source-register.md#s2-psd)) The analytical output is 10 m.

**HEURISTIC — P0 default:** `green = NDVI >= 0.30`; publish sensitivity at `0.20` and `0.40`. These values are not universal ecological thresholds. If local reference labels are available, tune on a separate calibration subset and freeze the selected value across both periods.

Publish:

- median NDVI by period;
- continuous `delta_ndvi`;
- thresholded green-cover area on the common-valid footprint;
- gross green gain, gross green loss, and net change;
- threshold-sensitivity range.

### Interpretation guardrail

**DECISION:** call the binary result a **green-cover proxy**, not forest cover. NDVI responds to any photosynthetically active surface and is affected by crop calendars, irrigation, rainfall, harvest, senescence, soil background, and residual atmospheric contamination. The formula and its vegetation interpretation are documented by USGS; the district-specific confounders must be assessed locally. ([NDVI-USGS](research/source-register.md#ndvi-usgs))

### Alternatives

**RECOMMENDATION — dense-canopy diagnostic:** calculate EVI only as a secondary continuous layer:

\[
EVI=2.5(\rho_{NIR}-\rho_{red})/(\rho_{NIR}+6\rho_{red}-7.5\rho_{blue}+1)
\]

Use B8, B4, and B2 as 0–1 reflectance. The additive `1` means scaled integers cannot be inserted unchanged. EVI was designed to improve dense-canopy sensitivity and reduce some canopy-background and atmospheric effects relative to NDVI; its blue input also makes residual cloud/aerosol QA important. ([EVI-2002](research/source-register.md#evi-2002))

**OPTIONAL ONLY:** Dynamic World tree or grouped-vegetation probability may be used in a one-off comparison, but it is not a runtime dependency. Dynamic World supplies per-observation probabilities and a top-1 class, and its authors require validation of user-derived temporal products. Probabilities are not physical subpixel cover fractions. ([DW-2022](research/source-register.md#dw-2022), [DW-CATALOG](research/source-register.md#dw-catalog))

**STATIC CONTEXT ONLY:** ESA WorldCover 2021 may stratify validation or provide a 2021 reasonableness check. Do not difference WorldCover 2020 and 2021: their manuals document different algorithm versions, so apparent change mixes method and landscape change. ([WORLDCOVER-PUM](research/source-register.md#worldcover-pum))

### Production upgrade

Move to multi-year same-season baselines, phenology-aware trajectories, and separate tree, crop, grass, shrub, and wetland products. Calibrate class-specific rules locally and report error-adjusted area rather than calling thresholded NDVI forest inventory.

## P0-C: built-up spectral-candidate proxy

### Primary method: constrained NDBI

**DECISION:** use a direct Sentinel-2 spectral proxy because SPARC must not depend on Google Earth Engine. Begin with the Normalized Difference Built-up Index:

\[
NDBI=(\rho_{SWIR1}-\rho_{NIR})/(\rho_{SWIR1}+\rho_{NIR})
\]

| Input | Sentinel-2 band | Native resolution |
|---|---:|---:|
| NIR | B8 | 10 m |
| SWIR1 | B11 | 20 m |

The formula and positive built-up direction come from the original Landsat TM method. ([NDBI-2003](research/source-register.md#ndbi-2003)) The Sentinel-2 result is analytically 20 m because of B11. ([S2-PSD](research/source-register.md#s2-psd))

**HEURISTIC — P0 candidate rule:** classify a pixel as a built candidate only when all are true:

```text
NDBI > 0
MNDWI <= 0
NDVI < 0.30
```

The water and vegetation guards reduce obvious confusion; they do not make the output an authoritative built-area class. Run threshold sensitivity for NDBI and NDVI and preserve the continuous input indices.

**DECISION:** publish `built_candidate_proxy`, never “building footprint” or “impervious area.” NDBI can respond to bare soil, rock, sand, dry vegetation, construction sites, and some roof materials; the original study's result is not a universal transfer guarantee. ([NDBI-2003](research/source-register.md#ndbi-2003))

### IBI sensitivity method

The Index-based Built-up Index combines NDBI, SAVI, and MNDWI:

\[
SAVI=(\rho_{NIR}-\rho_{red})(1+L)/(\rho_{NIR}+\rho_{red}+L)
\]

\[
IBI=\frac{NDBI-(SAVI+MNDWI)/2}{NDBI+(SAVI+MNDWI)/2}
\]

**HEURISTIC:** use `L = 0.5` and `IBI > 0` only as sensitivity settings, with 0–1 reflectance and denominator guards. The original IBI paper was a single-city Landsat ETM+ experiment; its performance cannot be transferred to Nagpur or Sentinel-2 without local validation. ([IBI-2008](research/source-register.md#ibi-2008))

### Static corroboration

Use GHSL 2018 10 m built surface and WorldCover 2021 built-up class as dated context only. GHSL's 100 m multitemporal series uses five-year epochs and includes interpolated/extrapolated years; 2025/2030 must not be described as direct observations. ([GHSL-2023](research/source-register.md#ghsl-2023), [WORLDCOVER-PUM](research/source-register.md#worldcover-pum))

Dynamic World built probability is optional validation/context only because its canonical distribution is tied to Google infrastructure and SPARC has no Earth Engine dependency. Its built label is a land-cover class, not impervious fraction. ([DW-2022](research/source-register.md#dw-2022), [DW-CATALOG](research/source-register.md#dw-catalog))

### Production upgrade

Replace the constrained index rule with a locally trained, calibrated temporal classifier using Sentinel-2 reflectance/indices, Sentinel-1 backscatter where justified, texture/neighborhood features, and persistent transitions. Treat bare/construction ambiguity explicitly. Validate gain and loss classes and record the minimum mapping unit.

## P1: Landsat land-surface temperature and surface UHI

### Product and scale

**DECISION:** use Landsat 8/9 Collection 2 Tier 1 Level-2 Surface Temperature, not a manual Level-1 thermal shortcut. Require processing level `L2SP` and band `ST_B10`.

For valid stored values:

\[
T_K=DN\times0.00341802+149.0
\]

\[
T_C=T_K-273.15
\]

USGS documents the scale/offset and a single-channel production algorithm using Landsat thermal data, atmospheric inputs, and ASTER GED emissivity. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide), [LANDSAT-ST](research/source-register.md#landsat-st))

**FACT:** Landsat 8/9 thermal Band 10 has 100 m native support and is distributed on a 30 m grid. Do not claim independent 30 m thermal detail. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide))

### QA

Exclude `QA_PIXEL` bits:

- bit 0 — fill;
- bit 1 — dilated cloud;
- bit 2 — high-confidence cirrus;
- bit 3 — cloud;
- bit 4 — cloud shadow;
- bit 5 — snow.

Do not rely only on bit 6 “clear.” Retain `ST_QA` uncertainty, `ST_CDIST` distance to cloud, and `ST_EMIS` emissivity as evidence layers using their documented scales. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide))

**HEURISTIC — prototype QA:** require `ST_QA <= 2 K` and `ST_CDIST >= 1 km`; publish sensitivity at cloud distances 0, 1, and 2 km. These are SPARC settings, not USGS standards.

### Period summaries

For each clear March–May scene, calculate district median, interquartile range, and 90th percentile over valid land pixels. Aggregate scene-level statistics across the period; do not allow a month with more clear scenes to silently dominate without publishing counts.

### Surface UHI

For each scene:

\[
SUHI_{scene}=median(T_{urban})-median(T_{rural\ reference})
\]

Temperature differences have the same numeric magnitude in kelvin and degrees Celsius.

**RECOMMENDATION — heat grid:** analyze LST/SUHI on a fixed 100 m local projected grid to respect the thermal band's native support. Area-aggregate the 20 m built-candidate mask to a built-candidate fraction on that grid; do not select a 30 m thermal cell solely because one upsampled 20 m/30 m value crosses a threshold. The source product remains the USGS 30 m grid with 100 m thermal support. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide))

**HEURISTIC — zone membership:** classify a 100 m heat cell as urban when at least 50% is a built candidate in both optical periods, and as rural-reference eligible when at most 10% is a built candidate in both periods. Exclude water from both. Publish sensitivity to these fractions.

**RECOMMENDATION:** keep these persistent urban/rural memberships and the rural reference geometry fixed across 2019 and 2024. This avoids changing the temperature population while measuring temperature change. Analyze newly built-candidate cells separately as an exploratory transition group. Prefer rural samples with similar elevation and broad land cover.

**HEURISTIC:** begin with a 5–10 km ring around the persistent urban footprint, exclude built/water pixels, and publish sensitivity to ring width. If acquisition is limited to the district boundary, use the outer non-built district area and emit `RURAL_REFERENCE_CONSTRAINED` because that design is more confounded.

Calculate `SUHI_scene` first and then take the median across dates. Do not subtract two unrelated seasonal composites whose valid-date composition differs.

### LST limitations

- **FACT:** Landsat 8 and Landsat 9 each revisit on a 16-day cycle and are offset to provide approximately eight-day combined opportunities; acquisition is near 10:12 local solar time. The result therefore does not measure nighttime heat. ([LANDSAT-SCHEDULE](research/source-register.md#landsat-schedule))
- **FACT:** missing ASTER GED emissivity creates stable surface-temperature gaps, and cloud/cloud-shadow adjacency can bias retrieved temperature. ([LANDSAT-ST](research/source-register.md#landsat-st))
- **RISK:** cloud availability, weather, antecedent rainfall, soil moisture, irrigation, phenology, emissivity error, elevation, and rural-reference choice can dominate a two-period contrast.
- **DECISION:** a single surviving clear scene is a snapshot with low confidence, not a seasonal estimate.
- **DECISION:** no causal urbanization claim is allowed from this observational comparison.

### Production upgrade

Use a multi-year same-season scene series, scene-level urban-minus-matched-rural contrasts, bootstrap intervals by date and spatial block, elevation/land-cover matching, multiple rural-reference definitions, and independent ground radiometer data where available. Air-temperature stations cannot directly validate land-surface temperature because they measure a different quantity. ([NASA-LST](research/source-register.md#nasa-lst))

## Required output metadata

Every indicator result must include at least:

```text
indicatorId
methodVersion
aoiName
aoiGeometryHash
sourceProductIds[]
sourceAcquisitionTimes[]
sourceProcessingBaselines[]
periodStart
periodEnd
sourceBands[]
reflectanceOrTemperatureScaleRule
maskRule
targetCrs
pixelSizeMetres
resamplingRules
thresholdMethod
thresholdValue
thresholdSensitivity
validObservationCountSummary
commonValidAreaSqKm
commonValidFraction
rawAreaSqKm
cleanedAreaSqKm | null
gainSqKm
lossSqKm
netChangeSqKm
percentChange | null
validationMetrics | null
qualityLabel
warnings[]
attribution[]
```

## Validation dependency

No indicator is production-valid solely because the computation completes or agrees with another satellite product. Accuracy and area validation must follow the probability-sample and error-adjustment plan in [validation-plan.md](validation-plan.md), grounded in the original land-change good-practice paper. ([OLOFSSON-2014](research/source-register.md#olofsson-2014))
