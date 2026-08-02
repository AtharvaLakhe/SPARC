# ADR-005: MapLibre for P0 maps with a static analytical fallback

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Claude/frontend workstream, architecture reviewed by Shared
- **Applies to:** Two-dimensional analytical maps, map layers and chart companion views

## Context

SPARC needs an interactive map for district/block boundaries, before/after imagery and change overlays. P0 has a small, bounded set of GeoJSON and static raster/XYZ layers, not millions of animated features. The map must work with precomputed local assets and must not make a public basemap service or WebGL the only route to the analytical evidence.

MapLibre GL JS is actively maintained and permissively licensed. Its v6 release in July 2026 changed distribution/browser assumptions to ESM-only and WebGL2-only. Adopting an untested `latest` version days before a hackathon would create avoidable compatibility risk.

## Decision drivers

- First-class raster and vector web-map rendering.
- Local/static source support and provider-neutral layer descriptors.
- Permissive license and active maintenance.
- Reasonable React integration without requiring a second visualization engine.
- Accessible non-map equivalents and WebGL fallback.
- Predictable event build through exact version pinning.

## Decision

1. Use MapLibre GL JS for the P0 two-dimensional map.
2. During implementation, pin an exact tested pre-v6 (5.x) version in the lockfile after a browser/device compatibility spike. Do not use `latest`, a caret range that can cross a major release, or v6 by default during the event.
3. Re-evaluate MapLibre v6 for production only after ESM bundling, WebGL2 coverage, accessibility, performance and offline builds pass the supported-browser matrix.
4. Use MapLibre-native raster/image and GeoJSON/vector layers for P0. Do not add deck.gl unless a measured feature-count/visualization requirement exceeds MapLibre's tested capability.
5. Use Recharts for simple comparison/time-series charts, paired with semantic values, summaries and tables. Recharts is not a substitute for a map or for accessible text.
6. Load layers from SPARC `LayerDescriptor` objects with opaque `layerId`, bounds, representation, legend, attribution, checksum/content version and relative/approved URLs.
7. Do not allow the UI or a tile service to fetch an arbitrary caller-supplied URL.
8. Do not prefetch/package public `tile.openstreetmap.org` tiles. P0 may use an expressly licensed bundled context layer or a neutral background.
9. Provide a reviewed static before/after/change image, metrics, legend, provenance and table fallback when WebGL, map initialization or a layer fails.

## Rendering responsibilities

| Layer/content | P0 implementation | Fallback |
|---|---|---|
| District/block boundary | Small versioned GeoJSON | Text hierarchy and static outlined image |
| Before/after observation | Bounded image source or small XYZ set | Side-by-side static images with dates |
| Indicator/change layer | Image/raster/XYZ or small GeoJSON | Static change image plus data table |
| Legend and units | HTML outside the canvas, driven by descriptor | Same HTML remains visible |
| Attribution/provenance | Persistent visible attribution plus details panel | Same text remains visible |
| Chart | Recharts SVG for modest arrays | Semantic table and plain-language summary |

Analytical meaning must not depend only on hover, color, movement or map interaction.

## Dependency and licensing record

| Component | License | Maintenance signal as of 2026-08-02 | Attribution obligation |
|---|---|---|---|
| MapLibre GL JS | BSD-3-Clause | Active official repository; v6 released 2026-07-22 | Retain code license in distributions. Separately show data/basemap attribution required by each source |
| Recharts | MIT | Active 3.x releases in 2026 | Retain license; source data attribution remains separate |
| deck.gl | MIT | Active 9.x project | Not selected for P0; retain license if later introduced |
| CesiumJS | Apache-2.0 | Active monthly releases | Not selected as P0 2D map; Cesium ion/service terms are separate if ever used |

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Static images only | Maximum reliability and accessibility | No pan/zoom/layer interaction | Required fallback, not primary map |
| Leaflet | Mature lightweight 2D map model | Raster/vector styling and WebGL integration differ; changing the fixed project choice adds evaluation work | Viable fallback if MapLibre spike fails, not selected |
| MapLibre GL JS | Open renderer, raster/vector sources, style ecosystem, active maintenance | WebGL dependency; major v6 compatibility change | **Selected with exact tested pre-v6 pin** |
| deck.gl plus MapLibre | Advanced GPU layers and large-data capability | Extra bundle/runtime/API complexity with no P0 scale need | Deferred |
| CesiumJS | Geospatial globe/3D Tiles capability | Large optional 3D concern; user assets unknown; unnecessary for district 2D analytics | Not selected for core map |
| Hosted proprietary map SDK | Polished hosted data/services | Token, pricing, network and licensing dependency | Rejected for critical demo path |

## Consequences

### Positive

- One map engine covers P0 vector, image and raster/XYZ needs.
- Static local layers align with offline/demo architecture.
- Exact version pin prevents an event-day major-version surprise.
- Text/image/table fallback keeps the story available without WebGL.

### Negative and trade-offs

- The selected pre-v6 release does not receive v6-only improvements until a controlled migration.
- WebGL and GPU behavior still varies across devices and requires rehearsal.
- An offline basemap requires explicit compatible licensing or omission.
- Map accessibility requires HTML controls/summaries; the canvas alone is insufficient.

## Implementation constraints

- Run a browser/device spike before locking the exact 5.x release.
- Bundle library code locally; no runtime CDN.
- Use a stable style and source IDs, bounds and zoom caps from the contract.
- Ensure `transformRequest` or equivalent cannot add secrets to arbitrary hosts.
- Restrict layer origins and protocols; prefer same-origin/approved CDN relative URLs.
- Test context loss, missing/corrupt tiles, keyboard controls, reduced motion, high zoom, small screens and color contrast.
- Attribute all datasets/basemaps visibly and in provenance.
- Do not describe display interpolation as increased satellite resolution.

## Reversal conditions

Move to MapLibre v6 after a planned migration passes supported WebGL2 browsers, Vite ESM build, offline package, performance and fallback tests. Add deck.gl only after measured P1 scale/visual requirements. Replace MapLibre only if the compatibility spike fails and a fallback satisfies the same contract, license, offline and accessibility requirements.

## Sources

Official project/policy sources were accessed on 2026-08-02.

- [MapLibre GL JS documentation — MapLibre](https://maplibre.org/maplibre-gl-js/docs/). Rendering and source/layer API.
- [MapLibre GL JS repository and releases — MapLibre](https://github.com/maplibre/maplibre-gl-js). BSD-3-Clause license, maintenance and v6 release changes.
- [Recharts repository and releases — Recharts Group](https://github.com/recharts/recharts). MIT license and active 3.x maintenance.
- [deck.gl documentation and repository — vis.gl](https://deck.gl/docs), [repository](https://github.com/visgl/deck.gl). Advanced layer capabilities and MIT license.
- [CesiumJS repository — CesiumGS](https://github.com/CesiumGS/cesium). Apache-2.0 library license and release activity; hosted Cesium services are separately governed.
- [OpenStreetMap tile usage policy — OpenStreetMap Foundation](https://operations.osmfoundation.org/policies/tiles/). Attribution, no-SLA and no bulk/offline-prefetch requirements for the public service.
- [WCAG 2.2 — W3C](https://www.w3.org/TR/WCAG22/). Non-text alternatives, keyboard access, contrast and status requirements.

