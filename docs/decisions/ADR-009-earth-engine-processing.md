# ADR-009: Google Earth Engine for primary offline processing

- **Status:** Accepted
- **Date:** 2026-08-02
- **Supersedes:** ADR-001 for primary Sentinel-2 discovery and processing

## Decision

SPARC uses Google Earth Engine (GEE) as the primary offline worker for Sentinel-2 Level-2A discovery, masking, compositing, indicator calculation and controlled export. The worker uses `COPERNICUS/S2_SR_HARMONIZED`; direct Copernicus Data Space STAC remains a fallback metadata/discovery path.

## Why

The authenticated project successfully queried the selected collection for every fixed Nagpur and Bengaluru Urban window. GEE removes the immediate need to download, parse and reconcile hundreds of source rasters on the development machine.

## Boundaries

- GEE runs only in the offline/server worker, never in the Vite/Three.js browser, FastAPI request path or shipped demo.
- `EARTH_ENGINE_PROJECT` is configuration, not a browser variable. OAuth tokens and any service-account key stay in the local/user or deployment secret store and are never committed, logged, returned, or put in a manifest.
- The released demo still consumes immutable local outputs and works with GEE, internet and API access unavailable.
- GEE scene-cloud metadata is only a prefilter. Per-pixel cloud/shadow masking, common-valid support, fixed dates and scientific validation remain mandatory.
- The approved district polygon and public redistribution basis are still blocked; a broad search envelope is not a substitute for it.

## Consequences

This replaces the direct-CDSE raster path as the primary implementation route. It introduces GEE project access, quota and terms as a build-time dependency, so the project preserves both the CDSE fallback script and verified offline package path.

## Sources

- [Earth Engine access and Cloud-project requirements](https://developers.google.com/earth-engine/guides/access)
- [Harmonized Sentinel-2 Level-2A surface-reflectance collection](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Earth Engine authentication](https://developers.google.com/earth-engine/guides/auth)
