# SPARC source register

**Status:** planning baseline  
**Evidence cut-off:** 2026-08-02  
**Last access check:** 2026-08-02

This register is the bibliography and provenance ledger for SPARC's research documents. The short source IDs are used as citations throughout `docs/`. A source is included only when it is a product-owner specification, government data page, legal notice, or original peer-reviewed method paper. A living web page with no displayed publication date is recorded as **undated living documentation** rather than assigned an invented date.

The register does not imply that SPARC has downloaded, tested, or redistributed a dataset. Dataset acquisition remains a later implementation step.

## Copernicus Sentinel sources

<a id="gee-access"></a>
### GEE-ACCESS

- **Title:** *Earth Engine access*
- **Author/owner:** Google Earth Engine
- **URL:** https://developers.google.com/earth-engine/guides/access
- **Accessed:** 2026-08-02
- **Used for:** Cloud-project registration, API enablement, authentication and server-side access requirements.

<a id="gee-s2-sr"></a>
### GEE-S2-SR

- **Title:** *Harmonized Sentinel-2 MSI: MultiSpectral Instrument, Level-2A (SR)*
- **Author/owner:** European Union/ESA/Copernicus; catalogued by Google Earth Engine
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- **Accessed:** 2026-08-02
- **Used for:** primary offline image collection `COPERNICUS/S2_SR_HARMONIZED`, its L2A surface-reflectance scaling, harmonization behavior, SCL availability and Copernicus terms.

<a id="s2-psd"></a>
### S2-PSD

- **Title:** *Sentinel-2 Products Specification*
- **Author/owner:** Copernicus Sentinel-2 / European Space Agency
- **Version and date:** issue 15.1, 2025-12-05; published in the SentiWiki library 2026-03-05
- **URL:** https://sentiwiki.copernicus.eu/__attachments/1692737/S2-PDGS-CS-DI-PSD-V15.1.pdf
- **Accessed:** 2026-08-02
- **Used for:** Level-2A product structure, MSI band definitions, spatial resolutions, Scene Classification Layer values, metadata, processing baseline, reflectance encoding, and quality assets.
- **Authority note:** current mission product specification at the evidence cut-off.

<a id="s2-dqr"></a>
### S2-DQR

- **Titles:** *Sentinel-2 Annual Performance Report – Year 2025* and *Data Quality Report – Sentinel-2 MSI Level-2A, May 2026*
- **Author/owner:** Copernicus Sentinel-2 Optical Mission Performance Cluster / European Space Agency
- **Versions and dates:** annual report issue 1.0, 2026-02-27; monthly quality report issue 97.0, 2026-05-13
- **URLs:** https://sentiwiki.copernicus.eu/__attachments/1692737/OMPC.CS.APR.008-i1r0-S2%20MSI-Annual-Performance-Report-2025.pdf and https://sentiwiki.copernicus.eu/__attachments/1692737/OMPC.CS.DQR.002.04-2026-i97r0-MSI-L2A-DQR-May-2026.pdf
- **Accessed:** 2026-08-02
- **Used for:** `BOA_ADD_OFFSET`, `QUANTIFICATION_VALUE`, processing-baseline changes, Level-2A surface-reflectance conversion, and product-quality caveats.
- **Decision consequence:** a direct-CDSE implementation must read product metadata and must not assume that every stored DN is simply `DN / 10000`.

<a id="s2-processing"></a>
### S2-PROCESSING

- **Title:** *S2 Processing*
- **Author/owner:** Copernicus Sentinel / European Space Agency
- **Date:** undated living documentation; content included processing baseline 05.12 at access time
- **URL:** https://sentiwiki.copernicus.eu/web/s2-processing
- **Accessed:** 2026-08-02
- **Used for:** processing-baseline history, Collection-1 reprocessing, and the requirement to preserve processing-version provenance.

<a id="cdse-s2-l2a"></a>
### CDSE-S2-L2A

- **Title:** *Sentinel-2 L2A – Documentation*
- **Author/owner:** Copernicus Data Space Ecosystem
- **Date:** undated living documentation
- **URL:** https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html
- **Accessed:** 2026-08-02
- **Used for:** Level-2A band and Scene Classification Layer descriptions and CDSE processing-service semantics.

<a id="cdse-stac"></a>
### CDSE-STAC

- **Title:** *STAC product catalogue – Documentation*
- **Author/owner:** Copernicus Data Space Ecosystem
- **Date:** undated living documentation; the current endpoint replaced the legacy endpoint on 2025-11-17
- **URL:** https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- **Accessed:** 2026-08-02
- **Used for:** direct, non-Google-Earth-Engine Sentinel discovery through `https://stac.dataspace.copernicus.eu/v1/`, including spatial, temporal, collection, and cloud-metadata filtering.
- **Operational note:** clients must use the current endpoint and query the live collection/queryables metadata rather than hard-code the deprecated catalog schema.

<a id="cdse-terms"></a>
### CDSE-TERMS

- **Title:** *Terms and conditions*
- **Author/owner:** European Union / Copernicus Data Space Ecosystem
- **Date:** undated living legal notice
- **URL:** https://dataspace.copernicus.eu/terms-and-conditions
- **Accessed:** 2026-08-02
- **Used for:** Sentinel access, reuse conditions, attribution, and legal provenance.

<a id="sentinel-legal"></a>
### SENTINEL-LEGAL

- **Title:** *Sentinel Data Legal Notice*
- **Author/owner:** European Union / European Space Agency
- **Date:** undated notice citing the 2013/2014 Copernicus legal framework
- **URL:** https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice
- **Accessed:** 2026-08-02
- **Used for:** permitted reproduction, distribution, adaptation/combination, source notice, warranty disclaimer, lawful-use condition, and non-endorsement/legal provenance.

<a id="cdse-attribution"></a>
### CDSE-ATTRIBUTION

- **Title:** *Copernicus Data Space Ecosystem FAQ – attribution guidance*
- **Author/owner:** Copernicus Data Space Ecosystem
- **Date:** undated living documentation
- **URL:** https://documentation.dataspace.copernicus.eu/FAQ.html
- **Accessed:** 2026-08-02
- **Used for:** the public-output notice `Contains modified Copernicus Sentinel data [year(s)]`.

<a id="s1-grd"></a>
### S1-GRD

- **Title:** *Sentinel-1 GRD – Documentation*
- **Author/owner:** Copernicus Data Space Ecosystem
- **Date:** undated living documentation
- **URL:** https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S1GRD.html
- **Accessed:** 2026-08-02
- **Used for:** Sentinel-1 GRD calibration, thermal-noise removal, optional speckle filtering, radiometric terrain correction, and orthorectification options.

## Water-method sources

<a id="ndwi-1996"></a>
### NDWI-1996

- **Title:** “The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features”
- **Author:** S. K. McFeeters
- **Publication:** *International Journal of Remote Sensing*, volume 17, issue 7
- **Date:** 1996
- **DOI/URL:** https://doi.org/10.1080/01431169608948714
- **Accessed:** 2026-08-02
- **Used for:** McFeeters NDWI formula and original zero-threshold direction.

<a id="mndwi-2006"></a>
### MNDWI-2006

- **Title:** “Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery”
- **Author:** Hanqiu Xu
- **Publication:** *International Journal of Remote Sensing*, volume 27, issue 14
- **Date:** 2006
- **DOI/URL:** https://doi.org/10.1080/01431160600589179
- **Accessed:** 2026-08-02
- **Used for:** MNDWI formula, SWIR substitution rationale, and the positive-water starting rule.

<a id="awei-2014"></a>
### AWEI-2014

- **Title:** “Automated Water Extraction Index: A new technique for surface water mapping using Landsat imagery”
- **Authors:** Gudina L. Feyisa, Henrik Meilby, Rasmus Fensholt, and Simon R. Proud
- **Publication:** *Remote Sensing of Environment*, volume 140
- **Date:** 2014
- **DOI/URL:** https://doi.org/10.1016/j.rse.2013.08.029
- **Accessed:** 2026-08-02
- **Used for:** `AWEI_nsh` and `AWEI_sh`, their Landsat-derived coefficients, shadow-handling intent, and the fact that zero is a starting threshold rather than a universal optimum.

<a id="otsu-1979"></a>
### OTSU-1979

- **Title:** “A threshold selection method from gray-level histograms”
- **Author:** Nobuyuki Otsu
- **Publication:** *IEEE Transactions on Systems, Man, and Cybernetics*, volume 9, issue 1
- **Date:** 1979
- **DOI/URL:** https://doi.org/10.1109/TSMC.1979.4310076
- **Accessed:** 2026-08-02
- **Used for:** the histogram threshold-selection algorithm evaluated as a sensitivity method, not as an automatically valid environmental threshold.

<a id="gsw-2016"></a>
### GSW-2016

- **Title:** “High-resolution mapping of global surface water and its long-term changes”
- **Authors:** Jean-François Pekel, Andrew Cottam, Noel Gorelick, and Alan S. Belward
- **Publication:** *Nature*, volume 540
- **Date:** 2016-12-07
- **DOI/URL:** https://doi.org/10.1038/nature20584
- **Dataset DOI:** https://doi.org/10.2905/JRC.YEQMSPG
- **Accessed:** 2026-08-02
- **Used for:** the original JRC Global Surface Water method, scope, and validated 1984–2015 version of record.

<a id="gsw-2024"></a>
### GSW-2024

- **Title:** *Global Surface Water – Data Access and Data Update Notes (1984–2024)*
- **Author/owner:** European Commission Joint Research Centre / Google
- **Version and date:** GSW v1.5 / 2024 release; living access page
- **URL:** https://global-surface-water.appspot.com/download
- **Accessed:** 2026-08-02
- **Used for:** v1.5 temporal coverage, separate v1.4 and 2022–2024 assets, Collection-1/Collection-2 co-registration caveat, occurrence corrections, unresolved Monthly Recurrence caveat, license, citation, and map attribution.

## Vegetation and land-cover sources

<a id="ndvi-usgs"></a>
### NDVI-USGS

- **Title:** *Landsat Normalized Difference Vegetation Index*
- **Author/owner:** U.S. Geological Survey Landsat Missions
- **Date:** undated living method page
- **URL:** https://www.usgs.gov/landsat-missions/landsat-normalized-difference-vegetation-index
- **Accessed:** 2026-08-02
- **Used for:** NDVI formula, interpretation, and Landsat band mapping.

<a id="evi-2002"></a>
### EVI-2002

- **Title:** “Overview of the radiometric and biophysical performance of the MODIS vegetation indices”
- **Authors:** Alfredo Huete and co-authors
- **Publication:** *Remote Sensing of Environment*, volume 83
- **Date:** 2002-11-01
- **DOI/URL:** https://doi.org/10.1016/S0034-4257(02)00096-2
- **Accessed:** 2026-08-02
- **Used for:** EVI formulation and its intended canopy-background and atmospheric-resistance behavior relative to NDVI.

<a id="dw-2022"></a>
### DW-2022

- **Title:** “Dynamic World, Near real-time global 10 m land use land cover mapping”
- **Authors:** Christopher F. Brown and co-authors
- **Publication:** *Scientific Data*, volume 9, article 251
- **Date:** 2022-06-09
- **DOI/URL:** https://doi.org/10.1038/s41597-022-01307-4
- **Accessed:** 2026-08-02
- **Used for:** Dynamic World class probabilities, top-1 labels, validation scope, known class limitations, temporal aggregation cautions, and the requirement to validate user-derived products.

<a id="dw-catalog"></a>
### DW-CATALOG

- **Title:** *Dynamic World V1 dataset catalog*
- **Author/owner:** Google, National Geographic Society, and World Resources Institute
- **Date:** undated living catalog
- **URL:** https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- **Accessed:** 2026-08-02
- **Used for:** class names, probability bands, temporal availability, algorithm-version metadata, CC BY 4.0 license, and required attribution.
- **Scope note:** optional comparison source only; it may be queried by the offline Earth Engine worker but is not required by the released demo.

<a id="worldcover-pum"></a>
### WORLDCOVER-PUM

- **Title:** *ESA WorldCover 10 m 2021 v200 Product User Manual*
- **Author/owner:** ESA WorldCover consortium
- **Version and date:** version 2.0, 2022-10-24
- **URL:** https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf
- **Accessed:** 2026-08-02
- **Used for:** classes, product grid, InputQuality layer, validation summary, license, attribution, and the warning that 2020 and 2021 used different algorithm versions.

<a id="worldcover-data"></a>
### WORLDCOVER-DATA

- **Title:** *ESA WorldCover data access*
- **Author/owner:** European Space Agency / ESA WorldCover consortium
- **Date:** undated living data page
- **URL:** https://esa-worldcover.org/en/data-access
- **2021 dataset DOI:** https://doi.org/10.5281/zenodo.7254221
- **Accessed:** 2026-08-02
- **Used for:** direct download, dataset version, citation, and CC BY 4.0 reuse route.

## Built-up sources

<a id="ndbi-2003"></a>
### NDBI-2003

- **Title:** “Use of normalized difference built-up index in automatically mapping urban areas from TM imagery”
- **Authors:** Y. Zha, J. Gao, and S. Ni
- **Publication:** *International Journal of Remote Sensing*, volume 24, issue 3
- **Date:** 2003
- **DOI/URL:** https://doi.org/10.1080/01431160304987
- **Accessed:** 2026-08-02
- **Used for:** NDBI formula and the original positive-value built-up direction.

<a id="ibi-2008"></a>
### IBI-2008

- **Title:** “A new index for delineating built-up land features in satellite imagery”
- **Author:** Hanqiu Xu
- **Publication:** *International Journal of Remote Sensing*, volume 29, issue 14
- **Date:** published online 2008-06-14
- **DOI/URL:** https://doi.org/10.1080/01431160802039957
- **Accessed:** 2026-08-02
- **Used for:** Index-based Built-up Index formula, its NDBI/SAVI/MNDWI composition, and the original single-city experimental scope.

<a id="ghsl-2023"></a>
### GHSL-2023

- **Title:** *GHSL Data Package 2023*
- **Author/owner:** European Commission Joint Research Centre
- **Report/date:** JRC133256, 2023
- **Report DOI/URL:** https://doi.org/10.2760/098587
- **Built-surface dataset DOI:** https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA
- **Product page:** https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php
- **Current reuse/citation page:** https://human-settlement.emergency.copernicus.eu/GHSLhowToCite.php
- **Latest release paper:** Pesaresi et al., “Advances on the Global Human Settlement Layer,” 2024, https://doi.org/10.1080/17538947.2024.2390454
- **Accessed:** 2026-08-02
- **Used for:** GHS-BUILT-S R2023A units, 100 m multitemporal epochs, 2018 10 m product, observed/modelled temporal distinctions, CC BY 4.0 reuse, and the requirement to cite both the latest peer-reviewed release and the product-specific dataset rather than only the GHSL website.

## Landsat surface-temperature sources

<a id="landsat-l2-guide"></a>
### LANDSAT-L2-GUIDE

- **Title:** *Landsat 8-9 Collection 2 Level 2 Science Product Guide*
- **Author/owner:** U.S. Geological Survey Landsat Missions
- **Version and date:** version 6, 2024-05-23
- **URL:** https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/LSDS-1619_Landsat8-9-Collection2-Level2-Science-Product-Guide-v6.pdf
- **Accessed:** 2026-08-02
- **Used for:** `ST_B10` scale/offset, algorithm inputs, product levels, QA bands, emissivity dependencies, and limitations.

<a id="landsat-st"></a>
### LANDSAT-ST

- **Title:** *Landsat Collection 2 Surface Temperature*
- **Author/owner:** U.S. Geological Survey Landsat Missions
- **Date:** undated living product page
- **URL:** https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature
- **Dataset DOI:** https://doi.org/10.5066/P9OGBGM6
- **Accessed:** 2026-08-02
- **Used for:** mission date coverage, scale/offset, ASTER GED dependence, stable missing-data locations, cloud-adjacency caveat, public-domain citation, and product credit.

<a id="landsat-stac"></a>
### LANDSAT-STAC

- **Title:** *Landsat Commercial Cloud Data Access*
- **Author/owner:** U.S. Geological Survey Landsat Missions / EROS Center
- **Date:** living page; tutorials published 2024-07-09 and updated access guidance highlighted 2026-01-28
- **URL:** https://www.usgs.gov/landsat-missions/landsat-commercial-cloud-data-access
- **STAC browser:** https://landsatlook.usgs.gov/stac-browser
- **Accessed:** 2026-08-02
- **Used for:** non-Google-Earth-Engine Landsat Collection 2 discovery, COG/STAC availability, AWS requester-pays caveat, and EarthExplorer fallback.

<a id="landsat-public-domain"></a>
### LANDSAT-PUBLIC-DOMAIN

- **Title:** *Are Landsat data in the cloud still considered to be within the public domain?*
- **Author/owner:** U.S. Geological Survey
- **Updated:** 2025-05-15
- **URL:** https://www.usgs.gov/faqs/are-landsat-data-cloud-still-considered-be-within-public-domain
- **Accessed:** 2026-08-02
- **Used for:** public-domain status and requested USGS acknowledgement.

<a id="landsat-schedule"></a>
### LANDSAT-SCHEDULE

- **Title:** *What are the acquisition schedules for the Landsat satellites?*
- **Author/owner:** U.S. Geological Survey Landsat Missions
- **Date:** undated living mission page
- **URL:** https://www.usgs.gov/faqs/what-are-acquisition-schedules-landsat-satellites
- **Accessed:** 2026-08-02
- **Used for:** Landsat 8/9 revisit and approximate local overpass timing.

<a id="nasa-lst"></a>
### NASA-LST

- **Title:** *Land Surface Temperature Anomaly*
- **Author/owner:** NASA Earth Observatory
- **Date:** undated educational science page
- **URL:** https://science.nasa.gov/earth/earth-observatory/global-maps/land-surface-temperature-anomaly/
- **Accessed:** 2026-08-02
- **Used for:** the distinction between surface “skin” temperature and near-surface air temperature.

## Validation and boundary sources

<a id="olofsson-2014"></a>
### OLOFSSON-2014

- **Title:** “Good practices for estimating area and assessing accuracy of land change”
- **Authors:** Pontus Olofsson, Giles M. Foody, Martin Herold, Stephen V. Stehman, Curtis E. Woodcock, and Michael A. Wulder
- **Publication:** *Remote Sensing of Environment*, volume 148
- **Date:** 2014-05-25
- **DOI/URL:** https://doi.org/10.1016/j.rse.2014.02.015
- **Accessed:** 2026-08-02
- **Used for:** probability sampling, design-consistent confusion matrices, user's and producer's accuracy, error-adjusted area, uncertainty intervals, and validation of land-change products.

<a id="soi-abdb"></a>
### SOI-ABDB

- **Title:** *Administrative Boundary Data Base (ABDB)*
- **Author/owner:** Survey of India, Office of the Surveyor General of India
- **Last updated:** 2026-05-29
- **URL:** https://surveyofindia.gov.in/pages/administrative-boundary-data-base-abdb-
- **Accessed:** 2026-08-02
- **Used for:** authoritative Indian state, district, and sub-district boundary source and metadata route.

<a id="soi-catalog"></a>
### SOI-CATALOG

- **Title:** *Survey of India Digital Products – Administrative Boundary Database*
- **Author/owner:** Survey of India
- **Date:** undated living product catalog
- **URL:** https://onlinemaps.surveyofindia.gov.in/Digital_Products.aspx
- **Accessed:** 2026-08-02
- **Used for:** shapefile format, district-level coverage, product identity, and access conditions.

<a id="soi-abdb-metadata"></a>
### SOI-ABDB-METADATA

- **Title:** *Administrative Boundary Database ISO 19115-1 metadata package*
- **Author/owner:** Survey of India, Office of the Surveyor General of India
- **Dataset edition:** 2025; district/subdistrict metadata published 2026-05-06
- **URL:** https://surveyofindia.gov.in/documents/Metadata_ABDB.zip
- **Accessed:** 2026-08-02
- **Used for:** dataset identifiers, edition, harmonization period, scale, stated accuracy, reference system, ownership, copyright constraints, and distribution format. The metadata does not grant public redistribution permission for the geometry.

<a id="ogd-admin-boundaries"></a>
### OGD-ADMIN-BOUNDARIES

- **Title:** *Admin Boundaries*
- **Author/owner:** National Water Informatics Centre, Department of Water Resources, River Development & Ganga Rejuvenation; published through OGD Platform India
- **Published/updated:** 2022-09-28
- **URL:** https://www.data.gov.in/catalog/admin-boundaries
- **Accessed:** 2026-08-02
- **Used for:** government fallback discovery only. The page describes state, district and block boundaries, but its catalog API and ZIP download were disabled at inspection time; no artifact version, fields, checksum, geometry or resource-specific applicability of the Government Open Data License could be verified. It is not an approved processing input yet.

## Open-source license sources

These are candidate-library license records, not approved dependencies. Each exact selected version, native binary, driver, codec, transformation grid, and transitive dependency still requires a release audit.

| Source ID | Title/owner | Date shown | URL | License fact used | Accessed |
|---|---|---|---|---|---|
| `GDAL-LICENSE` | *GDAL License*, OSGeo | undated stable page | https://gdal.org/en/stable/license.html | most GDAL/OGR core is MIT-style; files and compiled dependencies/drivers can have other terms | 2026-08-02 |
| `PROJ-LICENSE` | *PROJ COPYING* and *Resource files*, OSGeo | living repository/docs | https://github.com/OSGeo/PROJ/blob/master/COPYING and https://proj.org/en/stable/resource_files.html | MIT-style package license; external grids may carry separate licenses | 2026-08-02 |
| `PYPROJ-LICENSE` | *pyproj LICENSE*, pyproj contributors | living repository | https://github.com/pyproj4/pyproj/blob/main/LICENSE | MIT | 2026-08-02 |
| `RASTERIO-LICENSE` | *Rasterio LICENSE.txt*, Rasterio/Mapbox contributors | copyright through 2021 in notice | https://github.com/rasterio/rasterio/blob/main/LICENSE.txt | BSD-3-Clause; linked GDAL distribution remains separate | 2026-08-02 |
| `NUMPY-LICENSE` | *NumPy license*, NumPy developers | copyright through 2025 in notice | https://numpy.org/doc/stable/license.html | BSD-3-Clause | 2026-08-02 |
| `SHAPELY-LICENSE` | *Shapely LICENSE.txt* and official documentation, Shapely contributors | living pages | https://github.com/shapely/shapely/blob/main/LICENSE.txt and https://shapely.readthedocs.io/en/stable/index.html | BSD-3-Clause; GEOS dependency documented as LGPL-2.1 | 2026-08-02 |
| `GEOPANDAS-LICENSE` | *GeoPandas LICENSE.txt*, GeoPandas developers | copyright through 2022 in notice | https://github.com/geopandas/geopandas/blob/main/LICENSE.txt | BSD-3-Clause | 2026-08-02 |
| `PYSTAC-CLIENT-LICENSE` | *pystac-client LICENSE*, stac-utils/Jon Duckworth | copyright 2021; Apache License dated 2004-01 | https://github.com/stac-utils/pystac-client/blob/main/LICENSE | Apache-2.0; returned datasets retain separate terms | 2026-08-02 |

## Source exclusions and unresolved evidence

- Secondary tutorials, blog posts, unsourced threshold lists, and vendor marketing pages are not evidence for indicator correctness.
- Search-engine snippets are not cited as evidence; only the linked source is registered.
- No source establishes a universal NDVI, MNDWI, NDBI, IBI, Dynamic World probability, Sentinel-1 dB, cloud-distance, or LST-hotspot threshold. Any such value in SPARC is explicitly a **heuristic** or must be locally calibrated.
- A metadata-only product inventory was generated on 2026-08-02 and is recorded in the [pilot source gate](pilot-source-gate.md). Scene cloud metadata does not establish clear district coverage; actual common-valid coverage and threshold stability remain unconfirmed until approved geometry and imagery are processed.
