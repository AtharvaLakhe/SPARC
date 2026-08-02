# SPARC data sources and acquisition policy

**Status:** source-selection plan; no source data has been downloaded  
**Evidence cut-off:** 2026-08-02  
**Runtime constraint:** no Google Earth Engine dependency

## Decisions

- **DECISION:** primary district is Nagpur; Bengaluru Urban is the prepared backup.
- **DECISION:** P0 Sentinel-2 periods are 2019-10-15 through 2019-12-15 and 2024-10-15 through 2024-12-15, inclusive.
- **CANDIDATE:** Bengaluru Urban backup periods are 2019-01-15 through 2019-03-15 and the same dates in 2024; they remain unfrozen until the discovery and common-valid-area gates pass.
- **DECISION:** P1 Landsat heat periods are March 1 through May 15 of 2019 and 2024.
- **DECISION:** primary P0 data are direct Copernicus Sentinel-2 Level-2A products discovered through Copernicus Data Space Ecosystem STAC.
- **DECISION:** primary P1 heat data are USGS Landsat 8/9 Collection 2 Tier 1 Level-2 Surface Temperature products.
- **DECISION:** Dynamic World is optional comparison material, never a production or demo runtime dependency.
- **ASSUMPTION:** enough clear common coverage exists for Nagpur in the fixed periods. This cannot be confirmed from the current codebase or planning documents because no catalog query or image acquisition has been run.

## Source matrix

| Priority | Source | SPARC use | Direct access path | Runtime role |
|---|---|---|---|---|
| Required | Survey of India Administrative Boundary Database | District AOI | Survey of India ABDB/download portal | pre-acquired, versioned boundary |
| Required | Copernicus Sentinel-2 Level-2A | MNDWI, NDVI, NDBI and optional AWEI/EVI | CDSE STAC plus official asset/download service | pre-acquired/cache; server-side processing |
| Required for P1 | USGS Landsat 8/9 Collection 2 Level-2 ST | LST and surface UHI | USGS STAC/AWS or EarthExplorer | pre-acquired/cache; server-side processing |
| Conditional | Copernicus Sentinel-1 IW GRD | cloudy-period water corroboration/fallback | CDSE STAC/download | offline fallback only for P0 |
| Optional | JRC Global Surface Water v1.5 | historical water plausibility | official JRC tile download | validation/context |
| Optional | ESA WorldCover 2021 v200 | static land-cover context/validation strata | ESA direct COG/tile download | bundled context if license notice included |
| Optional | GHSL GHS-BUILT-S R2023A | dated built-up plausibility | JRC direct product download | validation/context |
| Optional only | Dynamic World V1 | one-off probability/label comparison | Google-hosted catalog/export path | no live dependency; omit if not pre-acquired |

The access and product facts in this matrix are documented by the source owners. ([SOI-ABDB](research/source-register.md#soi-abdb), [CDSE-STAC](research/source-register.md#cdse-stac), [LANDSAT-STAC](research/source-register.md#landsat-stac), [GSW-2024](research/source-register.md#gsw-2024), [WORLDCOVER-DATA](research/source-register.md#worldcover-data), [GHSL-2023](research/source-register.md#ghsl-2023), [DW-CATALOG](research/source-register.md#dw-catalog))

### Reuse decision details

“Current” below means that an official owner page/product was available at the 2026-08-02 evidence cut-off. It does not prove that a particular Nagpur scene, boundary file, or service call works; those remain Day 0 acquisition gates.

| Resource | Purpose/component | License and attribution | Maintenance/current evidence | Advantages | Limitations | Prototype/production position | Alternative or fallback |
|---|---|---|---|---|---|---|---|
| Survey of India ABDB | Processing AOI and published district/subdistrict geometry | Exact acquired-product terms unresolved; do not redistribute until recorded ([SOI-ABDB](research/source-register.md#soi-abdb)) | Official product/catalog available at cut-off | Authoritative national mapping agency and subdistrict coverage | File not acquired; version, codes, topology, and redistribution permission unconfirmed | P0 only after geometry/license gate; production needs an update/version policy | Another authority-, version-, code-, and license-verified source; otherwise retain a non-redistributed local boundary or district-only result |
| Copernicus Sentinel-2 L2A | P0 processing input for water, vegetation, and built-up spectral proxies | Sentinel legal notice; derived output uses the modified-Copernicus attribution ([SENTINEL-LEGAL](research/source-register.md#sentinel-legal), [CDSE-ATTRIBUTION](research/source-register.md#cdse-attribution)) | Current mission specifications, quality reports, and CDSE STAC at cut-off ([S2-PSD](research/source-register.md#s2-psd), [CDSE-STAC](research/source-register.md#cdse-stac)) | Suitable visible/NIR/SWIR bands at 10/20 m and repeat coverage | Optical clouds/shadows; metadata-aware offsets/baselines; no thermal band | Required P0 and production-capable through a provider adapter | Approved alternate STAC/access host for the same Copernicus products; locally retained inputs and precomputed outputs |
| Landsat 8/9 C2 L2 ST | P1 offline processing for LST and surface-UHI | U.S. public-domain data; preserve USGS citation/credit ([LANDSAT-PUBLIC-DOMAIN](research/source-register.md#landsat-public-domain), [LANDSAT-ST](research/source-register.md#landsat-st)) | Current Collection 2 product/access documentation at cut-off | Official surface-temperature product with QA and stable scaling | Cloud/ASTER GED gaps, limited clear dates, coarse effective thermal support, daytime surface—not air—temperature | P1 precomputed prototype; production-capable with scene/uncertainty gates | EarthExplorer if STAC/cloud access fails; omit heat rather than substitute Sentinel-2 |
| Copernicus Sentinel-1 IW GRD | Conditional water corroboration when optical coverage fails | Copernicus Sentinel legal notice/attribution applies ([SENTINEL-LEGAL](research/source-register.md#sentinel-legal)) | Current official CDSE processing documentation at cut-off ([S1-GRD](research/source-register.md#s1-grd)) | Radar observations are not blocked by optical cloud | Calibration, terrain, speckle, orbit, and threshold choices add a separate method; no approved universal cutoff | Conditional fallback, not a silent substitute; production only after local validation | Expand equal optical windows symmetrically, switch whole pilot, or use the offline water pack |
| JRC Global Surface Water v1.5 | Water history plausibility and validation strata | Copernicus/JRC use terms; cite dataset/paper and use published map credit ([GSW-2024](research/source-register.md#gsw-2024)) | Official 1984–2024 update page at cut-off | Long historical record and useful water context | Aggregated history/product alignment is not contemporaneous independent truth for a local 2019/2024 classifier | Optional context in prototype and production | Omit it and retain explicit local validation/quality limits |
| ESA WorldCover 2021 v200 | Static land-cover context and validation strata | CC BY 4.0 with ESA wording, license, DOI, and modification notice ([WORLDCOVER-DATA](research/source-register.md#worldcover-data)) | Official v200 access/manual at cut-off | Global 10 m categorical context | Single 2021 epoch for this use; 2020/2021 algorithm change prevents naive change inference | Optional context only | Omit; use licensed independent reference sampling where available |
| GHSL GHS-BUILT-S R2023A | Dated built-up plausibility and long-horizon context | CC BY 4.0; cite both release paper and specific product ([GHSL-2023](research/source-register.md#ghsl-2023)) | Official current release/citation guidance at cut-off | Established global built-up context and multitemporal products | Product epochs/resolution/method do not make it local ground truth; future epochs may be modeled | Optional context, not a P0 classifier dependency | Omit; use independently sampled reference evidence |
| Dynamic World V1 | Optional per-scene probability/label comparison | CC BY 4.0 plus provider and modified-Sentinel attribution ([DW-CATALOG](research/source-register.md#dw-catalog)) | Official living catalog and 2022 source paper at cut-off | Per-Sentinel-2 probabilities can expose uncertainty/context | Canonical Google-hosted route, model-derived rather than independent truth, authentication/runtime risk | Optional pre-export only; not a demo or production dependency | Omit entirely; use WorldCover/GHSL/JRC context where method-appropriate |
| Earth Search / Sentinel-2 L2A COGs | Alternate discovery/delivery path for the same Copernicus products | Service software/access does not replace underlying Sentinel terms or attribution ([Earth Search](https://github.com/Element84/earth-search), [AWS registry](https://registry.opendata.aws/sentinel-2-l2a-cogs/)) | Public service/repository current at cut-off; maintainer states no SLA | Anonymous STAC and range-readable COG access simplify recovery | Non-authoritative delivery provider and no service guarantee | Approved P0 operational fallback, never sole production source | CDSE primary, Planetary Computer secondary, then retained local inputs |
| Microsoft Planetary Computer STAC | Second alternate catalog/delivery adapter | Check every collection's underlying data license; never persist expiring signed URLs ([official docs](https://planetarycomputer.microsoft.com/docs)) | Public documentation/service current at cut-off | Broad STAC catalog and COG-oriented access | Throttling and asset signing add state and expiry risk | Secondary fallback after a compatibility spike | CDSE/Earth Search, then retained local inputs and offline pack |

## 1. Administrative boundary

### Primary source

Use the Survey of India Administrative Boundary Database district layer. The official product provides Indian administrative boundaries through district/sub-district levels in vector formats including Shapefile. ([SOI-ABDB](research/source-register.md#soi-abdb), [SOI-CATALOG](research/source-register.md#soi-catalog))

Before analysis, store:

```text
sourceAgency
productName
downloadUrl
downloadDate
productVersionOrUpdateDate
districtName
stateName
stableDistrictCodeIfPresent
originalCrs
geometryRepairLog
originalFileHash
normalizedGeoJsonHash
licenseOrAccessTerms
```

**DECISION:** the same versioned Nagpur geometry must clip both 2019 and 2024. Administrative-boundary change must not be confused with land-cover change.

**RECOMMENDATION:** retain the original vector, create a normalized analysis copy without changing topology, and compute area before and after repair. A material area difference is a stop condition.

**LEGAL RISK:** free access is not the same as unrestricted redistribution. The exact terms shipped with the selected Survey of India product must be recorded before embedding the boundary in a public repository or downloadable artifact. The current source establishes official availability but is not treated here as a blanket redistribution license. ([SOI-ABDB](research/source-register.md#soi-abdb))

## 2. Sentinel-2 Level-2A

### Discovery

Use the current CDSE STAC root:

```text
https://stac.dataspace.copernicus.eu/v1/
```

The legacy CDSE STAC endpoint was deprecated on 2025-11-17. Query `sentinel-2-l2a` with spatial intersection and the exact date interval; inspect the live collection and queryables documents instead of assuming a permanent response schema. ([CDSE-STAC](research/source-register.md#cdse-stac))

Required discovery fields:

```text
itemId
collection
geometry
datetime/start_datetime/end_datetime
eo:cloud_cover
platform
processing baseline/version fields when exposed
asset hrefs and media types
license/provider links
```

**HEURISTIC:** a scene-level cloud prefilter of at most 80% may reduce catalog volume, but it must not replace AOI-level per-pixel SCL masking. A globally cloudy tile can contain clear AOI pixels, and a low scene percentage can still hide the AOI.

### Required assets

| SPARC method | Bands/assets |
|---|---|
| MNDWI water | B3, B11, SCL, product/tile metadata |
| NDVI green cover | B4, B8, SCL, product/tile metadata |
| constrained NDBI | B3, B4, B8, B11, SCL, product/tile metadata |
| AWEI sensitivity | B2, B3, B8, B11, B12, SCL, metadata |
| EVI sensitivity | B2, B4, B8, SCL, metadata |

Sentinel-2 MSI native resolutions are 10 m for B2/B3/B4/B8 and 20 m for B11/B12; any index using a SWIR band is analytically 20 m even if displayed at 10 m. ([S2-PSD](research/source-register.md#s2-psd))

### Mandatory metadata handling

Read `BOA_ADD_OFFSET` and `QUANTIFICATION_VALUE` from the product metadata. Direct L2A surface reflectance is decoded as `(DN + BOA_ADD_OFFSET) / QUANTIFICATION_VALUE`, with DN zero reserved for nodata. Processing baselines and Collection-1 reprocessing make metadata-aware decoding necessary for a reproducible 2019/2024 comparison. ([S2-DQR](research/source-register.md#s2-dqr), [S2-PROCESSING](research/source-register.md#s2-processing))

Do not:

- assume all DNs are simply divided by 10,000;
- substitute Level-1C imagery when Level-2A is missing without creating a different method version;
- resample SCL with bilinear/cubic interpolation;
- treat SCL water as the water answer;
- discard product IDs or processing baselines after mosaicking.

### Download and cache policy

**RECOMMENDATION:** use STAC for discovery, then acquire only official assets needed for the AOI/method when the provider supports asset-level access. Otherwise acquire the official product and extract bands server-side. The implementation must follow returned asset metadata rather than an invented filename convention.

Store raw products outside Git, read-only by content hash. Derived COGs should include the source-item IDs, original checksums where available, processing metadata, CRS/transform, nodata, scale, and attribution.

## 3. Landsat Collection 2 Level-2 Surface Temperature

### Discovery and access

USGS exposes Landsat Collection 2 through its STAC/cloud access route and EarthExplorer. Collection 2 cloud assets use STAC metadata and COGs; the AWS bucket is requester-pays, so cloud egress/request cost and credentials must be considered. EarthExplorer is the operational fallback. ([LANDSAT-STAC](research/source-register.md#landsat-stac))

**RECOMMENDATION:** query the current USGS STAC collections endpoint and select the live Collection 2 Level-2 surface-temperature collection rather than hard-coding an undocumented asset layout. At access time, the official browser exposes `landsat-c2l2-st`. Persist the returned collection and item metadata.

### Selection

Require:

- Landsat 8 or 9;
- Collection 2;
- Tier 1 for primary comparison;
- processing level `L2SP`;
- acquisition date from March 1 through May 15 in 2019 or 2024;
- AOI intersection;
- valid `ST_B10` and supporting QA assets.

Required assets:

```text
ST_B10
QA_PIXEL
QA_RADSAT or equivalent validity asset when supplied
ST_QA
ST_CDIST
ST_EMIS
product metadata
```

USGS documents the `ST_B10` scale `0.00341802`, offset `149.0 K`, QA layers, ASTER GED emissivity dependency, and stable missing-data/cloud-adjacency caveats. ([LANDSAT-L2-GUIDE](research/source-register.md#landsat-l2-guide), [LANDSAT-ST](research/source-register.md#landsat-st))

Do not download Level-1 solely to implement a popular brightness-temperature shortcut. The approved P1 method uses the official Level-2 surface-temperature product.

## 4. Sentinel-1 conditional fallback

Use Sentinel-1 only when Sentinel-2 optical coverage fails the documented release threshold or as a separate corroboration layer.

Selection must keep these homogeneous:

```text
instrument mode = IW
polarization availability
orbit direction
preferably relative orbit
nominal resolution
processing/calibration path
```

Official CDSE processing options document calibration, thermal-noise removal, optional speckle filtering, radiometric terrain correction, and orthorectification. ([S1-GRD](research/source-register.md#s1-grd)) There is no approved universal SPARC dB cutoff; calibration/threshold selection belongs in a separate method version.

## 5. Optional context products

### JRC Global Surface Water

Use official v1.5 direct downloads for current 1984–2024 aggregate products and separate 2022–2024 histories. The official page documents that historical v1.4 and newer history assets may need merging and records Collection-1/Collection-2 alignment and Monthly Recurrence caveats. ([GSW-2024](research/source-register.md#gsw-2024))

Use only for water plausibility/stratification. Do not use maximum extent as a hard exclusion mask and do not call agreement independent validation.

### ESA WorldCover

Use WorldCover 2021 v200 direct tiles/COGs for static context. Do not use 2020-to-2021 differencing as change because the product manual documents an algorithm-version change. ([WORLDCOVER-PUM](research/source-register.md#worldcover-pum), [WORLDCOVER-DATA](research/source-register.md#worldcover-data))

### GHSL

Use GHS-BUILT-S 2018 10 m as dated context and the 100 m multitemporal product for broad long-horizon context only. Do not label 2025/2030 epochs observed. Cite both the current GHSL release paper and the specific dataset; a generic GHSL website citation is insufficient under the product owner's reuse guidance. ([GHSL-2023](research/source-register.md#ghsl-2023))

### Dynamic World

Dynamic World is licensed CC BY 4.0 and provides per-Sentinel-2 probabilities and top-1 labels, but the canonical catalog is Google-hosted. ([DW-CATALOG](research/source-register.md#dw-catalog))

**DECISION:** no server path, demo path, test, or build may require Earth Engine authentication. If a pre-exported Dynamic World subset is used for optional comparison, preserve item/date/algorithm metadata and required attribution; the application must function when the layer is absent.

## 6. Acquisition manifest

Create one immutable manifest per acquisition run:

```json
{
  "manifestVersion": "1",
  "createdAt": "ISO-8601 UTC",
  "aoi": {
    "name": "Nagpur",
    "source": "Survey of India ABDB",
    "geometryHash": "sha256:..."
  },
  "period": {
    "start": "2019-10-15",
    "end": "2019-12-15",
    "endInclusive": true
  },
  "catalog": {
    "provider": "CDSE",
    "endpoint": "https://stac.dataspace.copernicus.eu/v1/",
    "query": {},
    "queriedAt": "ISO-8601 UTC"
  },
  "items": [
    {
      "id": "provider item id",
      "datetime": "ISO-8601 UTC",
      "processingBaseline": "provider value",
      "assets": [
        {
          "key": "provider asset key",
          "href": "provider URL",
          "mediaType": "provider value",
          "checksum": "provider or locally computed hash"
        }
      ]
    }
  ],
  "licenseAndAttribution": []
}
```

Never store bearer tokens, refresh tokens, AWS keys, usernames, passwords, or signed URLs in this manifest.

## 7. License and attribution summary

| Source | Reuse position | Required/approved output treatment |
|---|---|---|
| Copernicus Sentinel | free/full/open under the Sentinel legal notice | `Contains modified Copernicus Sentinel data [year(s)]` for derived outputs ([SENTINEL-LEGAL](research/source-register.md#sentinel-legal), [CDSE-ATTRIBUTION](research/source-register.md#cdse-attribution)) |
| Landsat Collection 2 | U.S. government public-domain data; USGS requests acknowledgement | cite DOI `10.5066/P9OGBGM6`; recommended credit `Landsat Collection 2 Level-2 image courtesy of the U.S. Geological Survey.` ([LANDSAT-PUBLIC-DOMAIN](research/source-register.md#landsat-public-domain), [LANDSAT-ST](research/source-register.md#landsat-st)) |
| Dynamic World | CC BY 4.0 | provider attribution, modified-Sentinel notice, license link, modification statement, and Brown et al. citation ([DW-CATALOG](research/source-register.md#dw-catalog)) |
| ESA WorldCover | CC BY 4.0 | ESA WorldCover's published-map wording, license link, modification statement, and dataset DOI ([WORLDCOVER-DATA](research/source-register.md#worldcover-data)) |
| JRC Global Surface Water | Copernicus/JRC free-use terms | cite dataset and Pekel et al.; map wording `Source: EC JRC/Google` ([GSW-2024](research/source-register.md#gsw-2024)) |
| GHSL | CC BY 4.0 | cite both the latest GHSL release paper and specific dataset; generic website citation alone is insufficient ([GHSL-2023](research/source-register.md#ghsl-2023)) |
| Survey of India ABDB | exact selected-product terms pending review | do not redistribute until the acquired terms are recorded ([SOI-ABDB](research/source-register.md#soi-abdb)) |

The exact wording and software-notice obligations are maintained in [open-source-reuse.md](open-source-reuse.md).

## 8. Credentials and network boundary

- All catalog/download credentials are server-side or acquisition-time secrets.
- Do not expose secrets through `NEXT_PUBLIC_*`, browser JavaScript, result JSON, logs, screenshots, or committed fixtures.
- Prefer anonymous public catalog discovery where supported; authenticate only the asset-fetch step that requires it.
- Cache deterministic demo products so a conference/demo path does not depend on live provider uptime or credentials.
- Rotate any credential that enters Git history or public logs; deleting the current file is not enough.

## 9. Demo and offline fallback

Before the hackathon presentation, prepare a small, licensed, provenance-complete Nagpur package containing:

- normalized district boundary or a non-redistributed local reference to it, depending on Survey of India terms;
- selected source item manifests;
- clipped/derived indicator COGs;
- valid-observation counts and common-valid masks;
- area summaries and validation status;
- a copy of required attribution text and license links;
- a backup Bengaluru Urban package if Nagpur discovery fails the coverage gate.

The demo may read these immutable outputs without calling CDSE, USGS, AWS, Google, or another provider. It must display that they are precomputed and show their source dates.

## 10. Discovery dry-run acceptance checklist

Before implementation claims data feasibility, confirm and record:

1. Official Nagpur geometry obtained and legally usable for the intended artifact.
2. Sentinel-2 L2A item counts for both fixed windows.
3. AOI-level common-valid coverage after SCL masking—not scene-level cloud metadata alone.
4. At least two valid observations per period for most target pixels, or a documented downgrade.
5. Processing baseline/metadata decoding works across both periods.
6. Required bands/assets are retrievable through the current direct endpoint.
7. Landsat `L2SP` item counts and clear March 1–May 15 coverage for both years.
8. ASTER-related ST gaps and cloud-distance sensitivity do not invalidate the rural/urban comparison.
9. Estimated storage, requests, egress, and processing time fit the hackathon budget.
10. Bengaluru Urban can be substituted without changing the method contract if Nagpur fails.

Until this checklist is complete, district-level data availability is an **assumption**, not a confirmed fact.
