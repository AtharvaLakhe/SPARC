# Geospatial pipeline hardening

**Status:** mandatory requirements before upstream imagery is opened  
**Applies to:** acquisition adapters, Rasterio/GDAL processing, CLI steps, scratch storage, and publication

GDAL has a deliberately broad format surface. Its official security guidance identifies arbitrary code execution, unwanted network access, data theft, and denial of service as relevant risks when untrusted data is processed. File extensions are not a security boundary: content can select a different driver, and reference-capable formats can read other files or reach networks.

## H1 — Separate acquisition from parsing

- A dedicated acquisition step parses provider URLs, requires HTTPS, rejects credentials in URLs, checks the resolved host against a configured allowlist, and rejects private, loopback, link-local, and metadata-service addresses.
- Redirects are bounded and revalidated at every hop.
- Downloads stream to quarantine with byte and time limits and a recorded SHA-256.
- Rasterio and GDAL receive an approved local quarantine path, never a caller/catalogue URL or `/vsi*` path.
- P0 may deliberately download complete bounded assets. A later range-readable COG design requires a separate restricted-egress decision; it is not silently mixed with this rule.

## H2 — Restrict drivers explicitly

- The pinned Rasterio version must open upstream rasters with its documented `driver` string/list argument and the smallest required allowlist, initially GeoTIFF only where product compatibility permits.
- The code verifies the opened dataset's reported driver before any band read.
- Reference, network, document, and memory-pointer-capable drivers are not accepted as upstream inputs.
- Runtime `GDAL_SKIP` is defense in depth, not the primary allowlist. Its effective registration timing is tested against the pinned GDAL build.
- Do not globally disable the MEM driver without compatibility testing; GDAL documents legitimate internal creation uses.

## H3 — Use a defensive GDAL environment

- Python VRT pixel functions remain disabled.
- Remote virtual filesystems are unavailable to the parsing process unless a later reviewed design explicitly requires them.
- Directory scanning, retries, network timeouts, caches, and thread counts are bounded for the pinned build.
- Driver plugin paths and configuration arguments are fixed by code, not inherited from catalogue or request values.

## H4 — Reject implausible resources before reads

- The acquisition stream enforces a maximum byte count before the asset reaches the parser.
- Immediately after open and before band reads, validate driver, width, height, pixel count, band count, data types, block sizes, CRS, transform, bounds, overview structure, and expected product metadata.
- Limits are derived from approved Sentinel/Landsat product shapes and the target machine. They are configuration with tests, not universal constants copied from a review.
- CPU, memory, open-file, scratch-space, and wall-clock limits bound the worker process.

## H5 — Prevent command injection

- GDAL CLI commands receive an argument list built from code-owned flags and validated values.
- Never invoke a shell, use `shell=True`, accept arbitrary CLI options, or pass external `--config`, driver-path, expression, SQL, or filename values.
- Paths originate from fixed roots and server-generated names, not from region IDs or catalogue text.

## H6 — Isolate credentials and privileges

- Catalogue authentication and raster parsing run in separate processes.
- The parsing worker receives no provider credentials, `.env` access, signing key, database password, or unrestricted network route.
- It runs as a dedicated low-privilege identity with access only to its quarantine input and scratch output.
- A separate publisher verifies and promotes output; the parser cannot write directly into the published demo/output root.

## H7 — Quarantine, verify, then publish

- Derived output stays in scratch until it is re-opened under the allowed driver policy and passes shape, CRS, bounds, media-type, size, and checksum validation.
- Publication uses an atomic promotion step controlled by the publisher process.
- The immutable manifest records input and output hashes, source identities, method/configuration versions, and processing environment.
- Any failed check quarantines the asset and all derived output; it is never partially served.

## Required tests

- Disguised VRT/XML input is rejected even when named `.tif`.
- `/vsicurl/`, `/vsizip/`, remote redirects, private IPs, and metadata endpoints are rejected before GDAL receives a path.
- Oversized downloads, dimensions, bands, and decompression-expansion cases stop within configured budgets.
- Parser processes cannot read a test secret or write into the publication root.
- CLI wrappers prove that untrusted strings remain one argument and that arbitrary configuration flags cannot enter the command.
- Known-good approved products still open and produce deterministic output under the same restrictions.

## Authoritative references

- [GDAL security considerations](https://gdal.org/en/stable/user/security.html)
- [GDAL configuration options](https://gdal.org/en/stable/user/configoptions.html)
- [GDAL VRT security and raw-file restrictions](https://gdal.org/en/stable/drivers/raster/vrt.html)
- [Rasterio `open` API](https://rasterio.readthedocs.io/en/stable/api/rasterio.html#rasterio.open)

