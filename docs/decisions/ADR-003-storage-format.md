# ADR-003: Static, versioned P0 storage with object/PostGIS production path

- **Status:** Accepted
- **Date:** 2026-08-02
- **Decision owners:** Codex workstream, reviewed by Shared
- **Applies to:** Processed outputs, demo assets, metadata and future persistence

## Context

SPARC's P0 scope is two preselected district scenarios, three main proxy indicators and a finite set of map layers. A runtime database or dynamic tile service would add deployment, network, migration, backup and recovery failure modes without being needed to complete the demonstration.

The design still needs reproducibility, integrity, provenance, local/offline delivery and a credible path to multiple regions and live processing.

## Decision drivers

- Complete demo without internet, backend or database.
- Simple assets that React/MapLibre can consume directly.
- Immutable, auditable scientific outputs.
- Minimal operational burden in 3-to-4 days.
- Production migration without changing public API schemas.
- Avoid committing raw scenes or unbounded generated files.

## Decision

### P0 runtime

- Use no database.
- Store response payloads as versioned JSON and small vectors as RFC 7946 GeoJSON.
- Store presentation rasters as PNG/WebP plus bounds/legend/attribution descriptors, or as a deliberately bounded prebuilt XYZ tile set.
- Permit a COG as an analytical/production-compatible artifact, but do not require browser COG reading or a tile server for the critical path.
- Inventory every demo asset in a manifest with relative path, media type, byte size and SHA-256.
- Keep primary and backup packs self-contained and immutable after verification.

### Preparation and QA

- GeoPackage may be used as a portable versioned boundary/derived-vector handoff. It is not the serving database.
- DuckDB Spatial may be used by an analyst for local SQL/QA only when it reduces effort. It is not a required runtime dependency or concurrent application database. If used offline, its extension binary must already be available rather than installed from the network at demo time.

### Production evolution

- Use managed PostgreSQL/PostGIS for region hierarchy, result metadata, provenance, publication state and jobs.
- Use object storage and a CDN for large COGs, images, tiles and reports.
- Store object identity/key, checksum, bounds, media type and content version in metadata.
- Do not put large raster pixels into PostGIS unless a measured database-side raster query justifies it.

## Format rules

| Format | Role | Required controls |
|---|---|---|
| JSON | API/demo payload | Schema validation; UTF-8; no non-finite numbers; explicit units/version/mode |
| GeoJSON | Browser vector exchange | RFC 7946 WGS 84 longitude/latitude; analytical geometry version retained separately |
| PNG/WebP | Static analytical presentation | Bounds, source resolution, legend, attribution and checksum; not treated as raw evidence |
| XYZ tiles | Small interactive overlay | Only required zooms/regions, local relative URLs, complete attribution; no OSM public-tile prefetch |
| COG | Optional analytical/future tile source | Valid tiling/overviews/nodata/georeferencing and range-capable object host |
| GeoPackage | Portable vector/interchange | Version, source/license and geometry validity metadata; no concurrent API writes |

## Options considered

| Option | Advantages | Limitations | Decision |
|---|---|---|---|
| Static versioned pack | Highest reliability, inspectable and portable | Finite scenarios and package-size management | **Selected P0 runtime** |
| GeoPackage serving database | Portable and transactional | File locking/concurrency and browser/API access limitations | Preparation only |
| DuckDB Spatial serving database | Excellent local analytics | Not a multi-user operational service; extension packaging | Optional QA only |
| PostgreSQL/PostGIS from Day 1 | Mature spatial SQL and concurrency | Unnecessary deployment/migration/backup surface for two packs | Deferred to production |
| Raster-in-PostGIS | Central spatial processing | Storage/operations complexity and no measured P0 query need | Rejected initially |
| Object storage/CDN only | Scalable immutable objects | Does not replace queryable job/region metadata and adds network dependency | Production with PostGIS, not P0 critical path |

## Consequences

### Positive

- The complete P0 story works without a service process or network.
- Static content is easy to hash, copy, cache, test and recover.
- The same JSON/GeoJSON can serve contract mocks and final precomputed results.
- Future storage adapters can preserve API resource IDs and schemas.

### Negative and trade-offs

- P0 supports explicitly packaged requests rather than arbitrary regions/periods.
- Large source data and tiles need disciplined exclusion from Git.
- Publishing a corrected result requires a new pack/version.
- Static delivery does not support write workflows or live job state by itself.

## Integrity, retention, and security

- Treat local IDs as data, never as direct filenames; resolve through an allowlisted manifest to prevent traversal.
- Do not publish raw provider credentials, `.env` files, temporary signed URLs or private source data.
- Verify schemas, media types, byte sizes, image dimensions, bounds and hashes before release.
- Preserve immutable provenance and generation environment records with each pack.
- Keep the final pack on at least two separately tested devices.
- License and attribution are required fields. A file without verified publication rights is excluded.

## Reversal conditions

Introduce PostGIS/object storage when live multi-region results, concurrent writes, server-side spatial queries or durable jobs are P1/production requirements. Replace static layers with a dynamic tile service only when measured asset size or interaction requirements justify its security and operational costs.

## Sources

Official sources were accessed on 2026-08-02.

- [GeoPackage Encoding Standard 1.4.0 — OGC](https://www.geopackage.org/spec140/). Standard SQLite container and conformance model.
- [SQLite copyright — SQLite project](https://www.sqlite.org/copyright.html). Public-domain status.
- [DuckDB Spatial overview — DuckDB Foundation](https://duckdb.org/docs/current/core_extensions/spatial/overview). First-party extension purpose and installation.
- [DuckDB R-tree index documentation — DuckDB Foundation](https://duckdb.org/docs/stable/core_extensions/spatial/r-tree_indexes.html). Current spatial-index behavior and limitations.
- [PostGIS manual — PostGIS project](https://postgis.net/docs/en/). Spatial type/index/query capabilities.
- [PostGIS GPL FAQ — PostGIS project](https://postgis.net/documentation/faq/gpl-license/). Application and distribution licensing implications.
- [PostgreSQL license — PostgreSQL Global Development Group](https://www.postgresql.org/about/licence/). PostgreSQL License.
- [OGC COG Standard 1.0 — OGC](https://docs.ogc.org/is/21-026/21-026.html). COG structure and partial HTTP access.
- [RFC 7946: GeoJSON — IETF](https://www.rfc-editor.org/rfc/rfc7946). GeoJSON exchange requirements.

