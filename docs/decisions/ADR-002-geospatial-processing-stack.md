# ADR-002: Pinned Python geospatial processing stack

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Codex workstream
- **Applies to:** Offline/precomputed processing and a future worker

## Context

P0 must transform selected satellite observations and administrative boundaries into defensible water, vegetation and built-up proxy summaries within a short implementation window. The team should reuse mature geospatial libraries rather than build raster readers, coordinate transformations, vector topology, STAC pagination or image-processing algorithms.

Geospatial Python packages depend on native GDAL/GEOS binaries and compatible NumPy wheels. Installing unpinned packages on the event day is a predictable delivery risk. Conversely, adding multidimensional/distributed frameworks for two period composites would increase complexity without a demonstrated need.

## Decision drivers

- Correct, established format/CRS behavior.
- Smallest maintainable P0 dependency set.
- Windowed processing rather than full-scene memory loading.
- Reproducible container build and version manifest.
- Permissive open-source licenses.
- Clear upgrade path to production workers.

## Decision

Use a pinned, container-tested Python processing environment built around:

| Dependency | Purpose | License and attribution | Maintenance signal as of 2026-08-02 | P0 decision | Production/fallback |
|---|---|---|---|---|---|
| GDAL command-line tools | Inspect, warp/translate, build and validate geospatial rasters/COGs | MIT-style; retain license and notices for bundled dependencies | Active; official releases continued in July 2026 | Selected for deterministic build steps | Continue; use Rasterio where its API is clearer |
| Rasterio | Windowed raster reads/writes, masks, transforms and reprojection | BSD-3-Clause | Active; current main documents modern Python/NumPy/GDAL requirements | Selected | Continue with pinned ABI matrix; GDAL CLI fallback |
| GeoPandas | Boundary reads, joins and district-scale vector aggregation | BSD-3-Clause | Active 1.x releases | Selected | Continue for modest data; PostGIS/SQL when scale requires |
| Shapely | Geometry validity, intersection and topology operations | BSD-3-Clause; linked GEOS is LGPL-2.1 | Active 2.x releases | Selected | Continue; PostGIS fallback for server-scale spatial queries |
| NumPy | Index algebra, boolean QA masks and numeric aggregation | BSD-3-Clause | Active core scientific project | Selected | Continue; require windowing/chunk discipline |
| scikit-image | Otsu threshold and narrowly scoped morphology/connected-component operations | BSD-3-Clause | Active 0.26 release line | Conditional, only where methodology calls for it | A documented fixed threshold/NumPy rule is the simpler fallback |
| pystac-client | STAC search, pagination and Item/Asset models | Apache-2.0 | Active 0.9 documentation/repository | Selected | Direct standards-compliant HTTP only if a provider incompatibility is demonstrated |

Retain library LICENSE/NOTICE files and an environment/SBOM manifest. Data and basemap attribution are separate obligations and must appear in result/layer provenance.

## Processing boundaries

- GDAL CLI is preferred for explicit translation/warping/COG inspection steps. Avoid raw Python GDAL bindings unless a capability is unavailable through Rasterio or the CLI.
- Rasterio reads only required bands/windows and owns raster metadata/masks in Python.
- GeoPandas/Shapely handle versioned administrative boundaries and small zonal-vector outputs.
- NumPy performs index/mask arithmetic. Non-finite denominators become nodata, not serialized infinity.
- scikit-image is introduced only for a cited, versioned method. It is not a reason to hide an unsupported threshold.
- pystac-client stays behind the provider adapter; provider-specific authentication/extensions remain explicit.
- Area/statistics use an appropriate projected/equal-area CRS. RFC 7946 WGS 84 GeoJSON is an exchange/display format, not an area-calculation CRS.

## Deferred dependencies

| Dependency | Why useful later | Why deferred from P0 | Fallback/current approach |
|---|---|---|---|
| Xarray | Labelled multidimensional/time-series arrays | Two composites do not justify its model and dependency surface | Rasterio + NumPy |
| rioxarray | CRS/nodata/clip operations on Xarray | Inherits unnecessary Xarray complexity | Rasterio |
| Dask | Parallel/distributed chunk computation | No measured workload or cluster requirement; operational complexity | Windowed serial/bounded parallel tasks |
| rio-tiler | Dynamic COG tile reads | Static P0 layers are simpler and more reliable | Prebuilt XYZ or bounded image overlays |
| TiTiler | Ready FastAPI COG tile endpoints | Adds serving/SSRF/cache/operations concerns; no P0 need | Static layers; later wrap `titiler.core` behind an opaque registry |
| DuckDB Spatial | Local analytical SQL | Not required for the main pipeline or runtime | GeoPandas/Rasterio and optional analyst use |
| PostGIS | Durable concurrent spatial query | Runtime database is unnecessary for two demo packs | Static artifacts; production migration |
| Celery/Redis or another queue | Durable asynchronous jobs | Live processing is not required for the critical demo | Offline CLI/precompute; later choose from measured needs |

The old TiTiler metapackage name must not be copied from stale examples; current TiTiler documentation separates packages such as `titiler.core` and `titiler.application`. No TiTiler package is installed for P0.

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Handwritten raster/vector processing | Few declared dependencies | Reimplements mature format, CRS and topology behavior; high correctness risk | Rejected |
| Full Xarray/rioxarray/Dask stack | Strong for time cubes and distributed workloads | Unnecessary abstraction/ABI/deployment surface for two-period district analysis | Deferred |
| Database-centric PostGIS raster pipeline | Central SQL operations and concurrency | Service setup and raster-database complexity are not justified for P0 | Deferred |
| Hosted-only processing platform | Avoids local native setup | Account/quota/vendor/outage dependency and weaker offline reproducibility | Rejected as a required path |
| Pinned GDAL/Rasterio/GeoPandas/Shapely/NumPy stack | Mature, focused, portable and compatible with future workers | Requires disciplined binary pinning and container build | **Selected** |

## Consequences

### Positive

- Established CRS, raster and geometry behavior replaces bespoke code.
- One processing package can run in a local build step and later a worker.
- Windowed reads keep memory proportional to the region/chunk rather than whole scenes.
- Permissive licenses suit prototype and production distribution when notices are retained.

### Negative and trade-offs

- Native GDAL/GEOS compatibility and image size require build discipline.
- GeoPandas is not a national-scale concurrent query engine.
- Python processing may need later profiling/parallelization for many regions.
- A container does not guarantee scientific reproducibility unless inputs, parameters and versions are also recorded.

## Build and verification constraints

1. Select an exact Python version only after the current Rasterio/GDAL/NumPy compatibility matrix succeeds; current Rasterio main requirements make Python 3.12 a likely baseline, not an untested promise.
2. Lock Python packages and OS/native dependencies. Record image digest, GDAL/PROJ/GEOS versions and package list.
3. Build from an official Python base and install native libraries explicitly. Do not use the deprecated FastAPI `uvicorn-gunicorn` base image for the planned API.
4. Build and exercise the image before the event; cache/export it so event-day network installation is unnecessary.
5. Test CRS transforms, pixel alignment, nodata, scale/offset, band mapping, non-finite math, area units, deterministic output and representative known fixtures.
6. Keep processing outside HTTP request handlers.

## Reversal conditions

Add Xarray/rioxarray, distributed execution, dynamic tiling or a database only after a concrete P1/production use case and measured workload justify the dependency. Replacing a core library requires equivalent format/CRS correctness, licensing, maintenance and regression evidence.

## Sources

Official project sources were accessed on 2026-08-02.

- [GDAL overview, downloads and license — OSGeo](https://gdal.org/en/stable/about.html), [license](https://gdal.org/en/stable/license.html), [downloads](https://gdal.org/en/stable/download.html).
- [Rasterio repository — Rasterio contributors](https://github.com/rasterio/rasterio). Requirements, BSD-3-Clause license and maintenance activity.
- [GeoPandas repository — GeoPandas contributors](https://github.com/geopandas/geopandas). BSD-3-Clause license and releases.
- [Shapely repository — Shapely contributors](https://github.com/shapely/shapely). BSD-3-Clause license, GEOS dependency and releases.
- [NumPy repository — NumPy developers](https://github.com/numpy/numpy). BSD-3-Clause license and maintenance.
- [scikit-image repository — scikit-image contributors](https://github.com/scikit-image/scikit-image). BSD-3-Clause license and releases.
- [pystac-client documentation — STAC utilities contributors](https://pystac-client.readthedocs.io/en/latest/). API behavior and current version; [Apache-2.0 license](https://github.com/stac-utils/pystac-client/blob/main/LICENSE).
- [Xarray repository — Xarray contributors](https://github.com/pydata/xarray). Apache-2.0 license and maintenance.
- [rioxarray documentation — rioxarray contributors](https://corteva.github.io/rioxarray/latest/). Rasterio/Xarray integration and Apache-2.0 licensing.
- [rio-tiler documentation — Development Seed](https://cogeotiff.github.io/rio-tiler/latest/). COG/STAC tile-reading capability and BSD-3-Clause license.
- [TiTiler getting started — Development Seed](https://developmentseed.org/titiler/user_guide/getting_started/). Current package structure and MIT license.

