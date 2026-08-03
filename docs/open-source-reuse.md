# SPARC open-source and data-reuse plan

**Status:** planning review only; no dependency, source code, model, or dataset has been added  
**Evidence cut-off and license-page access date:** 2026-08-02

## Decisions

- **DECISION:** SPARC will not copy implementation code from research papers, notebooks, tutorials, or unreviewed repositories.
- **DECISION:** index and area algorithms will be independently implemented from the cited equations and product specifications.
- **DECISION:** Google Earth Engine is the worker-only primary platform for Sentinel-2 processing. Dynamic World remains optional comparison material only.
- **DECISION:** software license, linked native library license, transformation-grid license, dataset license, and imagery/reference license are separate obligations and must be audited separately.
- **DECISION:** no candidate in this document is approved merely by being listed. Approval occurs only after an exact version/build is pinned, its transitive artifacts are inventoried, and required notices are generated.

## Candidate processing components

These are boring, established candidates for a future offline/server-side geospatial worker. The repository currently contains no implementation from which a final language or dependency set can be confirmed.

| Candidate | Potential use | License fact and authoritative source | Reuse consequence | Planning status |
|---|---|---|---|---|
| GDAL | raster/vector I/O, warp, COG creation | Most core GDAL/OGR code uses an MIT-style license; individual files and compiled drivers can have other licenses. *GDAL License*, OSGeo, undated stable documentation, accessed 2026-08-02: https://gdal.org/en/stable/license.html | Retain notices for redistributed code/binaries. Audit the actual binary, drivers, codecs, and native dependencies; “GDAL is MIT” is not a complete distribution audit. | candidate |
| PROJ | CRS transformations | MIT-style terms cover the PROJ package; external transformation grids can carry separate terms. *PROJ COPYING* and *Resource files*, OSGeo, living repository/docs, accessed 2026-08-02: https://github.com/OSGeo/PROJ/blob/master/COPYING and https://proj.org/en/stable/resource_files.html | Retain notice. Inventory every shipped grid and its source/license. | candidate |
| pyproj | Python interface to PROJ | MIT. *pyproj LICENSE*, pyproj contributors, living repository, accessed 2026-08-02: https://github.com/pyproj4/pyproj/blob/main/LICENSE | Retain notice and separately comply with PROJ/grid terms. | candidate if Python is selected |
| Rasterio | windowed raster I/O and masking | BSD-3-Clause. *Rasterio LICENSE.txt*, Rasterio/Mapbox contributors, living repository, accessed 2026-08-02: https://github.com/rasterio/rasterio/blob/main/LICENSE.txt | Retain/reproduce license and disclaimer; no endorsement. Audit linked GDAL build. | candidate if Python is selected |
| NumPy | array/index arithmetic | BSD-3-Clause. *NumPy license*, NumPy developers, copyright through 2025 in the current notice, accessed 2026-08-02: https://numpy.org/doc/stable/license.html | Retain/reproduce notice and disclaimer; no endorsement. | candidate if Python is selected |
| Shapely | geometry validation and clipping | BSD-3-Clause; official documentation states its GEOS dependency uses LGPL-2.1. *Shapely LICENSE.txt* and *Shapely documentation*, Shapely contributors, living pages, accessed 2026-08-02: https://github.com/shapely/shapely/blob/main/LICENSE.txt and https://shapely.readthedocs.io/en/stable/index.html | Retain Shapely notice and audit/comply with the exact GEOS binary distribution. | candidate if Python is selected |
| GeoPandas | tabular vector preparation | BSD-3-Clause. *GeoPandas LICENSE.txt*, GeoPandas developers, living repository, accessed 2026-08-02: https://github.com/geopandas/geopandas/blob/main/LICENSE.txt | Retain/reproduce notice; audit pandas, Shapely, pyproj, and file-format dependencies separately. | optional convenience layer |
| pystac-client | STAC discovery | Apache-2.0. *pystac-client LICENSE*, stac-utils/Jon Duckworth, copyright 2021; Apache License dated 2004-01, accessed 2026-08-02: https://github.com/stac-utils/pystac-client/blob/main/LICENSE | Include Apache-2.0, mark modifications, retain applicable notices, and reproduce NOTICE content when present. Dataset assets returned by STAC retain their own terms. | optional; plain HTTP is sufficient for P0 |

None of these permissive software licenses requires a visible map attribution merely because the library ran. Their notice obligations become relevant when SPARC redistributes source, wheels, native libraries, containers, installers, or bundled binaries. The exact pinned distribution—not the headline license—controls the audit.

## Cross-stack recommendation matrix

The following table closes the implementation decision for each recommended direct dependency. “Active” describes evidence at the 2026-08-02 cut-off, not a permanent guarantee; exact versions, transitive dependencies, and current project status must be rechecked when the lockfiles are created. Dataset and basemap attribution remains separate from software-license notices.

| Dependency | Purpose and component | License and attribution | Maintenance evidence | Advantages | Limitations | Prototype suitability | Production suitability | Alternative or fallback |
|---|---|---|---|---|---|---|---|---|
| GDAL | Server/offline raster and vector I/O, reprojection, and COG creation | Core is MIT-style; retain notices and audit the exact drivers/codecs/native build ([official license](https://gdal.org/en/stable/license.html)) | Active official releases/docs at cut-off | Mature format and CRS support; avoids custom geospatial I/O | Native packaging and driver licenses require care | Required indirectly/directly, with a pinned build | Suitable with a tested image/SBOM and security updates | Provider-side conversion for a narrow case; no credible full custom replacement |
| PROJ + pyproj | Server/offline CRS selection and transformations | PROJ MIT-style and pyproj MIT; retain notices and audit shipped grids ([PROJ terms](https://github.com/OSGeo/PROJ/blob/master/COPYING), [pyproj terms](https://github.com/pyproj4/pyproj/blob/main/LICENSE)) | Active official projects at cut-off | Authoritative transformation machinery and Python integration | Grid files have separate licenses; wrong CRS still produces wrong area | Selected; pin with the GDAL stack | Suitable with grid/version provenance | GDAL transformation APIs, which still use PROJ underneath |
| Rasterio | Server/offline windowed raster reads, masks, warps, and outputs | BSD-3-Clause; retain notice; linked GDAL obligations remain ([official license](https://github.com/rasterio/rasterio/blob/main/LICENSE.txt)) | Active official project at cut-off | Pythonic, established, works well for district-scale windows | Native GDAL compatibility and memory discipline matter | Selected core P0 library | Suitable for bounded workers; distributed scale may need a different execution layer | Direct GDAL Python API, with more verbose application code |
| NumPy | Shared processing arithmetic for indices, masks, and summaries | BSD-3-Clause; retain notice ([official license](https://numpy.org/doc/stable/license.html)) | Active official project at cut-off | Fast, stable array primitives; keeps formulas transparent | Does not provide CRS, raster metadata, or out-of-core policy | Selected core P0 library | Suitable as a numerical foundation | Rasterio masked arrays still rely on NumPy |
| Shapely | Server/offline geometry validity, clipping, and intersections | BSD-3-Clause; retain notice; audit linked GEOS LGPL terms ([official license](https://github.com/shapely/shapely/blob/main/LICENSE.txt)) | Active official 2.x project at cut-off | Proven topology operations; avoids handwritten geometry logic | Invalid inputs and CRS misuse remain application responsibilities | Selected for boundary preparation | Suitable for bounded workers; PostGIS can serve concurrent queries later | GDAL/OGR geometry operations or production PostGIS |
| GeoPandas | Server/offline boundary tables, joins, and district/subdistrict aggregation | BSD-3-Clause; retain notice and audit pandas/Shapely/pyproj ([official license](https://github.com/geopandas/geopandas/blob/main/LICENSE.txt)) | Active official 1.x project at cut-off | Concise tabular vector workflow for a small pilot | Adds a dataframe layer and is not a serving database | Selected convenience layer for P0 | Suitable for batch jobs of measured size | Shapely + pyogrio/Rasterio; PostGIS when concurrency justifies it |
| pystac-client | Server/offline catalog discovery adapter | Apache-2.0; include license/NOTICE and mark modifications where required ([official license](https://github.com/stac-utils/pystac-client/blob/main/LICENSE)) | Active official project at cut-off | Handles STAC search/pagination without inventing a client | Does not grant data rights or normalize every provider quirk | Selected if the CDSE compatibility spike passes | Suitable behind a provider adapter with retries and telemetry | Small standards-compliant HTTP client using the provider's live schema |
| scikit-image | Server/offline Otsu and narrowly justified cleanup operations | BSD-3-Clause; retain notice ([official repository](https://github.com/scikit-image/scikit-image)) | Active 0.26 line at cut-off | Tested image algorithms avoid custom morphology/threshold code | Easy to hide unsupported heuristics; adds binary dependencies | Conditional only where the frozen methodology names it | Suitable when versioned and regression-tested | Fixed documented threshold and explicit NumPy/Rasterio operations |
| FastAPI + Pydantic | Planned server/backend HTTP routing and authoritative request/response validation | Both MIT; retain notices ([FastAPI](https://github.com/fastapi/fastapi), [Pydantic](https://github.com/pydantic/pydantic)) | Active official projects/current docs at cut-off | Strong Python fit, schema support, small modular-monolith surface | Runtime-generated OpenAPI can drift from the reviewed contract; native geospatial work must not block handlers | Selected for the P0 read API, but not required by the offline static path | Suitable with pinned workers, limits, observability, and contract-diff checks | A static HTTP bundle for demo; another framework only after proving identical contract behavior |
| React | Browser/client components and stateful dashboard views | MIT; retain notice ([official license](https://github.com/facebook/react/blob/main/LICENSE)) | Active official project at cut-off | Established component ecosystem and team fit | Accessibility and data-flow correctness are not automatic | Selected | Suitable with measured performance and maintained upgrades | Standards-based static pages for recovery; framework replacement is not justified during the event |
| TypeScript | Browser/client static type checking and shared generated contract types | Apache-2.0; retain license/NOTICE obligations ([official repository](https://github.com/microsoft/TypeScript)) | Active official project at cut-off | Detects many contract/use errors before runtime | Types do not validate untrusted JSON at runtime | Selected | Suitable with strict settings and runtime schema validation | JavaScript plus runtime schemas, with weaker editor/build checks |
| Vite | Build/configuration for the static React bundle and development server | MIT; retain notice ([official repository](https://github.com/vitejs/vite)) | Active official project at cut-off | Fast, simple static build and clear public environment prefix | The preview server is not a production server; `VITE_*` values are public | Selected | Suitable for static/CDN output with a real host | Any standards-based static server can serve the built recovery bundle |
| MapLibre GL JS | Browser/client two-dimensional raster, image, and vector map | BSD-3-Clause; retain software notice and separately show map/data attribution ([official repository](https://github.com/maplibre/maplibre-gl-js)) | Active; v6 released 2026-07-22 with ESM/WebGL2 changes | Open renderer, useful source/layer model, avoids proprietary runtime lock-in | WebGL and version compatibility risk; map accessibility needs text/table alternatives | Selected only after pinning a tested pre-v6 release | Re-evaluate current major version after compatibility/performance tests | Static georeferenced images and tables; Leaflet only if the compatibility spike fails |
| Recharts | Browser/client comparison and optional time-series charts | MIT; retain notice ([official repository](https://github.com/recharts/recharts)) | Active 3.x line at cut-off | Fits React and modest result arrays | SVG/chart defaults do not provide a complete accessible explanation | Selected with adjacent semantic table/text | Suitable for modest datasets; reassess for very large series | Plain HTML table/summary; another chart library only for a measured missing capability |

These choices are not authorization to install packages during planning. The implementation owner must record the exact version, direct reason, transitive/native surface, lockfile diff, and fallback before adding each dependency. Architecture rationale and rejected/deferred packages are detailed in [ADR-002](decisions/ADR-002-geospatial-processing-stack.md) and [ADR-005](decisions/ADR-005-map-library.md).

## Algorithm reuse

| Method | SPARC reuse approach | Evidence |
|---|---|---|
| NDWI/MNDWI | independently implement the published formula and cite the original papers | [NDWI-1996](research/source-register.md#ndwi-1996), [MNDWI-2006](research/source-register.md#mndwi-2006) |
| AWEI | independently implement both published equations; mark unchanged Sentinel-2 coefficients as a transfer assumption | [AWEI-2014](research/source-register.md#awei-2014) |
| NDVI/EVI | independently implement equations using decoded surface reflectance | [NDVI-USGS](research/source-register.md#ndvi-usgs), [EVI-2002](research/source-register.md#evi-2002) |
| NDBI/IBI | independently implement equations and document that original studies do not validate Nagpur transfer | [NDBI-2003](research/source-register.md#ndbi-2003), [IBI-2008](research/source-register.md#ibi-2008) |
| Otsu threshold | independently implement or use an approved library implementation; cite the original method | [OTSU-1979](research/source-register.md#otsu-1979) |
| Error-adjusted area | implement the actual design-consistent estimator, not an unattributed blog simplification | [OLOFSSON-2014](research/source-register.md#olofsson-2014) |

Research-paper PDFs, publisher figures/tables, and third-party notebook code are not project assets and must not be copied into SPARC. Bibliographic citation does not grant code or figure redistribution rights.

## Dataset and product obligations

### Copernicus Sentinel-1/2

Copernicus Sentinel access is free, full, and open under the Sentinel legal framework, subject to the legal notice. Public adapted outputs should carry:

```text
Contains modified Copernicus Sentinel data [year(s)]
```

For an unmodified public data display, use `Copernicus Sentinel data [year]`. Source: *Sentinel Data Legal Notice*, European Union/European Space Agency, regulations referenced 2013/2014, and current CDSE attribution FAQ, undated living pages, accessed 2026-08-02: [SENTINEL-LEGAL](research/source-register.md#sentinel-legal), [CDSE-TERMS](research/source-register.md#cdse-terms), [CDSE-ATTRIBUTION](research/source-register.md#cdse-attribution).

Do not imply that the European Union or ESA endorses SPARC, and preserve source/product IDs so the notice is auditable.

### Landsat 8/9 Collection 2 Level-2

USGS Landsat data are public domain and have no use/redistribution restriction; USGS requests acknowledgement. *Are Landsat data in the cloud still considered to be within the public domain?*, U.S. Geological Survey, updated 2025-05-15, accessed 2026-08-02: [LANDSAT-PUBLIC-DOMAIN](research/source-register.md#landsat-public-domain).

Use the dataset citation:

```text
Earth Resources Observation and Science (EROS) Center. (2020).
Landsat 8-9 Operational Land Imager / Thermal Infrared Sensor Level-2,
Collection 2 [dataset]. U.S. Geological Survey.
https://doi.org/10.5066/P9OGBGM6
```

Recommended image credit:

```text
Landsat Collection 2 Level-2 image courtesy of the U.S. Geological Survey.
```

The product citation and credit route are documented on the USGS Collection 2 surface-temperature page. ([LANDSAT-ST](research/source-register.md#landsat-st))

### Dynamic World V1 — optional only

Dynamic World is CC BY 4.0. If an optional export is shared or displayed, include both provider attribution and the modified-Sentinel notice:

```text
This dataset is produced for the Dynamic World Project by Google in partnership
with National Geographic Society and the World Resources Institute.
Contains modified Copernicus Sentinel data [2015-present].
```

Also link CC BY 4.0, identify changes, and cite Brown et al. Source: *Dynamic World V1 dataset catalog*, Google, undated living catalog, accessed 2026-08-02, and original paper dated 2022-06-09. ([DW-CATALOG](research/source-register.md#dw-catalog), [DW-2022](research/source-register.md#dw-2022))

### ESA WorldCover

WorldCover is CC BY 4.0. A published map should carry the product owner's wording:

```text
© ESA WorldCover project [year] / Contains modified Copernicus Sentinel data
([year]) processed by ESA WorldCover consortium
```

Use `2021` for v200, link CC BY 4.0, identify modifications, and cite the 2021 dataset DOI. Source: *ESA WorldCover data access*, ESA WorldCover consortium, undated living page, accessed 2026-08-02. ([WORLDCOVER-DATA](research/source-register.md#worldcover-data))

### JRC Global Surface Water

The current product is provided free of charge without use restrictions under the Copernicus framework. Publications/models/products must cite the dataset and Pekel et al.; published maps require:

```text
Source: EC JRC/Google
```

Source: *Global Surface Water – Data Access and Data Update Notes (1984–2024)*, European Commission Joint Research Centre/Google, v1.5/2024 living page, accessed 2026-08-02. ([GSW-2024](research/source-register.md#gsw-2024), [GSW-2016](research/source-register.md#gsw-2016))

### GHSL

Current GHSL reuse guidance licenses the data under CC BY 4.0 and requires appropriate credit, modification indication, and no implied endorsement. It explicitly requires both the latest peer-reviewed GHSL release reference and the product-specific dataset citation; citing only the generic GHSL website is insufficient.

For GHS-BUILT-S R2023A include:

- Pesaresi and Politis (2023), *GHS-BUILT-S R2023A*, European Commission Joint Research Centre, https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA
- Pesaresi et al. (2024), “Advances on the Global Human Settlement Layer,” https://doi.org/10.1080/17538947.2024.2390454

Sources: *GHSL use conditions and citation*, European Commission Joint Research Centre, undated living page, accessed 2026-08-02, https://human-settlement.emergency.copernicus.eu/GHSLhowToCite.php; and [GHSL-2023](research/source-register.md#ghsl-2023).

### geoBoundaries India ADM2 boundary

SPARC’s prototype district geometry comes from the pinned geoBoundaries gbOpen India ADM2 release `IND-ADM2-76128533`. Although geoBoundaries describes gbOpen generally as CC BY 4.0, the selected release's source metadata records ODbL 1.0. Treat the selected geometry as ODbL: preserve its attribution and applicable share-alike obligations, and do not label it CC BY-only. Include the boundary disclaimer in every release: “This boundary is suitable for prototype analysis but is not an authoritative legal or cadastral boundary.” No Survey of India ABDB geometry is used or redistributed. ([GBOPEN-IND-ADM2](research/source-register.md#gbopen-ind-adm2))

## Reference-imagery licensing

Validation imagery is a separate licensed input. A service allowing interactive viewing does not automatically permit screenshot redistribution, annotation-dataset publication, model training, or derived-tile hosting.

For every validation source, record:

```text
provider
product
acquisitionDate
termsUrl
licenseVersion
allowedUses
redistributionRule
screenshotRule
attribution
accessDate
```

If these cannot be established, use the imagery for no more than the explicitly permitted purpose and do not place it in Git, exported reports, or public sample datasets.

## Distribution audit

Before any public build, container, archive, or hosted dataset:

1. Generate an exact dependency lock/SBOM.
2. Inventory JavaScript/Python packages, native libraries, GDAL drivers, codecs, PROJ grids, model files, fonts, icons, map tiles, and datasets.
3. Resolve each artifact to a license and source revision.
4. Check copyleft and source-offer obligations for the exact linked/distributed form.
5. Preserve required copyright, permission, disclaimer, NOTICE, and attribution text.
6. Mark modified CC BY or Apache-licensed material as required.
7. Verify that provider names/logos are not used to imply endorsement.
8. Confirm commercial-use and hosting/redistribution rights separately.
9. Scan repository and build output for copied data, credentials, and license files that were omitted.
10. Block release on `UNKNOWN`, `NOASSERTION`, incompatible terms, or missing source/license provenance.

## Proposed third-party notice structure

```text
SPARC Third-Party Notices

Software
- name, exact version, source URL, license, copyright, required notice

Data
- product, provider, version/date, DOI, license, attribution, modifications

Research methods
- method, original citation and DOI

Validation references
- provider, permitted use, non-redistribution restrictions
```

## Explicitly prohibited shortcuts

- Calling all GDAL-based binaries “MIT” without auditing drivers and native libraries.
- Treating a STAC client's license as permission to redistribute assets returned by the catalog.
- Committing imagery because it is publicly viewable.
- Removing attribution from clipped, reprojected, classified, or composited products.
- Treating public domain as permission to omit scientific provenance.
- Adding a Google Earth Engine service-account key to the repository or making Dynamic World required.
- Copying paper/notebook code without verifying its license and origin.
- Redistributing the selected geoBoundaries geometry without ODbL attribution and applicable share-alike treatment.
